import wave
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import threading
import numpy as np
from django.utils import timezone
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from services.audio_analysis import AudioProcessor
from monitor.serializer import DisparoSerializer
from monitor.models import Disparo
import json
from asgiref.sync import sync_to_async
import random as rd
from shot_detector.constants import FULL_MODEL_PATH, UMBRAL


class AudioConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_processor = AudioProcessor(
            model_path=FULL_MODEL_PATH,
        )
        self.audio_buffer = bytearray()
        self.audio_save_thread = threading.Thread(target=self.save_audio_loop, daemon=True)
        self.audio_save_queue = []
        self.thread_running = True
        self.save_audio_lock = threading.Lock()
        self.audio_condition = threading.Condition(self.save_audio_lock)
        self.audio_save_thread.start()

    async def connect(self):
        print("Conexión WebSocket establecida.")
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            if data["type"] == "metadata":
                self.location = data["data"]["location"]
                self.sample_rate = data["data"]["sampleRate"]
        elif bytes_data:
            self.audio_buffer.extend(bytes_data)
            await self.process_audio()


    async def disconnect(self, close_code):
        """
        Limpieza de recursos cuando el cliente se desconecta.
        """
        print("Conexión WebSocket cerrada con el código:", close_code)

        # Libera el buffer de audio
        self.audio_buffer.clear()

        self.thread_running = False
        with self.audio_condition:
            self.audio_condition.notify_all()
        self.audio_save_thread.join()

        # Opcional: guarda logs o realiza tareas adicionales
        print("Recursos liberados y conexión cerrada.")

    async def process_audio(self):
        sample_rate = 16000  # 16 kHz
        bytes_per_sample = 2   # int16 = 2 bytes
        window_duration = 4    # segundos
        step_duration = 2      # segundos

        window_size = sample_rate * window_duration * bytes_per_sample  # bytes para 4 segundos
        step_size = sample_rate * step_duration * bytes_per_sample      # bytes para 1 segundo

        while len(self.audio_buffer) >= window_size:
            window = self.audio_buffer[:window_size]
            
            
            await self.process_window(window)
            # Desplaza el buffer en 2 segundo para el solapamiento deseado
            self.audio_buffer = self.audio_buffer[step_size:]
    
    @sync_to_async
    def create_disparo(self, **kwargs):
        latitud = kwargs.get("latitud")
        longitud = kwargs.get("longitud")
        ultimo = Disparo.objects.filter(latitud=latitud, longitud=longitud).last()
        if not ultimo or (ultimo and (timezone.now() - ultimo.fecha).seconds > 4):
            nuevo_disparo = Disparo.objects.create(**kwargs)
            serializer = DisparoSerializer(nuevo_disparo)
            data = serializer.data
            data["type"] = "incident_message"
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "incidentes_grupo",
                data
            )
            return nuevo_disparo
        return None
    
    async def send(self, text_data=None, bytes_data=None):
        if text_data:
            print(text_data)
            await super().send(text_data=json.dumps(text_data))
        elif bytes_data:
            await super().send(bytes_data=bytes_data)

    async def process_window(self, window):
        """Procesa una ventana de audio y detecta disparos."""
        print("Procesando ventana...")
        np_audio = np.frombuffer(window, dtype=np.int16)
        clase, confidence = self.audio_processor.predict(np_audio, self.sample_rate)
        if confidence is None:
            return None
        if clase == "disparo" and confidence > UMBRAL:
            disparo = await self.create_disparo(
                    latitud=self.location["latitude"],
                    longitud=self.location["longitude"],
                    probabilidad=confidence
                )
            # enviar por websocket
            if disparo:  # Si se crea un nuevo disparo
                with self.save_audio_lock:
                    # Guarda el audio junto con el ID del disparo
                    self.audio_save_queue.append((window.copy(), disparo.id))
                    self.audio_condition.notify()  # Notificar al hilo que hay un nuevo audio
                    await self.send(text_data=DisparoSerializer(disparo).data)
            return disparo
        print("Ventana procesada.")
        return None

    def save_audio_loop(self):
        """Hilo para guardar los audios procesados."""
        while self.thread_running:
            with self.audio_condition:
                while not self.audio_save_queue and self.thread_running:
                    self.audio_condition.wait()  # Bloquea el hilo hasta que sea notificado

                if not self.thread_running:
                    break

                # Extraer el audio de la cola
                audio_data,id = self.audio_save_queue.pop(0)

            # Guarda el audio en un archivo WAV
            file_path = f"./media/disparos/disparo_{id}.wav"
            self.save_to_wav(audio_data, file_path)

    @staticmethod
    def save_to_wav(audio_data, file_path):
        """Guarda un fragmento de audio en un archivo WAV."""
        sample_rate = 16000 
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)

class IncidentesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "incidentes_grupo"
        # Añade la conexión al grupo
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Quitar la conexión del grupo
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Recibir mensaje desde el grupo
    async def incident_message(self, event):
        # Enviar mensaje al WebSocket
        await self.send(text_data=json.dumps(event))