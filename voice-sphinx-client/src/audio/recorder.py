import numpy as np
import sounddevice as sd
import wave
import webrtcvad
from typing import Optional, Tuple
from loguru import logger

class AudioRecorder:
    def __init__(self, config):
        self.config = config
        self.vad = webrtcvad.Vad(config.vad_mode)
        self.stream = None
        self.recording = False
        self.audio_data = []
        self.silence_frames = 0
        self.silence_threshold = int(config.silence_threshold * config.sample_rate / 480)  # VAD работает с 30мс фреймами

    def start_recording(self) -> None:
        """Начало записи аудио"""
        if self.recording:
            return

        self.recording = True
        self.audio_data = []
        self.silence_frames = 0

        try:
            self.stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                device=self.config.audio_device,
                callback=self._audio_callback
            )
            self.stream.start()
            logger.info("Запись начата")
        except Exception as e:
            logger.error(f"Ошибка при запуске записи: {e}")
            self.recording = False
            raise

    def stop_recording(self) -> Optional[bytes]:
        """Остановка записи и возврат WAV-данных"""
        if not self.recording:
            return None

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            if not self.audio_data:
                return None

            # Конвертируем в WAV
            audio_data = np.concatenate(self.audio_data, axis=0)
            wav_data = self._convert_to_wav(audio_data)
            
            self.recording = False
            logger.info("Запись остановлена")
            return wav_data
        except Exception as e:
            logger.error(f"Ошибка при остановке записи: {e}")
            self.recording = False
            return None

    def _audio_callback(self, indata, frames, time, status) -> None:
        """Callback для обработки аудио-фреймов"""
        if status:
            logger.warning(f"Статус аудио-потока: {status}")

        if not self.recording:
            return

        # Конвертируем в 16-bit PCM для VAD
        audio_frame = (indata * 32768).astype(np.int16).tobytes()
        
        try:
            is_speech = self.vad.is_speech(audio_frame, self.config.sample_rate)
            if is_speech:
                self.silence_frames = 0
                self.audio_data.append(indata.copy())
            else:
                self.silence_frames += 1
                self.audio_data.append(indata.copy())

            # Проверяем на тишину
            if self.silence_frames > self.silence_threshold:
                self.stop_recording()
        except Exception as e:
            logger.error(f"Ошибка в обработке аудио-фрейма: {e}")

    def _convert_to_wav(self, audio_data: np.ndarray) -> bytes:
        """Конвертация аудио-данных в WAV формат"""
        with wave.open('temp.wav', 'wb') as wav_file:
            wav_file.setnchannels(self.config.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.config.sample_rate)
            wav_file.writeframes((audio_data * 32768).astype(np.int16).tobytes())

        with open('temp.wav', 'rb') as f:
            wav_data = f.read()

        # Удаляем временный файл
        import os
        os.remove('temp.wav')
        
        return wav_data 