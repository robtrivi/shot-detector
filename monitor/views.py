import os
import librosa
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Disparo
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import tempfile
import numpy as np
from services.audio_analysis import AudioProcessor
from shot_detector.constants import FULL_MODEL_PATH, UMBRAL

def monitoreo(request):
    return render(request, 'monitoreo.html')

def home(request):
    return render(request, 'base.html')

def upload_audio(request):
    return render(request, 'upload.html')

def record_audio(request):
    return render(request, 'record.html')

def monitor_audio(request):
    return render(request, 'monitor.html')

# Inicializar la clase de procesamiento
audio_processor = AudioProcessor(model_path=FULL_MODEL_PATH)

@csrf_exempt

def analyze_audio(request):
    if request.method == 'POST' and 'audio' in request.FILES:
        print('Analizando audio...')
        audio_file = request.FILES['audio']
        
        # Ruta para guardar el audio recibido
        save_path = os.path.join(settings.MEDIA_ROOT, 'received_audio')
        os.makedirs(save_path, exist_ok=True)  # Crear el directorio si no existe
        
        audio_file_path = os.path.join(save_path, audio_file.name)
        
        # Guardar el archivo recibido
        with open(audio_file_path, 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
        
        print(f"Archivo de audio guardado en: {audio_file_path}")
        
        try:
            # Cargar el archivo de audio y obtener sus datos
            audio_buffer, original_sr = librosa.load(audio_file_path, sr=None, mono=True)
            
            # Realizar predicción (asume que tienes un `audio_processor`)
            predictions = audio_processor.predict(audio_buffer, original_sr)

            # Extraer resultados
            result = {
                'clase': predictions[0],
                'confidence': float(predictions[1]),
            }
            return JsonResponse(result)
        except Exception as e:
            print("Error durante el análisis:", e)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Solicitud inválida'}, status=400)


@require_POST
def aprobar_disparo(request, id):
    disparo = get_object_or_404(Disparo, id=id)
    disparo.deteccion_valida = True
    disparo.save()
    return JsonResponse({'status': 'aprobado'})

@require_POST
def desaprobar_disparo(request, id):
    disparo = get_object_or_404(Disparo, id=id)
    disparo.deteccion_valida = False
    disparo.save()
    return JsonResponse({'status': 'desaprobado'})