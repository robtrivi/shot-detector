import numpy as np
import librosa
import tensorflow as tf
from tensorflow.keras.models import load_model
import random as rd

class AudioProcessor:
    def __init__(self, model_path, target_sr=22050, window_duration=4, target_shape=(128, 128)):
        self.model = load_model(model_path)
        self.target_sr = target_sr  # Frecuencia de muestreo objetivo
        self.window_duration = window_duration  # Duración de la ventana en segundos
        self.target_shape = target_shape  # Dimensiones del espectrograma

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

    def preprocess_audio(self, audio_buffer, original_sr):
        """
        Convierte un buffer de audio en espectrogramas mel.
        """
        # Normalizar la frecuencia de muestreo
        normalized_audio = self.normalize_audio(audio_buffer, original_sr)
        
        samples_per_window = self.target_sr * self.window_duration
        spectrograms = []

        for start in range(0, len(normalized_audio), samples_per_window):
            window = normalized_audio[start:start + samples_per_window]

            if len(window) < samples_per_window:
                window = np.pad(window, (0, samples_per_window - len(window)), mode='constant')

            rms = np.sqrt(np.mean(window**2))
            if rms < 0.025:
                print("Ventana descartada por baja energía")
                return None

            # Generar espectrograma mel
            mel_spec = librosa.feature.melspectrogram(y=window, sr=self.target_sr)
            mel_spec = np.expand_dims(mel_spec, axis=-1)  
            mel_spec = tf.image.resize(mel_spec, self.target_shape).numpy()  

            spectrograms.append(mel_spec)

        return np.array(spectrograms)

    def predict(self, audio_buffer, original_sr):
        """
        Preprocesa el audio y realiza predicciones con el modelo.
        """
        spectrograms = self.preprocess_audio(audio_buffer, original_sr)
        if spectrograms is None:
            return None, None
        predictions = self.model.predict(spectrograms)[0]
        classes = ['disparo', 'no_disparo']
        predicted_class = classes[np.argmax(predictions)]
        confidence = np.max(predictions)
        print(f"Prob disparo {predictions[0]:.2f} Prob no disparo {predictions[1]:.2f}")
        return (predicted_class, confidence)
        # return ('disparo', rd.random())  # Dummy prediction
