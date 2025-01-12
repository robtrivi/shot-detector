from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_audio, name='upload_audio'),
    path('record/', views.record_audio, name='record_audio'),
    path('monitor/', views.monitor_audio, name='monitor_audio'),
    path('analyze/', views.analyze_audio, name='analyze_audio'),
    path('monitoreo/', views.monitoreo, name='monitoreo'),
    path('aprobar_disparo/<int:id>/', views.aprobar_disparo, name='aprobar_disparo'),
    path('desaprobar_disparo/<int:id>/', views.desaprobar_disparo, name='desaprobar_disparo'),
]
