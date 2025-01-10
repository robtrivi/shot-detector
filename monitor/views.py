from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Disparo
from django.shortcuts import render

def index(request):
    return render(request, 'monitor/index.html')

def monitoreo(request):
    return render(request, 'monitor/monitoreo.html')


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