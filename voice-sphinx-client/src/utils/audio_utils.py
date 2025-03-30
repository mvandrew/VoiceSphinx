import numpy as np
import sounddevice as sd
from typing import List, Dict, Optional, Any
from loguru import logger

def get_available_microphones() -> List[Dict[str, Any]]:
    """Получение списка доступных микрофонов"""
    try:
        devices = sd.query_devices()
        microphones = []
        
        # Находим устройство по умолчанию
        default_device = sd.query_devices(kind='input')
        default_id = default_device['index'] if default_device else None
        
        for i, device in enumerate(devices):
            # Проверяем, является ли устройство микрофоном
            if device['max_input_channels'] > 0:
                microphones.append({
                    'id': device['index'],
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'default': device['index'] == default_id
                })
        
        return microphones
    except Exception as e:
        logger.error(f"Ошибка при получении списка микрофонов: {e}")
        return []

def get_default_microphone() -> Optional[int]:
    """Получение ID микрофона по умолчанию"""
    try:
        default_device = sd.query_devices(kind='input')
        if default_device:
            return default_device['index']
    except Exception as e:
        logger.error(f"Ошибка при получении микрофона по умолчанию: {e}")
    
    return None

class MicrophoneTester:
    """Класс для тестирования и мониторинга уровня звука микрофона"""
    
    def __init__(self, device_id, sample_rate=16000, channels=1, gain=5.0):
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.channels = channels
        self.gain = gain  # Коэффициент усиления для микрофона
        
        self.stream = None
        self.is_monitoring = False
        self.current_level = 0.0
        self.rms_values = []  # Храним историю RMS для сглаживания
        self.rms_history_size = 3  # Размер истории для усреднения
        
        self.logger = logger  # Используем глобальный логгер
    
    def start_monitoring(self):
        """Запускает мониторинг уровня звука с микрофона"""
        if self.is_monitoring:
            return True
            
        try:
            def audio_callback(indata, frames, time, status):
                if status:
                    self.logger.debug(f"Статус потока мониторинга: {status}")
                
                # Применяем усиление
                amplified_data = indata.copy() * self.gain
                
                # Вычисляем RMS уровень (корень из среднего квадрата амплитуды)
                rms = np.sqrt(np.mean(amplified_data**2))
                
                # Добавляем новое значение RMS в историю
                self.rms_values.append(rms)
                
                # Ограничиваем размер истории
                if len(self.rms_values) > self.rms_history_size:
                    self.rms_values.pop(0)
                
                # Устанавливаем текущий уровень как среднее из последних значений
                # Это делает индикатор более стабильным
                self.current_level = np.mean(self.rms_values)
            
            self.stream = sd.InputStream(
                device=self.device_id,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=audio_callback
            )
            
            self.stream.start()
            self.is_monitoring = True
            self.logger.info(f"Начат мониторинг микрофона (ID: {self.device_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при запуске мониторинга микрофона: {e}")
            return False
    
    def stop_monitoring(self):
        """Останавливает мониторинг микрофона"""
        if not self.is_monitoring:
            return
            
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
                
            self.is_monitoring = False
            self.current_level = 0.0
            self.rms_values = []
            self.logger.info("Мониторинг микрофона остановлен")
            
        except Exception as e:
            self.logger.error(f"Ошибка при остановке мониторинга микрофона: {e}")
    
    def get_audio_level(self):
        """Возвращает текущий уровень звука (от 0.0 до 1.0)"""
        return self.current_level 