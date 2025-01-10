from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('monitoreo/', views.monitoreo, name='monitoreo'),
    path('aprobar_disparo/<int:id>/', views.aprobar_disparo, name='aprobar_disparo'),
    path('desaprobar_disparo/<int:id>/', views.desaprobar_disparo, name='desaprobar_disparo'),
]
