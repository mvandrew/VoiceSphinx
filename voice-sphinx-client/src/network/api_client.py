import requests
from typing import Optional
from loguru import logger

class APIClient:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()

    def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Отправка аудио на сервер и получение транскрипции"""
        try:
            files = {'file': ('audio.wav', audio_data, 'audio/wav')}
            response = self.session.post(
                self.config.server_url,
                files=files,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if 'text' not in result:
                logger.error("Сервер вернул ответ без текста")
                return None
                
            return result['text']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при отправке аудио на сервер: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при работе с API: {e}")
            return None 