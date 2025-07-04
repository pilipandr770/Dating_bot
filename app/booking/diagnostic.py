#!/usr/bin/env python
# app/booking/diagnostic.py

import asyncio
import logging
from sqlalchemy import text
from app.database import get_session
from app.booking.models import AdminMessage, Place

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def check_tables():
    """Проверяет наличие и структуру таблиц в базе данных"""
    logger.info("=== НАЧАЛО ДИАГНОСТИКИ ТАБЛИЦ ===")
    
    try:
        async for session in get_session():
            # Проверяем таблицу admin_messages
            logger.info("--- Проверка таблицы admin_messages ---")
            
            # Проверяем наличие таблицы
            check_admin_msg_table = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'dating_bot'
                    AND table_name = 'admin_messages'
                );
            """)
            result = await session.execute(check_admin_msg_table)
            admin_msg_table_exists = result.scalar()
            
            if admin_msg_table_exists:
                logger.info("✅ Таблица admin_messages существует")
                
                # Выводим структуру таблицы
                structure_query = text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns
                    WHERE table_schema = 'dating_bot'
                    AND table_name = 'admin_messages'
                    ORDER BY ordinal_position;
                """)
                structure_result = await session.execute(structure_query)
                columns = structure_result.fetchall()
                
                logger.info("Структура таблицы admin_messages:")
                for col in columns:
                    logger.info(f"  - Колонка: {col[0]}, Тип: {col[1]}")
                
                # Выводим количество записей и примеры записей
                count_query = text("SELECT COUNT(*) FROM dating_bot.admin_messages")
                count_result = await session.execute(count_query)
                count = count_result.scalar()
                logger.info(f"Количество записей в таблице admin_messages: {count}")
                
                if count > 0:
                    data_query = text("SELECT * FROM dating_bot.admin_messages LIMIT 5")
                    data_result = await session.execute(data_query)
                    data = data_result.fetchall()
                    
                    logger.info("Примеры записей:")
                    for row in data:
                        logger.info(f"  - ID: {row.id}, Город: '{row.city}', Тип: '{row.place_type}', Сообщение: '{row.message[:50]}...'")
                else:
                    logger.warning("⚠️ Таблица admin_messages пуста")
            else:
                logger.error("❌ Таблица admin_messages не существует!")
            
            # Проверяем таблицу places
            logger.info("\n--- Проверка таблицы places ---")
            
            check_places_table = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'dating_bot'
                    AND table_name = 'places'
                );
            """)
            result = await session.execute(check_places_table)
            places_table_exists = result.scalar()
            
            if places_table_exists:
                logger.info("✅ Таблица places существует")
                
                # Выводим структуру таблицы
                structure_query = text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns
                    WHERE table_schema = 'dating_bot'
                    AND table_name = 'places'
                    ORDER BY ordinal_position;
                """)
                structure_result = await session.execute(structure_query)
                columns = structure_result.fetchall()
                
                logger.info("Структура таблицы places:")
                for col in columns:
                    logger.info(f"  - Колонка: {col[0]}, Тип: {col[1]}")
                
                # Выводим количество записей и примеры записей
                count_query = text("SELECT COUNT(*) FROM dating_bot.places")
                count_result = await session.execute(count_query)
                count = count_result.scalar()
                logger.info(f"Количество записей в таблице places: {count}")
                
                if count > 0:
                    data_query = text("SELECT id, name, city, type FROM dating_bot.places LIMIT 5")
                    data_result = await session.execute(data_query)
                    data = data_result.fetchall()
                    
                    logger.info("Примеры заведений:")
                    for row in data:
                        logger.info(f"  - ID: {row.id}, Название: '{row.name}', Город: '{row.city}', Тип: '{row.type}'")
                    
                    # Выводим уникальные города
                    cities_query = text("SELECT DISTINCT city FROM dating_bot.places WHERE city IS NOT NULL")
                    cities_result = await session.execute(cities_query)
                    cities = cities_result.fetchall()
                    
                    logger.info("Уникальные города в таблице places:")
                    for city in cities:
                        logger.info(f"  - '{city.city}'")
                    
                    # Выводим уникальные типы заведений
                    types_query = text("SELECT DISTINCT type FROM dating_bot.places WHERE type IS NOT NULL")
                    types_result = await session.execute(types_query)
                    types = types_result.fetchall()
                    
                    logger.info("Уникальные типы заведений в таблице places:")
                    for place_type in types:
                        logger.info(f"  - '{place_type.type}'")
                else:
                    logger.warning("⚠️ Таблица places пуста")
            else:
                logger.error("❌ Таблица places не существует!")
                
            # Проверяем соответствие данных
            if admin_msg_table_exists and places_table_exists and count > 0:
                logger.info("\n--- Проверка соответствия данных ---")
                
                # Получаем типы заведений из places
                place_types_query = text("SELECT DISTINCT type FROM dating_bot.places WHERE type IS NOT NULL")
                place_types_result = await session.execute(place_types_query)
                place_types = [row.type for row in place_types_result.fetchall()]
                
                # Получаем города из places
                place_cities_query = text("SELECT DISTINCT city FROM dating_bot.places WHERE city IS NOT NULL")
                place_cities_result = await session.execute(place_cities_query)
                place_cities = [row.city for row in place_cities_result.fetchall()]
                
                # Получаем типы заведений из admin_messages
                admin_msg_types_query = text("SELECT DISTINCT place_type FROM dating_bot.admin_messages")
                admin_msg_types_result = await session.execute(admin_msg_types_query)
                admin_msg_types = [row.place_type for row in admin_msg_types_result.fetchall()]
                
                # Получаем города из admin_messages
                admin_msg_cities_query = text("SELECT DISTINCT city FROM dating_bot.admin_messages")
                admin_msg_cities_result = await session.execute(admin_msg_cities_query)
                admin_msg_cities = [row.city for row in admin_msg_cities_result.fetchall()]
                
                # Проверяем соответствие типов заведений
                logger.info("Типы заведений в places vs admin_messages:")
                for place_type in place_types:
                    if place_type in admin_msg_types:
                        logger.info(f"  ✅ '{place_type}' найден в обеих таблицах")
                    else:
                        logger.warning(f"  ⚠️ '{place_type}' есть в places, но нет в admin_messages")
                
                for admin_msg_type in admin_msg_types:
                    if admin_msg_type not in place_types:
                        logger.warning(f"  ⚠️ '{admin_msg_type}' есть в admin_messages, но нет в places")
                
                # Проверяем соответствие городов
                logger.info("Города в places vs admin_messages:")
                for place_city in place_cities:
                    found = False
                    for admin_msg_city in admin_msg_cities:
                        if place_city.lower() in admin_msg_city.lower() or admin_msg_city.lower() in place_city.lower():
                            logger.info(f"  ✅ '{place_city}' соответствует '{admin_msg_city}' в admin_messages")
                            found = True
                            break
                    if not found:
                        logger.warning(f"  ⚠️ '{place_city}' есть в places, но нет соответствия в admin_messages")
    
    except Exception as e:
        logger.error(f"Ошибка при проверке таблиц: {e}")
    
    logger.info("=== КОНЕЦ ДИАГНОСТИКИ ТАБЛИЦ ===")

async def test_admin_message_queries():
    """Тестирует запросы к таблице admin_messages"""
    logger.info("\n=== ТЕСТИРОВАНИЕ ЗАПРОСОВ К ADMIN_MESSAGES ===")
    
    try:
        async for session in get_session():
            # Получаем все уникальные города и типы из таблицы places
            cities_query = text("SELECT DISTINCT city FROM dating_bot.places WHERE city IS NOT NULL")
            cities_result = await session.execute(cities_query)
            cities = [row.city for row in cities_result.fetchall()]
            
            types_query = text("SELECT DISTINCT type FROM dating_bot.places WHERE type IS NOT NULL")
            types_result = await session.execute(types_query)
            place_types = [row.type for row in types_result.fetchall()]
            
            if not cities or not place_types:
                logger.warning("⚠️ Нет данных для тестирования (нет городов или типов заведений)")
                continue
            
            # Тестируем запросы к таблице admin_messages для каждой пары город-тип
            from app.booking.services_admin_message import AdminMessageService
            
            logger.info("--- Тестирование получения админских сообщений ---")
            for city in cities[:3]:  # Ограничиваем до 3 городов для краткости
                for place_type in place_types[:3]:  # Ограничиваем до 3 типов
                    logger.info(f"\nПроверка для города '{city}' и типа '{place_type}':")
                    
                    # Пробуем получить админское сообщение
                    admin_message = await AdminMessageService.get_admin_message(
                        session=session,
                        city=city,
                        place_type=place_type
                    )
                    
                    if admin_message:
                        logger.info(f"✅ Найдено админское сообщение: '{admin_message[:50]}...'")
                    else:
                        logger.warning(f"⚠️ Админское сообщение не найдено")
                        
                        # Пробуем получить сообщение только по типу
                        type_only_message = await AdminMessageService.get_admin_message(
                            session=session,
                            city="",  # Пустой город
                            place_type=place_type
                        )
                        
                        if type_only_message:
                            logger.info(f"✅ Найдено сообщение только по типу '{place_type}': '{type_only_message[:50]}...'")
    
    except Exception as e:
        logger.error(f"Ошибка при тестировании запросов: {e}")
    
    logger.info("=== КОНЕЦ ТЕСТИРОВАНИЯ ЗАПРОСОВ К ADMIN_MESSAGES ===")

async def main():
    """Основная функция диагностики"""
    logger.info("Запуск диагностики базы данных...")
    
    # Проверяем таблицы
    await check_tables()
    
    # Тестируем запросы к таблице admin_messages
    await test_admin_message_queries()
    
    logger.info("Диагностика завершена.")

if __name__ == "__main__":
    asyncio.run(main())
