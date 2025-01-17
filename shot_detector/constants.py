import os
from shot_detector.settings import BASE_DIR

# Asume que la carpeta 'models' está en la raíz del proyecto
MODEL_PATH = os.path.join(BASE_DIR, 'models')

# Normaliza la ruta
MODEL_PATH = os.path.abspath(MODEL_PATH)

# Nombre del modelo
MODEL_NAME = 'the_sentinel.h5'

# Ruta completa del modelo
FULL_MODEL_PATH = os.path.join(MODEL_PATH, MODEL_NAME)

UMBRAL = 0.9
