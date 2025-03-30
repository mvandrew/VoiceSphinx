#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Простая утилита для проверки работы микрофона
Запустите с помощью: python mic_check.py
"""

import sounddevice as sd
import numpy as np
import time
import sys
import argparse

def list_devices():
    """Вывод списка доступных устройств"""
    print("Доступные устройства:")
    devices = sd.query_devices()
    
    for i, dev in enumerate(devices):
        input_channels = dev.get('max_input_channels', 0)
        if input_channels > 0:  # Это устройство ввода (микрофон)
            default = " [По умолчанию]" if dev.get('default_input') else ""
            print(f"ID {i}: {dev['name']} (вход: {input_channels} каналов){default}")

def record_and_check_mic(device_id=None, duration=3, sample_rate=16000, channels=1, gain=1.0):
    """Запись с микрофона и проверка уровня сигнала"""
    # Получаем информацию об устройстве
    try:
        if device_id is not None:
            device_info = sd.query_devices(device_id)
            print(f"Используется микрофон: {device_info['name']} (ID: {device_id})")
        else:
            default_device = sd.query_devices(kind='input')
            print(f"Используется микрофон по умолчанию: {default_device['name']}")
    except Exception as e:
        print(f"Ошибка при получении информации об устройстве: {e}")
        return
    
    # Записываем аудио
    print(f"Запись с микрофона {duration} секунд... Говорите что-нибудь")
    
    try:
        # Создаем массив для записи
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            device=device_id,
            dtype='float32'
        )
        
        # Отображаем прогресс
        for i in range(duration * 10):
            progress = i / (duration * 10)
            bar_length = int(progress * 30)
            sys.stdout.write(f"\rЗапись: [{'=' * bar_length}{' ' * (30 - bar_length)}] {int(progress * 100)}%")
            sys.stdout.flush()
            time.sleep(0.1)
        
        # Ждем окончания записи
        sd.wait()
        print("\nЗапись завершена!")
        
        # Нормализуем и усиливаем сигнал
        if gain != 1.0:
            recording = recording * gain
            print(f"Применено усиление: {gain}x")
            
        # Проверяем уровень сигнала
        original_rms = np.sqrt(np.mean(recording**2))
        original_peak = np.max(np.abs(recording))
        
        # Нормализуем сигнал для более надежного анализа
        # Удаляем тишину в начале и конце
        noise_floor = 0.0001  # Порог тишины
        is_signal = np.abs(recording) > noise_floor
        if np.any(is_signal):
            # Берем только части с сигналом для анализа
            signal_only = recording[is_signal]
            if len(signal_only) > 0:
                rms = np.sqrt(np.mean(signal_only**2))
                peak = np.max(np.abs(signal_only))
            else:
                rms = original_rms
                peak = original_peak
        else:
            rms = original_rms
            peak = original_peak
        
        print(f"Исходный RMS уровень: {original_rms:.6f}")
        print(f"Исходный пиковый уровень: {original_peak:.6f}")
        print(f"Отфильтрованный RMS уровень: {rms:.6f}")
        print(f"Отфильтрованный пиковый уровень: {peak:.6f}")
        
        # Отображаем уровень в виде визуальной шкалы
        # Используем более низкий порог для адаптации к чувствительности микрофона
        bar_length = min(int(rms * 200), 50)  # Умножаем на 200 вместо 100
        
        if rms > 0.005:  # Снижен порог (был 0.01)
            print(f"Уровень сигнала: [{'#' * bar_length}{' ' * (50 - bar_length)}] - Отлично!")
            print("Микрофон работает корректно.")
        elif rms > 0.0005:  # Снижен порог (был 0.001)
            print(f"Уровень сигнала: [{'#' * bar_length}{' ' * (50 - bar_length)}] - Нормальный")
            print("Микрофон работает, сигнал обнаружен.")
        elif rms > 0.00005:  # Снижен порог (был 0.0001)
            print(f"Уровень сигнала: [{'#' * bar_length}{' ' * (50 - bar_length)}] - Слабый")
            print("Сигнал обнаружен, но очень слабый. Добавлено усиление для анализа.")
        else:
            print(f"Уровень сигнала: [{'#' * bar_length}{' ' * (50 - bar_length)}] - Критически низкий")
            print("Микрофон не улавливает звук или сигнал слишком слабый. Проверьте подключение и системные настройки.")
            
        # Рекомендации по настройке
        if original_rms < 0.001:
            print("\nРекомендации:")
            print("1. Проверьте, что микрофон не выключен или заблокирован в системе")
            print("2. Увеличьте уровень микрофона в настройках операционной системы")
            print("3. Попробуйте запустить с параметром --gain для усиления сигнала:")
            print("   python mic_check.py --gain 5.0")
            print("4. При использовании в основном приложении, добавьте параметр --force:")
            print("   python main.py --test-mic --force")
            
    except Exception as e:
        print(f"\nОшибка при записи с микрофона: {e}")
        print("Проверьте, правильно ли выбран микрофон и работает ли он в системе.")

def main():
    parser = argparse.ArgumentParser(description="Проверка работы микрофона")
    parser.add_argument('--list', action='store_true', help='Показать список доступных микрофонов')
    parser.add_argument('--device', type=int, help='ID микрофона для проверки')
    parser.add_argument('--duration', type=int, default=3, help='Длительность записи в секундах')
    parser.add_argument('--sample-rate', type=int, default=16000, help='Частота дискретизации')
    parser.add_argument('--channels', type=int, default=1, help='Количество каналов')
    parser.add_argument('--gain', type=float, default=1.0, help='Усиление сигнала для анализа (1.0 = без усиления)')
    
    args = parser.parse_args()
    
    if args.list:
        list_devices()
    else:
        record_and_check_mic(
            device_id=args.device,
            duration=args.duration,
            sample_rate=args.sample_rate,
            channels=args.channels,
            gain=args.gain
        )

if __name__ == "__main__":
    main() 