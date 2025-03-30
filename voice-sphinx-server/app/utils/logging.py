from loguru import logger
import json
import sys

def setup_logging(config_path: str = "config.json"):
    """Настройка логирования"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    log_level = config['server']['log_level']
    
    # Удаляем стандартный обработчик
    logger.remove()
    
    # Добавляем вывод в консоль
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level.upper()
    )
    
    # Добавляем вывод в файл
    logger.add(
        "logs/server.log",
        rotation="500 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level.upper()
    ) 