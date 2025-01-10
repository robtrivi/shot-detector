from django.urls import path
from monitor.consumers import AudioConsumer, IncidentesConsumer

websocket_urlpatterns = [
    path('ws/audio/', AudioConsumer.as_asgi()),
    path("ws/incidentes/", IncidentesConsumer.as_asgi()),

]
