from fastapi import APIRouter, UploadFile, HTTPException
from loguru import logger
import numpy as np
import soundfile as sf
import io

from ..models.whisper_model import WhisperTranscriber
from ..utils.audio import validate_audio, save_audio, cleanup_temp_file

router = APIRouter()
transcriber = WhisperTranscriber()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile):
    """Эндпоинт для транскрипции аудио"""
    try:
        # Читаем аудиофайл
        contents = await file.read()
        audio_data, sample_rate = sf.read(io.BytesIO(contents))
        
        # Проверяем формат аудио
        if not validate_audio(audio_data, sample_rate):
            raise HTTPException(status_code=400, detail="Неверный формат аудио")
        
        # Сохраняем во временный файл
        temp_file = save_audio(audio_data, sample_rate)
        
        try:
            # Транскрибируем
            text = transcriber.transcribe(temp_file)
            return {"text": text}
            
        finally:
            # Удаляем временный файл
            cleanup_temp_file(temp_file)
            
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 