import soundfile as sf
import numpy as np
from loguru import logger
import tempfile
import os

def validate_audio(audio_data: np.ndarray, sample_rate: int) -> bool:
    """Проверка аудио на соответствие требованиям"""
    if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
        logger.error("Аудио должно быть моно")
        return False
        
    if sample_rate != 16000:
        logger.error(f"Частота дискретизации должна быть 16kHz, получено {sample_rate}Hz")
        return False
        
    return True

def save_audio(audio_data: np.ndarray, sample_rate: int) -> str:
    """Сохранение аудио во временный WAV файл"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, sample_rate)
            return temp_file.name
    except Exception as e:
        logger.error(f"Ошибка при сохранении аудио: {str(e)}")
        raise

def cleanup_temp_file(file_path: str):
    """Удаление временного файла"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.error(f"Ошибка при удалении временного файла: {str(e)}") 