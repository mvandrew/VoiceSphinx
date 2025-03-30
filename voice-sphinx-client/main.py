import sys
import os
import argparse
import time
import json
from loguru import logger

# Добавляем директорию src в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from src.config import Config
from src.audio.recorder import AudioRecorder
from src.network.api_client import APIClient
from src.input.text_inserter import TextInserter
from src.hotkeys.keyboard_listener import KeyboardListener
from src.utils.audio_utils import get_available_microphones, MicrophoneTester

def setup_logger(log_level: str) -> None:
    """Настройка логирования"""
    # Удаляем стандартный обработчик
    logger.remove()
    # Добавляем новый с заданным уровнем логирования
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level.upper()
    )

def list_microphones():
    """Вывод списка доступных микрофонов"""
    mics = get_available_microphones()
    
    if not mics:
        logger.error("Не найдены доступные микрофоны")
        return
    
    logger.info(f"Найдено {len(mics)} микрофонов:")
    for mic in mics:
        default_mark = " [По умолчанию]" if mic['default'] else ""
        logger.info(f"ID {mic['id']}: {mic['name']} ({mic['channels']} каналов){default_mark}")

def test_microphone(config, device_id=None, duration=3, force=False):
    """Тестирование микрофона и индикация уровня громкости"""
    # Временно устанавливаем устройство если передан device_id
    original_device = config.audio_device
    if device_id is not None:
        config.audio_device = device_id
    
    # Создаем тестировщик микрофона
    logger.info(f"Тестирование микрофона (ID: {config.audio_device if config.audio_device is not None else 'по умолчанию'})")
    
    # Сначала проверяем с помощью AudioRecorder
    recorder = AudioRecorder(config)
    mic_info = recorder.get_current_device_info()
    
    logger.info(f"Выбран микрофон: {mic_info['name']} (ID: {mic_info['id']})")
    logger.info(f"Параметры: gain={config.gain}, vad_mode={recorder.vad_mode}")
    
    # Проводим базовый тест микрофона
    if not recorder.test_microphone(0.5) and not force:
        logger.error("Тест микрофона не пройден! Используйте --force для принудительного использования.")
        if original_device is not None:
            config.audio_device = original_device
        return False
    
    # Тестируем уровень громкости в реальном времени с усилением сигнала
    tester = MicrophoneTester(mic_info['id'], config.sample_rate, config.channels, gain=config.gain)
    
    if not tester.start_monitoring():
        logger.error("Не удалось запустить мониторинг микрофона")
        if original_device is not None:
            config.audio_device = original_device
        return False
    
    try:
        logger.info(f"Слушаю микрофон в течение {duration} секунд. Говорите что-нибудь...")
        start_time = time.time()
        
        has_signal = False  # Флаг, определяющий, был ли получен сигнал выше порога
        max_level = 0.0     # Максимальный уровень сигнала
        
        while time.time() - start_time < duration:
            level = tester.get_audio_level()
            max_level = max(max_level, level)
            bar_length = int(level * 50)  # Увеличиваем множитель для лучшей визуализации
            
            if level < 0.002:  # Снижаем порог для красного индикатора
                message = f"[{'=' * bar_length}{' ' * (50 - bar_length)}] {level:.4f} - Очень тихо или микрофон не работает"
                color = "\033[91m"  # Красный
            elif level < 0.01:  # Снижаем порог для желтого индикатора
                has_signal = True
                message = f"[{'=' * bar_length}{' ' * (50 - bar_length)}] {level:.4f} - Тихо"
                color = "\033[93m"  # Желтый
            else:
                has_signal = True
                message = f"[{'=' * bar_length}{' ' * (50 - bar_length)}] {level:.4f} - Нормальный уровень"
                color = "\033[92m"  # Зеленый
                
            # Выводим индикатор с цветом если поддерживается терминалом
            # и очищаем строку для обновления
            sys.stdout.write('\r' + color + message + '\033[0m')
            sys.stdout.flush()
            
            time.sleep(0.1)
            
        print()  # Новая строка в конце
        logger.info(f"Максимальный уровень сигнала: {max_level:.4f}")
        
    finally:
        tester.stop_monitoring()
    
    success = False
    try:    
        # Записываем короткий тестовый аудиофрагмент
        logger.info("Записываю тестовый аудиофрагмент (3 секунды)...")
        recorder.start_recording()
        time.sleep(3)
        wav_data = recorder.stop_recording()
        
        if wav_data and len(wav_data) > 1000:  # Проверяем, что получены какие-то данные
            logger.info(f"Тестовая запись успешна (размер данных: {len(wav_data)} байт)")
            success = True
        else:
            logger.error("Не удалось записать тестовый аудиофрагмент или данные слишком малы")
    except Exception as e:
        logger.error(f"Ошибка при записи тестового фрагмента: {e}")
        success = False
    
    # Восстанавливаем исходное устройство
    if original_device is not None:
        config.audio_device = original_device
    
    # Даже если сигнал был слабым, но он был, то считаем, что тест пройден
    if force or has_signal or success:
        if not has_signal and not success:
            logger.warning("Тест пройден принудительно (--force), но сигнал отсутствует или очень слабый")
        return True
    else:
        logger.error("Тест микрофона не пройден: не обнаружен звуковой сигнал")
        return False

def set_microphone(config, device_id):
    """Установка микрофона в конфигурации"""
    try:
        # Если передан ID устройства
        device_id_int = int(device_id)
        # Проверяем, существует ли устройство с таким ID
        mics = get_available_microphones()
        found = False
        for mic in mics:
            if mic['id'] == device_id_int:
                logger.info(f"Устанавливаю микрофон: {mic['name']} (ID: {device_id_int})")
                found = True
                break
                
        if not found:
            logger.error(f"Микрофон с ID {device_id_int} не найден")
            return False
            
        config.audio_device = device_id_int
        config.save_config()
        return True
    except ValueError:
        # Если передано имя устройства или "default"
        if device_id.lower() == "default":
            logger.info("Устанавливаю микрофон по умолчанию")
            config.audio_device = None
            config.save_config()
            return True
            
        # Ищем микрофон по имени
        mics = get_available_microphones()
        for mic in mics:
            if device_id.lower() in mic['name'].lower():
                logger.info(f"Устанавливаю микрофон: {mic['name']} (ID: {mic['id']})")
                config.audio_device = device_id
                config.save_config()
                return True
                
        logger.error(f"Микрофон с именем '{device_id}' не найден")
        return False

class VoiceSphinxClient:
    def __init__(self, config_path: str = "config.json"):
        # Инициализация компонентов
        self.config = Config(config_path)
        
        # Настройка логирования
        setup_logger(self.config.log_level)

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

def run_client():
    """Запуск основного клиента приложения"""
    try:
        client = VoiceSphinxClient()
        client.start()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

class Config:
    """Класс для хранения конфигурации приложения"""
    def __init__(self, config_data):
        # Серверные настройки
        server_config = config_data.get('server', {})
        self.server_url = server_config.get('url', "http://localhost:8000/transcribe")
        
        # Аудио настройки
        audio_config = config_data.get('audio', {})
        self.audio_device = audio_config.get('device', None)
        self.sample_rate = audio_config.get('sample_rate', 16000)
        self.channels = audio_config.get('channels', 1)
        self.vad_mode = audio_config.get('vad_mode', 1)
        self.silence_threshold = audio_config.get('silence_threshold', 1.5)
        self.max_recording_time = audio_config.get('max_recording_time', 30.0)
        self.gain = audio_config.get('gain', 10.0)
        self.min_speech_level = audio_config.get('min_speech_level', 0.008)
        
        # Горячие клавиши
        hotkeys_config = config_data.get('hotkeys', {})
        self.start_recording_hotkey = hotkeys_config.get('start_recording', "alt+r")
        self.cancel_recording_hotkey = hotkeys_config.get('cancel_recording', "escape")
        
        # Общие настройки
        self.mode = config_data.get('mode', 'hotkey')
        self.log_level = config_data.get('log_level', 'info')
        self.audio_dump_path = config_data.get('audio_dump_path', 'audio_dump')
        self.history_size = config_data.get('history_size', 5)

def load_config(config_path='config.json'):
    """Загрузка конфигурации из JSON-файла"""
    try:
        # Преобразуем путь в абсолютный, если он относительный
        if not os.path.isabs(config_path):
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
            
        logger.info(f"Загрузка конфигурации из {config_path}")
        
        if not os.path.exists(config_path):
            logger.error(f"Файл конфигурации не найден: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            
        # Создаем объект конфигурации из загруженных данных
        return Config(config_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при разборе JSON конфигурации: {e}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}")
        
    return None

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="VoiceSphinx Client - Локальная система распознавания речи")
    parser.add_argument('--config', default='config.json', help='Путь к конфигурационному файлу')
    parser.add_argument('--list-mics', action='store_true', help='Показать список доступных микрофонов')
    parser.add_argument('--test-mic', action='store_true', help='Тестировать текущий микрофон')
    parser.add_argument('--test-mic-id', type=str, help='Тестировать микрофон с указанным ID/именем')
    parser.add_argument('--set-mic', type=str, help='Установить микрофон (ID, имя или "default")')
    parser.add_argument('--run', action='store_true', help='Запустить клиент')
    parser.add_argument('--force', action='store_true', help='Принудительно считать тест микрофона пройденным, даже если сигнал слабый')
    
    args = parser.parse_args()
    
    # Загружаем конфигурацию
    config = load_config(args.config)
    if config is None:
        logger.error("Не удалось загрузить конфигурацию, использую настройки по умолчанию")
        config = Config({})  # Создаем конфигурацию с настройками по умолчанию
    
    # Настраиваем логирование
    setup_logger(config.log_level)
    
    # Выполняем запрошенные операции
    if args.list_mics:
        list_microphones()
    elif args.test_mic:
        test_microphone(config, force=args.force)
    elif args.test_mic_id:
        test_microphone(config, args.test_mic_id, force=args.force)
    elif args.set_mic:
        set_microphone(config, args.set_mic)
    elif args.run:
        run_client()
    else:
        run_client()  # По умолчанию запускаем клиент

if __name__ == "__main__":
    main() 