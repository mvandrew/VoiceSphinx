import sys
import os
from loguru import logger
import torch

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_cuda_info():
    """Вывод информации о CUDA и PyTorch"""
    logger.info("=== Информация о CUDA и PyTorch ===")
    logger.info(f"PyTorch версия: {torch.__version__}")
    logger.info(f"CUDA доступна: {torch.cuda.is_available()}")
    
    # Проверка переменных окружения CUDA
    logger.info("\n=== Переменные окружения CUDA ===")
    cuda_home = os.environ.get('CUDA_HOME')
    cuda_path = os.environ.get('CUDA_PATH')
    cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES')
    
    logger.info(f"CUDA_HOME: {cuda_home}")
    logger.info(f"CUDA_PATH: {cuda_path}")
    logger.info(f"CUDA_VISIBLE_DEVICES: {cuda_visible_devices}")
    
    # Проверка путей CUDA
    if cuda_path:
        cuda_bin = os.path.join(cuda_path, 'bin')
        cuda_lib = os.path.join(cuda_path, 'libnvvp')
        logger.info(f"CUDA bin существует: {os.path.exists(cuda_bin)}")
        logger.info(f"CUDA lib существует: {os.path.exists(cuda_lib)}")
    
    if torch.cuda.is_available():
        logger.info(f"\nВерсия CUDA: {torch.version.cuda}")
        logger.info(f"Количество GPU: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            device = torch.cuda.get_device_properties(i)
            logger.info(f"\nGPU {i}:")
            logger.info(f"  Название: {device.name}")
            logger.info(f"  Объем VRAM: {device.total_memory / 1024**3:.2f} GB")
            logger.info(f"  CUDA capability: {device.major}.{device.minor}")
            logger.info(f"  Максимальное количество потоков: {device.multi_processor_count}")
    else:
        logger.error("\nCUDA недоступна. Проверьте:")
        logger.error("1. Установлен ли CUDA Toolkit")
        logger.error("2. Установлены ли драйверы NVIDIA")
        logger.error("3. Установлен ли PyTorch с поддержкой CUDA")
        logger.error("\nРекомендуемые действия:")
        logger.error("1. Удалите текущую версию PyTorch:")
        logger.error("   pip uninstall torch torchvision torchaudio")
        logger.error("2. Установите PyTorch с поддержкой CUDA:")
        logger.error("   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        logger.error("\n3. Проверьте переменные окружения:")
        logger.error("   - CUDA_HOME или CUDA_PATH должны указывать на директорию CUDA")
        logger.error("   - Путь к CUDA должен быть добавлен в PATH")

if __name__ == "__main__":
    print_cuda_info() 