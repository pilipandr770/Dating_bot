import asyncio
import os
import sys
import logging

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Функция для проверки файла __init__.py
async def check_imports():
    logger.info("Проверка файла app/booking/__init__.py...")
    
    # Импортируем register_booking_handlers и проверяем его источник
    try:
        from app.booking import register_booking_handlers
        import inspect
        source_file = inspect.getmodule(register_booking_handlers).__file__
        logger.info(f"register_booking_handlers импортирован из файла: {source_file}")
        
        # Проверяем, правильный ли это файл
        if "new_handlers.py" in source_file:
            logger.info("✅ Импорт корректен! Используется файл new_handlers.py")
        else:
            logger.error(f"❌ Импорт некорректен! Используется файл {source_file}")
            
        # Проверяем, что функция правильно зарегистрирована
        logger.info(f"Функция register_booking_handlers: {register_booking_handlers}")
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка: {e}")
    
    logger.info("Проверка завершена.")

# Запускаем проверку
if __name__ == "__main__":
    asyncio.run(check_imports())
