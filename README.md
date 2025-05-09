# VoiceSphinx

Локальная система офлайн-распознавания речи с клиент-серверной архитектурой. Преобразует голос в текст через GPU-ускоренный сервер и вставляет результат в активное приложение. Работает без интернета на Windows и Linux.

## Описание проекта

VoiceSphinx предоставляет возможность распознавания голоса в текст без необходимости подключения к интернету. Система работает по принципу клиент-сервер, где:

- **Сервер** использует модель Whisper (faster-whisper) для распознавания речи и работает с GPU-ускорением
- **Клиент** записывает речь с микрофона, отправляет на сервер и вставляет полученный текст в активное окно

## Особенности

- **Офлайн-распознавание** - работает без интернета
- **GPU-ускорение** - использует возможности видеокарты для быстрого распознавания
- **Два режима работы клиента**:
  - **Режим по горячим клавишам** - запись начинается и завершается по нажатию клавиш
  - **Автоматический режим** - использует детектор голосовой активности для определения начала и конца речи
- **Кроссплатформенность** - поддержка Windows и Linux
- **Настраиваемые горячие клавиши** - возможность изменения комбинаций клавиш
- **Гибкая конфигурация** - настройка сервера и клиента через JSON-файлы

## Структура проекта

```
voice-sphinx/
├── voice-sphinx-server/          # Серверная часть
│   ├── app/                      # Код сервера
│   │   ├── api/                  # API-эндпоинты
│   │   ├── models/               # Работа с моделью распознавания
│   │   └── utils/                # Вспомогательные функции
│   ├── config.json               # Конфигурация сервера
│   ├── requirements.txt          # Зависимости сервера
│   ├── main.py                   # Точка входа сервера
│   └── run_server.bat            # Скрипт запуска на Windows
│
└── voice-sphinx-client/          # Клиентская часть
    ├── src/                      # Код клиента
    │   ├── audio/                # Работа с аудио
    │   ├── hotkeys/              # Обработка горячих клавиш
    │   ├── input/                # Вставка текста
    │   ├── network/              # Сетевое взаимодействие
    │   └── utils/                # Вспомогательные функции
    ├── config.json               # Конфигурация клиента
    ├── requirements.txt          # Зависимости клиента
    ├── main.py                   # Точка входа клиента
    └── mic_check.py              # Утилита проверки микрофона
```

## Установка и настройка

### Требования

#### Сервер
- Python 3.10+
- CUDA-совместимая видеокарта (для GPU-ускорения)
- CUDA Toolkit и cuDNN (для GPU-ускорения)

#### Клиент
- Python 3.10+
- Микрофон

### Установка сервера

1. Клонируйте репозиторий:
```bash
git clone https://github.com/username/voice-sphinx.git
cd voice-sphinx/voice-sphinx-server
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. Отредактируйте `config.json` для настройки модели и сервера.

4. Запустите сервер:
```bash
python main.py
```

### Установка клиента

1. Перейдите в директорию клиента:
```bash
cd voice-sphinx/voice-sphinx-client
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. Отредактируйте `config.json` для настройки параметров клиента.

4. Запустите клиент:
```bash
python main.py
```

## Использование

### Проверка микрофона

Перед использованием клиента рекомендуется проверить работу микрофона:

```bash
python main.py --list-mics    # Список доступных микрофонов
python main.py --test-mic     # Тестирование микрофона
python main.py --set-mic ID   # Установка определенного микрофона
```

### Запуск клиента

```bash
python main.py                # Запуск в обычном режиме
python main.py --mode auto    # Запуск в автоматическом режиме
python main.py --mode hotkey  # Запуск в режиме горячих клавиш
```

### Горячие клавиши по умолчанию

- `Alt+R` - начать запись
- `Escape` - отменить запись

## Конфигурация

### Конфигурация сервера (config.json)

```json
{
  "model": {
    "model_size": "large-v3",    // Размер модели Whisper
    "device": "cuda",            // cuda или cpu
    "compute_type": "float16",   // тип вычислений
    "language": "ru",            // Язык распознавания
    "beam_size": 5               // Параметр beam search
  },
  "server": {
    "host": "0.0.0.0",           // Адрес для прослушивания
    "port": 8000,                // Порт
    "log_level": "info"          // Уровень логирования
  }
}
```

### Конфигурация клиента (config.json)

```json
{
  "server": {
    "url": "http://localhost:8000/transcribe"  // URL сервера
  },
  "audio": {
    "device": null,                // Устройство (null = по умолчанию)
    "sample_rate": 16000,          // Частота дискретизации
    "channels": 1,                 // Моно
    "vad_mode": 1,                 // Чувствительность VAD (1-3)
    "silence_threshold": 1.5,      // Порог тишины в секундах
    "max_recording_time": 30.0     // Максимальное время записи
  },
  "hotkeys": {
    "start_recording": "alt+r",    // Горячая клавиша для начала записи
    "cancel_recording": "escape"   // Отмена записи
  },
  "mode": "hotkey",                // Режим работы: "hotkey" или "auto"
  "log_level": "debug"             // Уровень логирования
}
```

## Дополнительная информация

- Для работы сервера в офлайн-режиме необходимо предварительно загрузить модель Whisper
- При первом запуске модель будет загружена автоматически (требуется подключение к интернету)
- Для достижения наилучшего качества распознавания рекомендуется использовать хороший микрофон и тихое помещение

## Лицензия

Проект распространяется под лицензией [MIT](LICENSE).
