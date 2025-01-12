from rest_framework import serializers
from .models import Disparo

class DisparoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disparo
        fields = ['id', 'fecha', 'latitud', 'longitud', 'probabilidad']
