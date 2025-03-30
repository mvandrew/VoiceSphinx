import json
import os
from typing import Dict, Any, List, Optional, Union
from loguru import logger

class Config:
    """Класс для работы с конфигурацией приложения"""
    
    def __init__(self, config_path: str = "config.json"):
        """Инициализация конфигурации"""
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        
        # Устанавливаем значения по умолчанию
        self.config = {
            "server": {"url": "http://localhost:8000/transcribe"},
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "device": None,
                "vad_mode": 3,
                "silence_threshold": 1.0,
                "max_recording_time": 30.0,
                "gain": 5.0
            },
            "hotkeys": {
                "record": ["alt", "win", "z"],
                "cancel": ["escape"]
            },
            "mode": "hotkey",
            "log_level": "info"
        }
        
        # Загружаем конфигурацию из файла
        self.load_config(config_path)
    
    def load_config(self, config_path: str) -> bool:
        """Загрузка конфигурации из файла"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = json.load(file)
            logger.info(f"Конфигурация загружена из {config_path}")
            logger.debug(f"Загруженная конфигурация: {self.config}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации: {e}")
            return False
    
    def save_config(self) -> bool:
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                json.dump(self.config, file, indent=2, ensure_ascii=False)
            logger.info(f"Конфигурация сохранена в {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении конфигурации: {e}")
            return False
    
    @property
    def server_url(self) -> str:
        """URL сервера для отправки аудио"""
        return self.config.get('server', {}).get('url', 'http://localhost:8000/transcribe')
    
    @server_url.setter
    def server_url(self, url: str) -> None:
        """Установка URL сервера"""
        if 'server' not in self.config:
            self.config['server'] = {}
        self.config['server']['url'] = url
    
    @property
    def sample_rate(self) -> int:
        """Частота дискретизации аудио"""
        return self.config.get('audio', {}).get('sample_rate', 16000)
    
    @sample_rate.setter
    def sample_rate(self, rate: int) -> None:
        """Установка частоты дискретизации"""
        if 'audio' not in self.config:
            self.config['audio'] = {}
        self.config['audio']['sample_rate'] = rate
    
    @property
    def channels(self) -> int:
        """Количество каналов аудио"""
        return self.config.get('audio', {}).get('channels', 1)
    
    @channels.setter
    def channels(self, channels: int) -> None:
        """Установка количества каналов"""
        if 'audio' not in self.config:
            self.config['audio'] = {}
        self.config['audio']['channels'] = channels
    
    @property
    def audio_device(self) -> Optional[Union[int, str]]:
        """ID или имя устройства записи"""
        return self.config.get('audio', {}).get('device', None)
    
    @audio_device.setter
    def audio_device(self, device: Optional[Union[int, str]]) -> None:
        """Установка устройства записи"""
        if 'audio' not in self.config:
            self.config['audio'] = {}
        self.config['audio']['device'] = device
    
    @property
    def vad_mode(self) -> int:
        """Режим VAD (0-3, где 3 - самый агрессивный)"""
        return self.config.get('audio', {}).get('vad_mode', 3)
    
    @vad_mode.setter
    def vad_mode(self, mode: int) -> None:
        """Установка режима VAD"""
        if 'audio' not in self.config:
            self.config['audio'] = {}
        self.config['audio']['vad_mode'] = mode
    
    @property
    def silence_threshold(self) -> float:
        """Порог тишины в секундах"""
        return self.config.get('audio', {}).get('silence_threshold', 1.0)
    
    @silence_threshold.setter
    def silence_threshold(self, threshold: float) -> None:
        """Установка порога тишины"""
        if 'audio' not in self.config:
            self.config['audio'] = {}
        self.config['audio']['silence_threshold'] = threshold
    
    @property
    def max_recording_time(self) -> float:
        """Максимальное время записи в секундах"""
        return self.config.get('audio', {}).get('max_recording_time', 30.0)
    
    @max_recording_time.setter
    def max_recording_time(self, time: float) -> None:
        """Установка максимального времени записи"""
        if 'audio' not in self.config:
            self.config['audio'] = {}
        self.config['audio']['max_recording_time'] = time
    
    @property
    def record_hotkey(self) -> List[str]:
        """Горячая клавиша для начала записи"""
        return self.config.get('hotkeys', {}).get('record', ['alt', 'win', 'z'])
    
    @record_hotkey.setter
    def record_hotkey(self, keys: List[str]) -> None:
        """Установка горячей клавиши для записи"""
        if 'hotkeys' not in self.config:
            self.config['hotkeys'] = {}
        self.config['hotkeys']['record'] = keys
    
    @property
    def cancel_hotkey(self) -> List[str]:
        """Горячая клавиша для отмены записи"""
        return self.config.get('hotkeys', {}).get('cancel', ['escape'])
    
    @cancel_hotkey.setter
    def cancel_hotkey(self, keys: List[str]) -> None:
        """Установка горячей клавиши для отмены"""
        if 'hotkeys' not in self.config:
            self.config['hotkeys'] = {}
        self.config['hotkeys']['cancel'] = keys
    
    @property
    def mode(self) -> str:
        """Режим работы: 'hotkey' или 'auto'"""
        return self.config.get('mode', 'hotkey')
    
    @mode.setter
    def mode(self, mode: str) -> None:
        """Установка режима работы"""
        self.config['mode'] = mode
    
    @property
    def log_level(self) -> str:
        """Уровень логирования"""
        return self.config.get('log_level', 'info')
    
    @log_level.setter
    def log_level(self, level: str) -> None:
        """Установка уровня логирования"""
        self.config['log_level'] = level
    
    @property
    def gain(self) -> float:
        """Усиление микрофона"""
        return self.config.get('audio', {}).get('gain', 5.0)
    
    @gain.setter
    def gain(self, value: float) -> None:
        """Установка усиления микрофона"""
        if 'audio' not in self.config:
            self.config['audio'] = {}
        self.config['audio']['gain'] = value
        logger.info(f"Установлено усиление микрофона: {value}") 