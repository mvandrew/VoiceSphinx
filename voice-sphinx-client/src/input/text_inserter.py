import pyautogui
import time
from typing import Optional
from loguru import logger

class TextInserter:
    def __init__(self):
        # Настройка безопасности pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def insert_text(self, text: str) -> bool:
        """Вставка текста в активное окно"""
        if not text:
            return False

        try:
            # Небольшая задержка перед вставкой
            time.sleep(0.5)
            
            # Вставляем текст
            pyautogui.write(text)
            logger.info(f"Текст вставлен: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при вставке текста: {e}")
            return False 