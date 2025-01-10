import wave
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import threading
import numpy as np
from django.utils import timezone
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Disparo
import json
from asgiref.sync import sync_to_async
import random as rd

class AudioConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_buffer = bytearray()
        self.audio_save_thread = threading.Thread(target=self.save_audio_loop, daemon=True)
        self.audio_save_queue = []
        self.save_audio_lock = threading.Lock()
        self.audio_save_thread.start()

    async def connect(self):
        print("Conexión WebSocket establecida.")
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            if data["type"] == "location":
                # Procesa la ubicación del cliente
                self.location = data["data"]
        elif bytes_data:
            # Procesa los datos de audio
            self.audio_buffer.extend(bytes_data)
            await self.process_audio()

    async def disconnect(self, close_code):
        """
        Limpieza de recursos cuando el cliente se desconecta.
        """
        print("Conexión WebSocket cerrada con el código:", close_code)

        # Libera el buffer de audio
        self.audio_buffer.clear()

        # Detiene el hilo de guardado si es necesario
        with self.save_audio_lock:
            self.audio_save_queue.clear()

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
            
            with self.save_audio_lock:
                self.audio_save_queue.append(window)

            await self.process_window(window)

            # Desplaza el buffer en 2 segundo para el solapamiento deseado
            self.audio_buffer = self.audio_buffer[step_size:]
    
    @sync_to_async
    def create_disparo(self, **kwargs):
        latitud = kwargs.get("latitud")
        longitud = kwargs.get("longitud")
        ultimo = Disparo.objects.filter(latitud=latitud, longitud=longitud).last()
        if not ultimo or (ultimo and (timezone.now() - ultimo.fecha).seconds > 4):
            print("Disparo detectado.")
            nuevo_disparo = Disparo.objects.create(**kwargs)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
            "incidentes_grupo",
            {
                "type": "incident_message",
                "id": nuevo_disparo.id,
                "fecha": nuevo_disparo.fecha.isoformat(),
                "latitud": nuevo_disparo.latitud,
                "longitud": nuevo_disparo.longitud,
            }
            )
        return None
    
    async def process_window(self, window):
        """Procesa una ventana de audio y detecta disparos."""
        np_audio = np.frombuffer(window, dtype=np.int16)
        if self.detect_shot(np_audio):
            await self.create_disparo(
                    latitud=self.location["latitude"],
                    longitud=self.location["longitude"]
                )
        print("Ventana procesada.")

    def detect_shot(self, audio_data):
        """Simulación de detección de disparos."""
        return rd.random() > 0.5  # Ejemplo de umbral

    def save_audio_loop(self):
        """Hilo para guardar los audios procesados."""
        while True:
            if self.audio_save_queue:
                with self.save_audio_lock:
                    audio_data = self.audio_save_queue.pop(0)

                # Guarda el audio en un archivo WAV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
                file_path = f"./audios/audio_{timestamp}.wav"
                self.save_to_wav(audio_data, file_path)

    @staticmethod
    def save_to_wav(audio_data, file_path):
        """Guarda un fragmento de audio en un archivo WAV."""
        sample_rate = 16000  # 16 kHz
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16 bits
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
        await self.send(text_data=json.dumps({
            'id': event['id'],
            'fecha': event['fecha'],
            'latitud': event['latitud'],
            'longitud': event['longitud'],
        }))