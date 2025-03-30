from faster_whisper import WhisperModel
from loguru import logger
import json
import os
import sys

class WhisperTranscriber:
    def __init__(self, config_path: str = "config.json"):
        """Инициализация модели Whisper"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        model_config = self.config['model']
        logger.info(f"Загрузка модели Whisper {model_config['model_size']}...")
        
        try:
            # Устанавливаем переменную окружения для выбора GPU из конфигурации
            if 'cuda_device' in model_config:
                os.environ["CUDA_VISIBLE_DEVICES"] = str(model_config['cuda_device'])
                logger.info(f"Используется GPU: {model_config['cuda_device']}")
            
            # Инициализируем модель с правильными параметрами
            self.model = WhisperModel(
                model_size_or_path=model_config['model_size'],
                device=model_config['device'],
                compute_type=model_config['compute_type']
            )
            logger.info("Модель успешно загружена")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации модели: {str(e)}")
            logger.error("Проверьте:")
            logger.error("1. Установлен ли CUDA Toolkit")
            logger.error("2. Установлены ли драйверы NVIDIA")
            logger.error("3. Доступна ли указанная GPU")
            logger.error("4. Достаточно ли VRAM для загрузки модели")
            raise
        
    def transcribe(self, audio_path: str) -> str:
        """Транскрипция аудиофайла"""
        try:
            segments, _ = self.model.transcribe(
                audio_path,
                language=self.config['model']['language'],
                beam_size=self.config['model']['beam_size']
            )
            
            text = " ".join([segment.text for segment in segments])
            logger.info(f"Текст успешно распознан: {text[:100]}...")
            return text
            
        except Exception as e:
            logger.error(f"Ошибка при транскрипции: {str(e)}")
            logger.error("Проверьте:")
            logger.error("1. Корректность входного аудиофайла")
            logger.error("2. Достаточно ли VRAM для обработки")
            logger.error("3. Не произошло ли отключение GPU")
            raise 