import numpy as np
import librosa
import tensorflow as tf
from tensorflow.keras.models import load_model
import random as rd

class AudioProcessor:
    def __init__(self, model_path, target_sr=22050, window_duration=4, target_shape=(128, 128), n_mfcc=40):
        self.model = load_model(model_path)
        self.target_sr = target_sr  # Frecuencia de muestreo objetivo
        self.window_duration = window_duration  # Duración de la ventana en segundos
        self.target_shape = target_shape  # Dimensiones del espectrograma
        self.n_mfcc = n_mfcc
    def normalize_audio(self, audio_buffer, original_sr):
        """
        Normaliza el audio a la frecuencia de muestreo objetivo (target_sr).
        """

        if audio_buffer.dtype == np.int16:
            audio_buffer = audio_buffer.astype(np.float32) / 32768.0
        
        if original_sr == self.target_sr:
            # Si ya está en la frecuencia correcta, no hace nada
            return audio_buffer
        
        # Convertir int16 a float32 si es necesario
        # Re-samplear el audio
        normalized_audio = librosa.resample(audio_buffer, orig_sr=original_sr, target_sr=self.target_sr)
        return normalized_audio

    def preprocess_audio(self, audio_buffer, original_sr, rms_threshold=0.025):
        """
        Preprocesa un archivo de audio dividiéndolo en ventanas de duración fija y generando características MFCC.

        Args:
            audio (np.array): Señal de audio cargada con librosa.
            target_sr (int): Frecuencia de muestreo objetivo (por defecto 22050 Hz).
            window_duration (int): Duración de la ventana en segundos (por defecto 4 segundos).
            n_mfcc (int): Número de coeficientes MFCC a extraer (por defecto 40).
            rms_threshold (float): Umbral mínimo de RMS para procesar una ventana (por defecto 0.025).

        Returns:
            list: Lista de vectores MFCC para cada ventana válida.
        """
        # Calcular el tamaño de cada ventana en muestras
        samples_per_window = self.target_sr * self.window_duration
        mfcc_features = []
        audio = self.normalize_audio(audio_buffer, original_sr)

        # Dividir el audio en ventanas deslizantes
        for start in range(0, len(audio), samples_per_window):
            # Extraer una ventana del audio
            window = audio[start:start + samples_per_window]

            # Calcular RMS (energía promedio)
            rms = np.sqrt(np.mean(window ** 2))

            # Filtrar ventanas con baja energía
            if rms < rms_threshold:
                continue

            # Rellenar con ceros si la ventana es más pequeña que la duración esperada
            if len(window) < samples_per_window:
                window = np.pad(window, (0, samples_per_window - len(window)), mode='constant')

            # Generar características MFCC
            mfccs = librosa.feature.mfcc(y=window, sr=self.target_sr, n_mfcc=self.n_mfcc)
            mfccs_scaled = np.mean(mfccs.T, axis=0)  # Promedio de los MFCC en el tiempo
            mfcc_features.append(mfccs_scaled)

        return np.array(mfcc_features)

    def predict(self, audio_buffer, original_sr):
        """
        Preprocesa el audio y realiza predicciones con el modelo.
        """
        spectrograms = self.preprocess_audio(audio_buffer, original_sr)
        if len(spectrograms) == 0:
            return "no_disparo", 0.0
        predictions = self.model.predict(spectrograms)
        classes = ['disparo', 'no_disparo']
        disparo_ventanas = []
        # Recorrer las predicciones de cada ventana
        for pred in predictions:
            clase_predicha = classes[np.argmax(pred)]
            if clase_predicha == 'disparo':
                disparo_ventanas.append(pred)

        # Si se detectó al menos un disparo en alguna ventana
        if disparo_ventanas:
            # Obtener la ventana con mayor confianza de disparo
            disparo_confianzas = [np.max(pred) for pred in disparo_ventanas]
            max_idx = np.argmax(disparo_confianzas)
            mejor_confianza = disparo_confianzas[max_idx]
            return 'disparo', float(mejor_confianza)
        else:
            # Si ninguna ventana indica disparo, determinar la mayor confianza de 'no_disparo'
            no_disparo_confianzas = [pred[classes.index('no_disparo')] for pred in predictions]
            mejor_confianza = float(np.max(no_disparo_confianzas))
            return 'no_disparo', mejor_confianza
        # return ('disparo', rd.random())  # Dummy prediction
