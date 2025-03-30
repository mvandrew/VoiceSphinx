from pynput import keyboard
from typing import List, Set, Callable, Optional
from loguru import logger

class KeyboardListener:
    def __init__(self, config):
        self.config = config
        self.listener = None
        self.current_keys: Set[keyboard.Key] = set()
        self.record_callback: Optional[Callable] = None
        self.cancel_callback: Optional[Callable] = None

    def start(self) -> None:
        """Запуск прослушивания клавиатуры"""
        if self.listener:
            return

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        logger.info("Прослушивание клавиатуры запущено")
        logger.info(f"Ожидание комбинации клавиш: {self.config.record_hotkey}")

    def stop(self) -> None:
        """Остановка прослушивания клавиатуры"""
        if self.listener:
            self.listener.stop()
            self.listener = None
            logger.info("Прослушивание клавиатуры остановлено")

    def set_callbacks(self, record_callback: Callable, cancel_callback: Callable) -> None:
        """Установка callback-функций для обработки горячих клавиш"""
        self.record_callback = record_callback
        self.cancel_callback = cancel_callback

    def _on_press(self, key: keyboard.Key) -> None:
        """Обработка нажатия клавиши"""
        try:
            # Логируем нажатие клавиши
            key_str = str(key).lower()
            if isinstance(key, keyboard.Key):
                if key == keyboard.Key.cmd:
                    key_str = 'win'
                elif key == keyboard.Key.alt:
                    key_str = 'alt'
                elif key == keyboard.Key.ctrl:
                    key_str = 'ctrl'
                elif key == keyboard.Key.shift:
                    key_str = 'shift'
            
            logger.debug(f"Нажата клавиша: {key_str}")
            self.current_keys.add(key_str)

            # Логируем текущий набор клавиш
            current_keys_str = {str(k).lower() for k in self.current_keys}
            logger.debug(f"Текущие клавиши: {current_keys_str}")

            # Проверяем комбинацию для записи
            if self._check_hotkey(self.config.record_hotkey):
                logger.info("Обнаружена комбинация клавиш для записи")
                if self.record_callback:
                    self.record_callback()

            # Проверяем комбинацию для отмены
            if self._check_hotkey(self.config.cancel_hotkey):
                logger.info("Обнаружена комбинация клавиш для отмены")
                if self.cancel_callback:
                    self.cancel_callback()

        except Exception as e:
            logger.error(f"Ошибка при обработке нажатия клавиши: {e}")

    def _on_release(self, key: keyboard.Key) -> None:
        """Обработка отпускания клавиши"""
        try:
            # Логируем отпускание клавиши
            key_str = str(key).lower()
            if isinstance(key, keyboard.Key):
                if key == keyboard.Key.cmd:
                    key_str = 'win'
                elif key == keyboard.Key.alt:
                    key_str = 'alt'
                elif key == keyboard.Key.ctrl:
                    key_str = 'ctrl'
                elif key == keyboard.Key.shift:
                    key_str = 'shift'
            
            logger.debug(f"Отпущена клавиша: {key_str}")
            self.current_keys.discard(key_str)

            # Логируем текущий набор клавиш
            current_keys_str = {str(k).lower() for k in self.current_keys}
            logger.debug(f"Текущие клавиши: {current_keys_str}")

        except Exception as e:
            logger.error(f"Ошибка при обработке отпускания клавиши: {e}")

    def _check_hotkey(self, hotkey: List[str]) -> bool:
        """Проверка комбинации горячих клавиш"""
        try:
            current_keys_str = {str(k).lower() for k in self.current_keys}
            hotkey_str = {k.lower() for k in hotkey}
            
            # Логируем сравнение
            logger.debug(f"Сравнение комбинаций: текущие={current_keys_str}, ожидаемые={hotkey_str}")
            
            return current_keys_str == hotkey_str
        except Exception as e:
            logger.error(f"Ошибка при проверке горячих клавиш: {e}")
            return False 