#!/usr/bin/env python3
import argparse
import time
import os
import sys
from loguru import logger
from src.config import Config
from src.audio.recorder import AudioRecorder
from src.utils.audio_utils import get_available_microphones, MicrophoneTester

def setup_logger(log_level: str) -> None:
    """Настройка логирования"""
    # Удаляем стандартный обработчик
    logger.remove()
    # Добавляем новый с заданным уровнем логирования
    logger.add(sys.stderr, level=log_level.upper())

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

def test_microphone(config, device_id=None, duration=3):
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
    
    # Проводим базовый тест микрофона
    if not recorder.test_microphone(0.5):
        logger.error("Тест микрофона не пройден!")
        if original_device is not None:
            config.audio_device = original_device
        return False
    
    # Тестируем уровень громкости в реальном времени
    tester = MicrophoneTester(mic_info['id'], config.sample_rate, config.channels)
    
    if not tester.start_monitoring():
        logger.error("Не удалось запустить мониторинг микрофона")
        if original_device is not None:
            config.audio_device = original_device
        return False
    
    try:
        logger.info(f"Слушаю микрофон в течение {duration} секунд. Говорите что-нибудь...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            level = tester.get_audio_level()
            bar_length = int(level * 30)  # 30 символов для максимальной громкости
            
            if level < 0.05:
                message = f"[{'=' * bar_length}{' ' * (30 - bar_length)}] {level:.2f} - Очень тихо или микрофон не работает"
                color = "\033[91m"  # Красный
            elif level < 0.2:
                message = f"[{'=' * bar_length}{' ' * (30 - bar_length)}] {level:.2f} - Тихо"
                color = "\033[93m"  # Желтый
            else:
                message = f"[{'=' * bar_length}{' ' * (30 - bar_length)}] {level:.2f} - Нормальный уровень"
                color = "\033[92m"  # Зеленый
                
            # Выводим индикатор с цветом если поддерживается терминалом
            # и очищаем строку для обновления
            sys.stdout.write('\r' + color + message + '\033[0m')
            sys.stdout.flush()
            
            time.sleep(0.1)
            
        print()  # Новая строка в конце
        
    finally:
        tester.stop_monitoring()
        
    # Записываем короткий тестовый аудиофрагмент
    logger.info("Записываю тестовый аудиофрагмент (3 секунды)...")
    recorder.start_recording()
    time.sleep(3)
    wav_data = recorder.stop_recording()
    
    if wav_data and len(wav_data) > 1000:  # Проверяем, что получены какие-то данные
        logger.info(f"Тестовая запись успешна (размер данных: {len(wav_data)} байт)")
        success = True
    else:
        logger.error("Не удалось записать тестовый аудиофрагмент")
        success = False
    
    # Восстанавливаем исходное устройство
    if original_device is not None:
        config.audio_device = original_device
        
    return success

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

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="VoiceSphinx Client - Работа с микрофоном")
    parser.add_argument('--config', default='config.json', help='Путь к конфигурационному файлу')
    parser.add_argument('--list-mics', action='store_true', help='Показать список доступных микрофонов')
    parser.add_argument('--test-mic', action='store_true', help='Тестировать текущий микрофон')
    parser.add_argument('--test-mic-id', type=str, help='Тестировать микрофон с указанным ID/именем')
    parser.add_argument('--set-mic', type=str, help='Установить микрофон (ID, имя или "default")')
    
    args = parser.parse_args()
    
    # Загружаем конфигурацию
    config = Config(args.config)
    
    # Настраиваем логирование
    setup_logger(config.log_level)
    
    # Выполняем запрошенные операции
    if args.list_mics:
        list_microphones()
    elif args.test_mic:
        test_microphone(config)
    elif args.test_mic_id:
        test_microphone(config, args.test_mic_id)
    elif args.set_mic:
        set_microphone(config, args.set_mic)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 