import uvicorn
from fastapi import FastAPI
from loguru import logger
import json
import os

from app.api.transcription import router as transcription_router
from app.utils.logging import setup_logging

# Создаем директорию для логов
os.makedirs("logs", exist_ok=True)

# Настраиваем логирование
setup_logging()

# Загружаем конфигурацию
with open("config.json", 'r', encoding='utf-8') as f:
    config = json.load(f)

app = FastAPI(
    title="VoiceSphinx Server",
    description="Сервер для офлайн-распознавания речи с использованием Whisper",
    version="1.0.0"
)

# Подключаем роутер
app.include_router(transcription_router)

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "status": "ok",
        "message": "VoiceSphinx Server работает",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    server_config = config['server']
    uvicorn.run(
        "main:app",
        host=server_config['host'],
        port=server_config['port'],
        reload=True
    )
