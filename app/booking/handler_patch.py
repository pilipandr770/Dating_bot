# app/booking/handler_patch.py

import asyncio
import logging
import sys
import os
from sqlalchemy import text

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("HANDLER_PATCH")

async def patch_new_handler_file():
    """
    Create an optimized version of the critical admin message section in new_handlers.py
    """
    try:
        # Define the path to the original file
        original_file = os.path.join(os.path.dirname(__file__), "new_handlers.py")
        
        # Check if the file exists
        if not os.path.exists(original_file):
            logger.error(f"File not found: {original_file}")
            return False
            
        # Create a backup of the original file
        backup_file = original_file + ".bak"
        with open(original_file, 'r', encoding='utf-8') as src:
            with open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        logger.info(f"Created backup of original file: {backup_file}")
        
        # Read the original file content
        with open(original_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Define the sections to be replaced
        old_admin_message_section = """        # Пробуем получить сообщение администратора для этого города и типа заведения
        admin_message = None
        try:
            logger.info(f"[NEW] Запрашиваем сообщение админа для города '{city}' и типа '{place_type}'")
            from app.booking.services_admin_message import AdminMessageService
            
            async for session in get_session():
                # Выводим все доступные сообщения для отладки
                try:
                    admin_messages = await AdminMessageService.list_admin_messages(session)
                    logger.info(f"[NEW] Доступные админские сообщения: {len(admin_messages)}")
                    for msg in admin_messages:
                        logger.info(f"[NEW] Доступное сообщение: город='{msg.get('city')}', тип='{msg.get('place_type')}', текст='{msg.get('message')[:30] if msg.get('message') else 'None'}...'")
                except Exception as list_error:
                    logger.error(f"[NEW] Ошибка при получении списка админских сообщений: {list_error}")
                
                # Проверяем и нормализуем параметры
                city_value = city if city else "Unknown"
                if not isinstance(city_value, str):
                    city_value = str(city_value)
                
                place_type_value = place_type
                if not isinstance(place_type_value, str):
                    place_type_value = str(place_type_value)
                
                logger.info(f"[NEW] Используем нормализованные параметры: город='{city_value}' (тип: {type(city_value).__name__}), тип места='{place_type_value}' (тип: {type(place_type_value).__name__})")
                
                # Запрашиваем конкретное сообщение
                try:
                    # Сначала проверяем, что таблица существует
                    check_table_query = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'dating_bot' AND table_name = 'admin_messages');")
                    check_result = await session.execute(check_table_query)
                    table_exists = check_result.scalar()
                    logger.info(f"[NEW] Таблица admin_messages существует: {table_exists}")
                    
                    if not table_exists:
                        logger.error("[NEW] Таблица admin_messages не существует!")
                        continue
                    
                    # Теперь запрашиваем сообщение
                    admin_message = await AdminMessageService.get_admin_message(session, city_value, place_type_value)
                    
                    if admin_message:
                        logger.info(f"[NEW] Найдено сообщение администратора для города '{city_value}' и типа '{place_type_value}': '{admin_message}'")
                    else:
                        logger.info(f"[NEW] Не найдено сообщение администратора для города '{city_value}' и типа '{place_type_value}'")
                        
                        # Пробуем напрямую запросить из БД
                        direct_query = text("""SELECT message FROM dating_bot.admin_messages 
                            WHERE LOWER(city) LIKE LOWER(:city_pattern) 
                            AND LOWER(place_type) = LOWER(:place_type) 
                            LIMIT 1""").bindparams(city_pattern=f"%{city_value}%", place_type=place_type_value)
                        
                        try:
                            direct_result = await session.execute(direct_query)
                            direct_row = direct_result.fetchone()
                            if direct_row:
                                admin_message = direct_row[0]
                                logger.info(f"[NEW] Найдено сообщение администратора через прямой SQL: '{admin_message}'")
                        except Exception as direct_query_error:
                            logger.error(f"[NEW] Ошибка при прямом запросе к БД: {direct_query_error}")
                except Exception as get_msg_error:
                    logger.error(f"[NEW] Ошибка при запросе админского сообщения: {get_msg_error}")
        except Exception as admin_msg_error:
            logger.error(f"[NEW] Общая ошибка при получении сообщения администратора: {admin_msg_error}")
            logger.error(f"[NEW] Полный стек ошибки:\\n{traceback.format_exc()}")
            """
            
        new_admin_message_section = """        # Пробуем получить сообщение администратора для этого города и типа заведения
        admin_message = None
        try:
            logger.info(f"[NEW] Запрашиваем сообщение админа для города '{city}' и типа '{place_type}'")
            from app.booking.services_admin_message import AdminMessageService
            
            async for session in get_session():
                # Проверяем и нормализуем параметры
                city_value = city if city else "Unknown"
                if not isinstance(city_value, str):
                    city_value = str(city_value)
                
                place_type_value = place_type
                if not isinstance(place_type_value, str):
                    place_type_value = str(place_type_value)
                
                logger.info(f"[NEW] Используем нормализованные параметры: город='{city_value}', тип места='{place_type_value}'")
                
                # Используем улучшенную гибкую версию для получения сообщения с запасными вариантами
                try:
                    admin_message = await AdminMessageService.get_admin_message_flexible(session, city_value, place_type_value)
                    if admin_message:
                        logger.info(f"[NEW] Найдено сообщение администратора: '{admin_message[:100]}...'")
                    else:
                        logger.info(f"[NEW] Не найдено сообщение администратора для города '{city_value}' и типа '{place_type_value}'")
                except Exception as get_msg_error:
                    logger.error(f"[NEW] Ошибка при запросе админского сообщения: {get_msg_error}")
        except Exception as admin_msg_error:
            logger.error(f"[NEW] Общая ошибка при получении сообщения администратора: {admin_msg_error}")
            logger.error(f"[NEW] Полный стек ошибки:\\n{traceback.format_exc()}")
            """
        
        # Also improve the adding of admin message to the response
        old_admin_message_addition = """            # Если есть сообщение админа, добавляем его
            if admin_message and isinstance(admin_message, str) and admin_message.strip():
                logger.info(f"[NEW] Добавляем админское сообщение к 'скоро будет доступно': {admin_message[:30]}...")
                message_text += f"\\n\\nℹ️ {admin_message}"
            else:
                logger.info(f"[NEW] Админское сообщение отсутствует или некорректно, не добавляем его к 'скоро будет доступно'")
                logger.info(f"[NEW] Значение admin_message: {admin_message}, тип: {type(admin_message).__name__}")"""
                
        new_admin_message_addition = """            # Если есть сообщение админа, добавляем его
            if admin_message and isinstance(admin_message, str) and admin_message.strip():
                logger.info(f"[NEW] Добавляем админское сообщение к 'скоро будет доступно': {admin_message[:30]}...")
                message_text += f"\\n\\nℹ️ {admin_message}"
                # Печатаем полный текст для отладки
                logger.info(f"[NEW] Полный текст сообщения с админским сообщением:\\n{message_text}")
            else:
                logger.info(f"[NEW] Админское сообщение отсутствует или некорректно, не добавляем его")
                logger.info(f"[NEW] Значение admin_message: {admin_message}, тип: {type(admin_message).__name__ if admin_message is not None else 'None'}")"""

        # Replace the sections in the content
        updated_content = content.replace(old_admin_message_section, new_admin_message_section)
        updated_content = updated_content.replace(old_admin_message_addition, new_admin_message_addition)
        
        # Write the updated content back to the file
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        logger.info(f"Successfully updated {original_file}")
        logger.info("The handler file has been optimized for better admin message handling")
        
        return True
    except Exception as e:
        logger.error(f"Error patching handler file: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(patch_new_handler_file())
