from rest_framework import serializers
from .models import Disparo

class DisparoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disparo
        fields = ['id', 'fecha', 'latitud', 'longitud', 'probabilidad', 'deteccion_valida']
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Convertir datetime a formato ISO 8601
        if 'fecha' in data and data['fecha']:
            data['fecha'] = instance.fecha.isoformat()
        return data