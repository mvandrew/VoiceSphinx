import sys
import os
import time
import numpy as np
import sounddevice as sd
import webrtcvad
import wave
from io import BytesIO
from typing import Optional, List, Dict, Any
from loguru import logger
from utils.audio_utils import get_default_microphone, get_available_microphones
import logging

# Подключаем путь к src для импортов
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class AudioRecorder:
    def __init__(self, config):
        """
        Инициализирует аудио рекордер
        
        Args:
            config: Конфигурация приложения
        """
        self.logger = logging.getLogger(__name__)
        
        # Основные параметры аудио
        self.sample_rate = config.sample_rate
        self.channels = config.channels
        self.device_id = config.audio_device
        self.gain = config.gain
        
        # Параметры VAD
        self.vad_mode = getattr(config, 'vad_mode', 1)  # По умолчанию используем менее строгий режим
        self.logger.info(f"Инициализация VAD с режимом {self.vad_mode} (1-3, где 1 - менее строгий, 3 - самый строгий)")
        self.vad = webrtcvad.Vad(self.vad_mode)
        
        # Оптимальный размер фрейма для VAD (должен быть 10, 20 или 30 мс)
        self.frame_duration_ms = 30
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        
        # Уровень сигнала для определения речи (адаптивный порог)
        self.min_speech_level = getattr(config, 'min_speech_level', 0.01)
        
        # Параметры обнаружения тишины
        self.silence_threshold = getattr(config, 'silence_threshold', 1.0)  # секунды тишины
        self.silence_frames = 0
        self.frame_count = 0
        self.max_level = 0.0
        
        # Состояние записи
        self.is_recording = False
        self.recording_data = None
        self.external_callback = None
        self.stream = None
        
        # Выбор устройства записи
        self.device_id = self._get_device_id(config.audio_device)
        
        # Настройка VAD
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self.vad_mode)
        self.logger.info(f"VAD настроен в режиме {self.vad_mode} (1=либеральный, 3=строгий)")
        
        # Размер фрейма для VAD (должен быть кратен 10, 20 или 30 мс)
        frame_duration_ms = 30  # Длительность фрейма в миллисекундах
        self.frame_size = int(self.sample_rate * frame_duration_ms / 1000)
        
        # Усиление сигнала микрофона для повышения качества распознавания
        self.gain = config.gain  # Берем из конфигурации
        
        # Дополнительная настройка для обнаружения речи
        self.min_speech_level = 0.0003  # Минимальный RMS для речи
        
        # Callback для внешнего использования
        self.callback = None
        
    def _get_device_id(self, device_id):
        """Получаем ID устройства из конфигурации или используем устройство по умолчанию"""
        if device_id is not None:
            try:
                # Если указан индекс устройства
                if isinstance(device_id, int):
                    return device_id
                # Если указано имя устройства
                elif isinstance(device_id, str):
                    devices = get_available_microphones()
                    for device in devices:
                        if device['name'].lower() in device_id.lower():
                            self.logger.info(f"Найдено устройство по имени: {device['name']} (ID: {device['id']})")
                            return device['id']
                    self.logger.warning(f"Устройство '{device_id}' не найдено, использую устройство по умолчанию")
                    return get_default_microphone()
            except Exception as e:
                self.logger.error(f"Ошибка при выборе аудиоустройства: {e}")
                self.logger.info("Использую устройство по умолчанию")
                return get_default_microphone()
        
        # Используем устройство по умолчанию
        return get_default_microphone()
    
    def get_current_device_info(self) -> Dict:
        """Получение информации о текущем устройстве записи"""
        try:
            if self.device_id is not None:
                device_info = sd.query_devices(self.device_id)
                return {
                    'id': self.device_id,
                    'name': device_info['name'],
                    'channels': device_info['max_input_channels'],
                    'default': device_info.get('default_input', False),
                    'sample_rate': self.sample_rate
                }
            else:
                default_device = sd.query_devices(kind='input')
                return {
                    'id': get_default_microphone(),
                    'name': default_device['name'],
                    'channels': default_device['max_input_channels'],
                    'default': True,
                    'sample_rate': self.sample_rate
                }
        except Exception as e:
            self.logger.error(f"Не удалось получить информацию об устройстве: {e}")
            return {
                'id': self.device_id,
                'name': 'Неизвестное устройство',
                'channels': 1,
                'default': False,
                'sample_rate': self.sample_rate
            }
    
    def list_available_devices(self) -> List[Dict]:
        """Получение списка доступных микрофонов"""
        return get_available_microphones()

    def test_microphone(self, duration: float = 1.0) -> bool:
        """Проверка работы микрофона с записью короткого фрагмента"""
        self.logger.info(f"Проверяю микрофон {self.get_current_device_info()['name']}...")
        
        try:
            test_audio = []
            
            def callback(indata, frames, time, status):
                if status:
                    self.logger.warning(f"Статус потока при тестировании: {status}")
                test_audio.append(indata.copy())
            
            # Запускаем временный поток
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device_id,
                callback=callback
            ):
                # Спим указанное время
                time.sleep(duration)
            
            if not test_audio:
                self.logger.error("Микрофон не записал никаких данных")
                return False
                
            # Преобразуем данные в единый массив
            audio_data = np.concatenate(test_audio).flatten()
            
            # Проверяем RMS и пиковый уровень
            rms = np.sqrt(np.mean(audio_data**2))
            peak = np.max(np.abs(audio_data))
            
            self.logger.info(f"Результаты тестирования микрофона:")
            self.logger.info(f"- Продолжительность: {len(audio_data) / self.sample_rate:.2f} сек")
            self.logger.info(f"- RMS уровень: {rms:.6f}")
            self.logger.info(f"- Пиковый уровень: {peak:.6f}")
            
            # Используем очень низкий порог, так как некоторые микрофоны могут быть тихими,
            # но все равно работать с VAD
            threshold = 0.0001
            if rms > threshold:
                self.logger.info("Тест микрофона пройден успешно")
                return True
            elif rms > 0.00001:  # Сверхнизкий уровень
                self.logger.warning(f"Очень низкий уровень сигнала ({rms:.6f}). Микрофон работает, но сигнал слабый.")
                self.logger.warning("Попробуйте говорить громче или увеличить чувствительность микрофона в настройках системы.")
                # Считаем, что тест пройден с предупреждением
                return True
            else:
                self.logger.error(f"Тест микрофона не пройден. Уровень сигнала ({rms:.6f}) ниже порогового значения ({threshold}).")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка при тестировании микрофона: {e}")
            return False

    def start_recording(self, callback=None):
        """
        Запускает запись звука с микрофона
        """
        if self.is_recording:
            return

        try:
            self.is_recording = True
            self.recording_data = []
            self.silence_frames = 0
            
            current_device_info = self.get_current_device_info()
            self.logger.info(f"Начинаю запись с микрофона: {current_device_info.get('name', 'Неизвестно')} (ID: {current_device_info.get('id', 'Н/Д')})")
            
            if callback:
                self.external_callback = callback
            
            try:
                self.stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    blocksize=self.frame_size,
                    device=self.device_id,
                    channels=self.channels,
                    dtype='float32',
                    callback=self._audio_callback
                )
                self.stream.start()
                self.logger.info(f"Запись звука успешно запущена с параметрами: samplerate={self.sample_rate}, "
                               f"channels={self.channels}, device={self.device_id}")
            except sd.PortAudioError as e:
                error_message = str(e)
                if "Invalid sample rate" in error_message:
                    self.logger.error(f"Неподдерживаемая частота дискретизации {self.sample_rate} Гц для устройства '{current_device_info.get('name')}'. "
                                   f"Попробуйте другую частоту, например 44100 Гц.")
                elif "Invalid number of channels" in error_message:
                    self.logger.error(f"Неподдерживаемое количество каналов {self.channels} для устройства '{current_device_info.get('name')}'. "
                                   f"Попробуйте другое количество каналов, например 2 (стерео).")
                else:
                    self.logger.error(f"Ошибка при запуске записи звука: {e}")
                self.is_recording = False
                raise
        except Exception as e:
            self.logger.error(f"Непредвиденная ошибка при запуске записи: {e}")
            self.is_recording = False
            raise

    def stop_recording(self) -> Optional[bytes]:
        """Остановка записи звука и возврат данных в формате WAV"""
        if not self.is_recording:
            return None
        
        try:
            # Устанавливаем флаг записи в False перед другими операциями
            self.is_recording = False
            
            # Останавливаем и закрываем поток
            stream_to_close = self.stream  # Сохраняем ссылку на поток
            self.stream = None  # Обнуляем ссылку на поток
            
            if stream_to_close:
                try:
                    stream_to_close.stop()
                    stream_to_close.close()
                except Exception as e:
                    self.logger.error(f"Ошибка при закрытии потока: {e}")
            
            if not self.recording_data:
                self.logger.warning("Остановка записи: нет записанных данных")
                return None
                
            # Преобразуем в единый массив
            audio_array = np.concatenate(self.recording_data)
            
            # Проверяем уровень звука (после усиления)
            rms = np.sqrt(np.mean(audio_array**2))
            duration = len(audio_array) / self.sample_rate
            
            self.logger.info(f"Остановка записи: RMS уровень звука: {rms:.6f}, длительность: {duration:.2f} сек")
            
            # Если запись слишком короткая и нет значимого сигнала, возвращаем None
            if duration < 0.2 and rms < 0.0005:
                self.logger.warning("Запись слишком короткая и сигнал слишком слабый. Игнорируем.")
                return None
                
            # Преобразуем float32 (-1.0...1.0) в int16 для WAV
            # Нормализуем амплитуду для предотвращения клиппинга
            max_amplitude = np.max(np.abs(audio_array))
            if max_amplitude > 0.99:  # Если амплитуда близка к 1.0, нормализуем
                normalization_factor = 0.9 / max_amplitude
                audio_array = audio_array * normalization_factor
                self.logger.debug(f"Применена нормализация с коэффициентом {normalization_factor:.4f}")
                
            audio_int16 = (audio_array * 32767).astype(np.int16)
            
            # Создаем WAV данные в памяти
            wav_io = BytesIO()
            
            try:
                with wave.open(wav_io, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(2)  # 16 bit
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_int16.tobytes())
                    
                wav_data = wav_io.getvalue()
                self.logger.info(f"Запись завершена успешно, размер данных: {len(wav_data)} байт")
                return wav_data
            finally:
                # Убедимся, что BytesIO объект закрыт в любом случае
                try:
                    wav_io.close()
                except Exception as e:
                    self.logger.error(f"Ошибка при закрытии BytesIO: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка при остановке записи: {e}")
            self.is_recording = False
            return None

    def _audio_callback(self, indata, frames, time_info, status):
        """Обратный вызов для потока аудио"""
        try:
            if status:
                self.logger.warning(f"Статус потока: {status}")
            
            # Проверяем, что запись активна
            if not self.is_recording:
                if self.external_callback:
                    self.external_callback(indata.copy(), status)
                return
            
            # Применяем усиление к входному сигналу
            amplified_data = indata.copy() * self.gain
            
            # Используем усиленные данные для всех дальнейших операций
            if self.recording_data is not None:
                self.recording_data.append(amplified_data)
            
            # Вычисляем RMS напрямую из аудиоданных
            rms = np.sqrt(np.mean(amplified_data**2))
            
            is_speech_rms = rms > self.min_speech_level
            
            # VAD ожидает 16-битные семплы
            frame_bytes = (amplified_data * 32767).astype(np.int16).tobytes()
            
            # Проверка для VAD - размер фрейма должен соответствовать требованиям
            valid_frame_for_vad = len(frame_bytes) == self.frame_size * 2  # 2 байта на сэмпл для int16
            
            if valid_frame_for_vad:
                # Используем VAD для определения речи
                is_speech_vad = self.vad.is_speech(frame_bytes, self.sample_rate)
                
                # Комбинируем результаты VAD и RMS для лучшего определения речи
                is_speech = is_speech_vad or is_speech_rms
                
                # Обновляем счетчик тишины
                if not is_speech:
                    self.silence_frames += 1
                    
                    # Логируем тишину, но не слишком часто (каждые ~30 фреймов)
                    if self.silence_frames % 30 == 0:
                        self.logger.debug(f"Тишина продолжается {self.silence_frames} фреймов, RMS: {rms:.6f}")
                else:
                    # Если выявлена речь, сбрасываем счетчик тишины
                    if self.silence_frames > 0:
                        self.logger.debug(f"Обнаружена речь после {self.silence_frames} фреймов тишины, RMS: {rms:.6f}")
                        self.silence_frames = 0
            else:
                # Если фрейм не подходит для VAD, используем только RMS
                is_speech = is_speech_rms
                
                # Логируем уровень сигнала периодически
                if self.frame_count % 50 == 0:
                    self.logger.debug(f"Аудио уровень: RMS={rms:.6f}")
            
            # Увеличиваем счетчик фреймов
            self.frame_count += 1
            
            # Отслеживаем максимальный уровень сигнала
            self.max_level = max(self.max_level, rms)
            
            # Вызываем внешний обратный вызов, если он установлен
            if self.external_callback:
                self.external_callback(amplified_data, status)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке фрейма: {e}")
            # Даже в случае ошибки продолжаем запись и вызываем внешний обратный вызов
            if self.external_callback:
                try:
                    self.external_callback(indata.copy(), status)
                except Exception as callback_error:
                    self.logger.error(f"Ошибка в обратном вызове: {callback_error}")

    def _convert_to_wav(self, audio_data: np.ndarray) -> bytes:
        """Конвертация аудио-данных в WAV формат"""
        # Создаем временную директорию, если её нет
        temp_dir = 'temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file = os.path.join(temp_dir, f'temp_{int(time.time())}.wav')
        
        try:
            with wave.open(temp_file, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes((audio_data * 32768).astype(np.int16).tobytes())

            with open(temp_file, 'rb') as f:
                wav_data = f.read()

            # Удаляем временный файл
            os.remove(temp_file)
            
            return wav_data
        except Exception as e:
            logger.error(f"Ошибка при конвертации в WAV: {e}")
            # Попытка удалить временный файл в случае ошибки
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise 