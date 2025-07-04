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

# Импортируем только то, что нам нужно
from app.booking.handlers_fixed import process_place_type
from app.booking.services_admin_message import AdminMessageService
from app.database import get_session
from sqlalchemy import text

class MockCallbackQuery:
    """Имитация объекта callback query для тестирования"""
    def __init__(self, data, user_id=123456):
        self.data = data
        self.from_user = type('obj', (object,), {'id': user_id})
        self.message = type('obj', (object,), {
            'text': 'Тестовое сообщение',
            'edit_text': lambda **kwargs: logger.info(f"edit_text вызван с {kwargs}"),
            'answer': lambda **kwargs: logger.info(f"answer вызван с {kwargs}")
        })
    
    async def answer(self):
        logger.info("CallbackQuery.answer() вызван")

class MockState:
    """Имитация объекта state для тестирования"""
    def __init__(self):
        self.data = {"city": "Франкфурт"}
    
    async def get_data(self):
        return self.data
    
    async def update_data(self, **kwargs):
        self.data.update(kwargs)
        
    async def finish(self):
        logger.info("State.finish() вызван")

async def test_process_place_type():
    """Тест функции process_place_type из handlers_fixed.py"""
    logger.info("====== НАЧАЛО ТЕСТА process_place_type ======")
    
    # Проверяем, что функция импортирована из правильного файла
    import inspect
    source_file = inspect.getmodule(process_place_type).__file__
    logger.info(f"Функция process_place_type импортирована из {source_file}")
    
    # Проверяем, что это действительно файл handlers_fixed.py
    if not source_file.endswith('handlers_fixed.py'):
        logger.error("Функция импортирована из неправильного файла!")
        return
    
    # Имитируем callback query для типа "restaurant" в городе "Франкфурт"
    callback = MockCallbackQuery(data="booking:type:restaurant")
    state = MockState()
    
    # Добавляем тестовое админское сообщение в БД, если его еще нет
    try:
        async for session in get_session():
            # Проверяем наличие админского сообщения
            query = text("""
                SELECT COUNT(*) FROM dating_bot.admin_messages 
                WHERE city = 'Франкфурт' AND place_type = 'restaurant'
            """)
            result = await session.execute(query)
            count = result.scalar()
            
            logger.info(f"В БД найдено {count} админских сообщений для города 'Франкфурт' и типа 'restaurant'")
            
            if count == 0:
                # Добавляем новое сообщение
                await AdminMessageService.add_admin_message(
                    session=session,
                    city="Франкфурт",
                    place_type="restaurant",
                    message="Тестовое сообщение для ресторанов Франкфурта"
                )
                logger.info("Добавлено новое тестовое админское сообщение в БД")
    except Exception as e:
        logger.error(f"Ошибка при проверке/добавлении админского сообщения: {e}")
    
    # Запускаем функцию
    logger.info("Вызываем process_place_type с тестовыми данными")
    try:
        await process_place_type(callback, state)
        logger.info("Функция process_place_type успешно выполнена")
    except Exception as e:
        logger.error(f"Ошибка при выполнении process_place_type: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("====== КОНЕЦ ТЕСТА process_place_type ======")

if __name__ == "__main__":
    asyncio.run(test_process_place_type())
