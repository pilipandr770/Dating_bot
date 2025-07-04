#!/usr/bin/env python
# app/booking/test_buttons.py

import asyncio
import logging
from aiogram.types import CallbackQuery
from sqlalchemy import text
from app.database import get_session, init_db
from app.booking.services_admin_message import AdminMessageService
from app.booking.models import AdminMessage, Place

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def test_admin_message_retrieval():
    """
    Тестирует получение админских сообщений для разных комбинаций города и типа заведения.
    Имитирует поведение при нажатии на кнопки выбора типа заведения.
    """
    logger.info("=== НАЧАЛО ТЕСТА ПОЛУЧЕНИЯ АДМИНСКИХ СООБЩЕНИЙ ===")
    
    try:
        await init_db()
        
        # Получаем все типы и города из базы данных
        async for session in get_session():
            # Проверяем, есть ли админские сообщения в БД
            admin_messages_query = "SELECT * FROM dating_bot.admin_messages"
            admin_messages_result = await session.execute(admin_messages_query)
            admin_messages = admin_messages_result.fetchall()
            
            if not admin_messages:
                logger.warning("⚠️ Таблица admin_messages пуста. Добавляем тестовые сообщения...")
                await AdminMessageService.add_admin_message(
                    session=session,
                    city='Франкфурт',
                    place_type='restaurant',
                    message='Тестовое сообщение для ресторанов Франкфурта! Скидка 10% по промокоду SOUL_LINK'
                )
                await AdminMessageService.add_admin_message(
                    session=session,
                    city='Франкфурт',
                    place_type='park',
                    message='Специальное сообщение для парков! Бесплатное посещение ботанического сада по выходным.'
                )
                logger.info("✅ Тестовые сообщения добавлены в БД")
            else:
                logger.info(f"ℹ️ В таблице admin_messages уже есть {len(admin_messages)} записей")
                for msg in admin_messages:
                    logger.info(f"Запись: город='{msg.city}', тип='{msg.place_type}', сообщение='{msg.message[:30]}...'")
            
            # Получаем все уникальные города из таблицы places
            cities_query = "SELECT DISTINCT city FROM dating_bot.places WHERE city IS NOT NULL"
            cities_result = await session.execute(cities_query)
            cities = [row[0] for row in cities_result.fetchall()]
            
            # Получаем все уникальные типы заведений из таблицы places
            types_query = "SELECT DISTINCT type FROM dating_bot.places WHERE type IS NOT NULL"
            types_result = await session.execute(types_query)
            place_types = [row[0] for row in types_result.fetchall()]
            
            logger.info(f"Найдено городов: {len(cities)}, типов заведений: {len(place_types)}")
            
            # Тестируем получение админских сообщений для каждой комбинации город-тип
            for city in cities:
                for place_type in place_types:
                    logger.info(f"\n--- Тест для города '{city}' и типа '{place_type}' ---")
                    
                    # Имитируем логику из process_place_type
                    admin_message = await AdminMessageService.get_admin_message(session, city, place_type)
                    
                    if admin_message:
                        logger.info(f"✅ Получено админское сообщение: {admin_message}")
                    else:
                        logger.warning(f"⚠️ Админское сообщение не найдено")
                        
                        # Пробуем запросить напрямую через SQL
                        direct_query = text("""
                            SELECT message FROM dating_bot.admin_messages 
                            WHERE LOWER(city) LIKE LOWER(:city_pattern) 
                            AND LOWER(place_type) = LOWER(:place_type) 
                            LIMIT 1
                        """).bindparams(city_pattern=f"%{city}%", place_type=place_type)
                        
                        direct_result = await session.execute(direct_query)
                        direct_row = direct_result.fetchone()
                        
                        if direct_row:
                            logger.info(f"✅ Получено админское сообщение через прямой SQL: {direct_row[0]}")
                        else:
                            logger.warning("❌ Админское сообщение не найдено даже через прямой SQL")
                    
                    # Также проверяем, есть ли заведения для этой комбинации
                    venues_query = text("""
                        SELECT * FROM dating_bot.places 
                        WHERE LOWER(city) LIKE LOWER(:city_pattern)
                        AND LOWER(type) = LOWER(:place_type)
                    """).bindparams(city_pattern=f"%{city}%", place_type=place_type)
                    
                    venues_result = await session.execute(venues_query)
                    venues = venues_result.fetchall()
                    
                    if venues:
                        logger.info(f"Найдено {len(venues)} заведений для города '{city}' и типа '{place_type}'")
                        for venue in venues[:3]:  # Показываем только первые 3
                            logger.info(f"Заведение: {venue.name}")
                    else:
                        logger.info(f"Для города '{city}' и типа '{place_type}' заведений не найдено")
    
    except Exception as e:
        logger.error(f"Ошибка при тестировании получения админских сообщений: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("=== КОНЕЦ ТЕСТА ПОЛУЧЕНИЯ АДМИНСКИХ СООБЩЕНИЙ ===")

async def simulate_button_click():
    """
    Имитирует нажатие на кнопку выбора типа заведения и обработку callback_query
    """
    logger.info("=== НАЧАЛО ИМИТАЦИИ НАЖАТИЯ НА КНОПКУ ===")
    
    try:
        await init_db()
        
        # Для каждого типа заведения имитируем нажатие на кнопку
        place_types = ['restaurant', 'cafe', 'bar', 'park']
        
        for place_type in place_types:
            logger.info(f"\n--- Имитация нажатия на кнопку типа '{place_type}' ---")
            
            # Имитируем часть логики из process_place_type
            async for session in get_session():
                # Получаем админское сообщение
                city = 'Франкфурт'  # Используем фиксированный город для теста
                
                logger.info(f"Запрос админского сообщения для города '{city}' и типа '{place_type}'")
                admin_message = await AdminMessageService.get_admin_message(session, city, place_type)
                
                if admin_message:
                    logger.info(f"✅ Получено админское сообщение: {admin_message}")
                    
                    # Имитируем создание сообщения с админским сообщением
                    message_text = f"Вы выбрали: {place_type}\n\nДоступные заведения этого типа:"
                    
                    if isinstance(admin_message, str) and admin_message.strip():
                        message_text += f"\n\nℹ️ {admin_message}"
                        logger.info(f"Сообщение с добавленным админским сообщением:\n{message_text}")
                    else:
                        logger.warning(f"Некорректный формат админского сообщения: {admin_message}, тип: {type(admin_message).__name__}")
                else:
                    logger.warning(f"❌ Админское сообщение для города '{city}' и типа '{place_type}' не найдено")
    
    except Exception as e:
        logger.error(f"Ошибка при имитации нажатия на кнопку: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("=== КОНЕЦ ИМИТАЦИИ НАЖАТИЯ НА КНОПКУ ===")

async def main():
    """Основная функция для тестирования"""
    logger.info("Запуск тестов бота...")
    
    # Тестируем получение админских сообщений
    await test_admin_message_retrieval()
    
    # Имитируем нажатие на кнопки
    await simulate_button_click()
    
    logger.info("Тестирование завершено.")

if __name__ == "__main__":
    asyncio.run(main())
