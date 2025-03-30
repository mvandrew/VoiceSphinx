import torch
from loguru import logger
import sys

def print_gpu_info():
    """Вывод информации о доступных GPU устройствах"""
    if not torch.cuda.is_available():
        logger.error("CUDA недоступна. Проверьте установку CUDA Toolkit и драйверов NVIDIA.")
        return False
        
    device_count = torch.cuda.device_count()
    logger.info(f"Найдено GPU устройств: {device_count}")
    
    for i in range(device_count):
        device = torch.cuda.get_device_properties(i)
        logger.info(f"\nGPU {i}:")
        logger.info(f"  Название: {device.name}")
        logger.info(f"  Объем VRAM: {device.total_memory / 1024**3:.2f} GB")
        logger.info(f"  CUDA capability: {device.major}.{device.minor}")
        logger.info(f"  Максимальное количество потоков: {device.multi_processor_count}")
        
    return True

if __name__ == "__main__":
    print_gpu_info() 