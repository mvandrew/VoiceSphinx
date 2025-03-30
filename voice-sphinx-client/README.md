# VoiceSphinx Client

Клиентская часть системы офлайн-распознавания речи VoiceSphinx.

## Возможности

- Запись речи с микрофона
- Два режима работы:
  - Режим по горячей клавише (Win + Alt + Z)
  - Автоматический режим с VAD
- Отправка аудио на сервер
- Вставка распознанного текста в активное окно
- Кроссплатформенность (Windows/Linux)
- Настраиваемые параметры через config.json

## Требования

- Python 3.10+
- Микрофон
- Доступ к серверу VoiceSphinx

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/voice-sphinx.git
cd voice-sphinx/voice-sphinx-client
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Конфигурация

Настройки клиента находятся в файле `config.json`:

```json
{
  "server": {
    "url": "http://localhost:8000/transcribe"
  },
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "device": null,
    "vad_mode": 3,
    "silence_threshold": 1.0,
    "max_recording_time": 30.0
  },
  "hotkeys": {
    "record": ["alt", "win", "z"],
    "cancel": ["escape"]
  },
  "mode": "hotkey",
  "log_level": "info"
}
```

### Параметры конфигурации

- `server.url`: URL сервера для отправки аудио
- `audio.sample_rate`: Частота дискретизации аудио
- `audio.channels`: Количество каналов аудио
- `audio.device`: ID устройства для записи (null = по умолчанию)
- `audio.vad_mode`: Режим VAD (1-3)
- `audio.silence_threshold`: Порог тишины в секундах
- `audio.max_recording_time`: Максимальное время записи в секундах
- `hotkeys.record`: Горячая клавиша для записи
- `hotkeys.cancel`: Горячая клавиша для отмены
- `mode`: Режим работы ("hotkey" или "auto")
- `log_level`: Уровень логирования

## Использование

1. Запустите клиент:
```bash
python src/main.py
```

2. В режиме по горячей клавише:
   - Нажмите Win + Alt + Z для начала записи
   - Говорите
   - Отпустите клавиши для остановки записи
   - Текст будет автоматически вставлен в активное окно

3. В автоматическом режиме:
   - Клиент автоматически определяет речь
   - При обнаружении тишины запись останавливается
   - Текст автоматически вставляется в активное окно

## Логирование

Логи выводятся в консоль с указанием времени, уровня, модуля и сообщения.

## Разработка

### Структура проекта

```
voice-sphinx-client/
├── src/
│   ├── __init__.py
│   ├── main.py              # Точка входа
│   ├── config.py            # Конфигурация
│   ├── audio/               # Модули для работы с аудио
│   │   ├── __init__.py
│   │   └── recorder.py
│   ├── network/             # Сетевое взаимодействие
│   │   ├── __init__.py
│   │   └── api_client.py
│   ├── input/               # Вставка текста
│   │   ├── __init__.py
│   │   └── text_inserter.py
│   ├── hotkeys/             # Обработка горячих клавиш
│   │   ├── __init__.py
│   │   └── keyboard_listener.py
│   └── utils/               # Вспомогательные функции
│       ├── __init__.py
│       └── platform_utils.py
├── requirements.txt
├── config.json
└── README.md
```

## Лицензия

MIT 