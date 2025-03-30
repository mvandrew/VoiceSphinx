import sys
import os
from loguru import logger

# Добавляем директорию src в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from config import Config
from audio.recorder import AudioRecorder
from network.api_client import APIClient
from input.text_inserter import TextInserter
from hotkeys.keyboard_listener import KeyboardListener

class VoiceSphinxClient:
    def __init__(self, config_path: str = "config.json"):
        # Инициализация компонентов
        self.config = Config(config_path)
        
        # Настройка логирования
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.config.log_level.upper()  # Преобразуем в верхний регистр для соответствия уровням loguru
        )

        # Инициализация остальных компонентов
        self.recorder = AudioRecorder(self.config)
        self.api_client = APIClient(self.config)
        self.text_inserter = TextInserter()
        self.keyboard_listener = KeyboardListener(self.config)

    def start(self) -> None:
        """Запуск клиента"""
        try:
            logger.info("Запуск VoiceSphinx Client...")
            
            if self.config.mode == "hotkey":
                self._start_hotkey_mode()
            else:
                self._start_auto_mode()
                
        except Exception as e:
            logger.error(f"Ошибка при запуске клиента: {e}")
            sys.exit(1)

    def _start_hotkey_mode(self) -> None:
        """Запуск режима с горячими клавишами"""
        logger.info("Запуск режима с горячими клавишами")
        
        def on_record():
            """Callback для начала записи"""
            if not self.recorder.recording:
                self.recorder.start_recording()
                logger.info("Начало записи по горячей клавише")

        def on_cancel():
            """Callback для отмены записи"""
            if self.recorder.recording:
                audio_data = self.recorder.stop_recording()
                if audio_data:
                    self._process_audio(audio_data)
                logger.info("Отмена записи по горячей клавише")

        # Устанавливаем callback-функции
        self.keyboard_listener.set_callbacks(on_record, on_cancel)
        self.keyboard_listener.start()

        # Держим программу запущенной
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.stop()

    def _start_auto_mode(self) -> None:
        """Запуск автоматического режима"""
        logger.info("Запуск автоматического режима")
        
        try:
            while True:
                self.recorder.start_recording()
                audio_data = self.recorder.stop_recording()
                if audio_data:
                    self._process_audio(audio_data)
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"Ошибка в автоматическом режиме: {e}")
            self.stop()

    def _process_audio(self, audio_data: bytes) -> None:
        """Обработка записанного аудио"""
        try:
            # Отправляем аудио на сервер
            text = self.api_client.transcribe_audio(audio_data)
            if text:
                # Вставляем распознанный текст
                self.text_inserter.insert_text(text)
        except Exception as e:
            logger.error(f"Ошибка при обработке аудио: {e}")

    def stop(self) -> None:
        """Остановка клиента"""
        try:
            if self.recorder.recording:
                self.recorder.stop_recording()
            self.keyboard_listener.stop()
            logger.info("VoiceSphinx Client остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке клиента: {e}")

def main():
    """Точка входа в программу"""
    try:
        client = VoiceSphinxClient()
        client.start()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 