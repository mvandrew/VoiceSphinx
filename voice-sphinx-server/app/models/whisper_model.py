import whisper
from loguru import logger
import json
import os

class WhisperTranscriber:
    def __init__(self, config_path: str = "config.json"):
        """Инициализация модели Whisper"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        model_config = self.config['model']
        logger.info(f"Загрузка модели Whisper {model_config['model_size']}...")
        
        self.model = whisper.load_model(
            name=model_config['model_size'],
            device=model_config['device']
        )
        logger.info("Модель успешно загружена")
        
    def transcribe(self, audio_path: str) -> str:
        """Транскрипция аудиофайла"""
        try:
            result = self.model.transcribe(
                audio_path,
                language=self.config['model']['language'],
                beam_size=self.config['model']['beam_size']
            )
            
            text = result["text"]
            logger.info(f"Текст успешно распознан: {text[:100]}...")
            return text
            
        except Exception as e:
            logger.error(f"Ошибка при транскрипции: {str(e)}")
            raise 