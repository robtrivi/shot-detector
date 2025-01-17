import os
import librosa
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from monitor.models import Disparo
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from services.audio_analysis import AudioProcessor
from shot_detector.constants import FULL_MODEL_PATH, UMBRAL
from monitor.serializer import DisparoSerializer
import json

class DisparosAPIView(APIView):
    def get(self, request):
        disparos = Disparo.objects.all().order_by('-fecha')
        data = DisparoSerializer(disparos, many=True)
        return Response(data.data)

def monitoreo(request):
    disparos = Disparo.objects.all().order_by('-fecha')
    data = DisparoSerializer(disparos, many=True)
    return render(request, 'monitoreo.html', {'disparos': json.dumps(data.data)})

def home(request):
    return render(request, 'upload.html')

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
        
        
        try:
            # Cargar el archivo de audio y obtener sus datos
            audio_buffer, original_sr = librosa.load(audio_file_path, sr=None, mono=True)
            
            # Realizar predicción (asume que tienes un `audio_processor`)
            predictions = audio_processor.predict(audio_buffer, original_sr)
            if None in predictions:
                return JsonResponse({'error': 'No se detectó audio válido'}, status=400)
            # Extraer resultados
            result = {
                'clase': predictions[0],
                'confidence': float(predictions[1]),
            }
            return JsonResponse(result)
        except Exception as e:
            print("Error durante el análisis:", e)
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            # Eliminar el archivo de audio
            os.remove(audio_file_path)

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