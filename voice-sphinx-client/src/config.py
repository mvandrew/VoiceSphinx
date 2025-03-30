import json
import os
from typing import Dict, Any, List
from loguru import logger

class Config:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Загрузка конфигурации из JSON файла"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                logger.info(f"Конфигурация загружена из {self.config_path}")
                logger.debug(f"Загруженная конфигурация: {self.config}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Конфигурационный файл {self.config_path} не найден")
        except json.JSONDecodeError:
            raise ValueError(f"Ошибка в формате конфигурационного файла {self.config_path}")

    @property
    def server_url(self) -> str:
        """URL сервера для отправки аудио"""
        return self.config.get('server', {}).get('url', 'http://localhost:8000/transcribe')

    @property
    def sample_rate(self) -> int:
        """Частота дискретизации аудио"""
        return self.config.get('audio', {}).get('sample_rate', 16000)

    @property
    def channels(self) -> int:
        """Количество каналов аудио"""
        return self.config.get('audio', {}).get('channels', 1)

    @property
    def audio_device(self) -> Any:
        """Устройство для записи аудио"""
        return self.config.get('audio', {}).get('device', None)

    @property
    def vad_mode(self) -> int:
        """Режим VAD (1-3)"""
        return self.config.get('audio', {}).get('vad_mode', 3)

    @property
    def silence_threshold(self) -> float:
        """Порог тишины в секундах"""
        return self.config.get('audio', {}).get('silence_threshold', 1.0)

    @property
    def max_recording_time(self) -> float:
        """Максимальное время записи в секундах"""
        return self.config.get('audio', {}).get('max_recording_time', 30.0)

    @property
    def record_hotkey(self) -> List[str]:
        """Горячая клавиша для записи"""
        hotkey = self.config.get('hotkeys', {}).get('record', ['alt', 'win', 'z'])
        logger.info(f"Загружена комбинация клавиш для записи: {hotkey}")
        return hotkey

    @property
    def cancel_hotkey(self) -> List[str]:
        """Горячая клавиша для отмены"""
        hotkey = self.config.get('hotkeys', {}).get('cancel', ['escape'])
        logger.info(f"Загружена комбинация клавиш для отмены: {hotkey}")
        return hotkey

    @property
    def mode(self) -> str:
        """Режим работы (hotkey/auto)"""
        return self.config.get('mode', 'hotkey')

    @property
    def log_level(self) -> str:
        """Уровень логирования"""
        return self.config.get('log_level', 'info') 