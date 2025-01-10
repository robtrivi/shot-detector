from django.db import models

class Disparo(models.Model):
    latitud = models.FloatField()
    longitud = models.FloatField()
    fecha = models.DateTimeField(auto_now_add=True)
    deteccion_valida = models.BooleanField(default=None, null=True, blank=True)
    
    def __str__(self):
        return f'Se detectó un disparo el {self.fecha} en la posición {self.latitud}, {self.longitud}'
    
    @property
    def google_maps(self):
        return f'https://www.google.com/maps/search/?api=1&query={self.latitud},{self.longitud}'