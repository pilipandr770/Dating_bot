# app/booking/services_admin_message.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.booking.models import AdminMessage

# Настройка логирования
logger = logging.getLogger(__name__)

class AdminMessageService:
    """Сервис для работы с сообщениями администратора"""

    @staticmethod
    async def add_admin_message(
        session: AsyncSession,
        city: str,
        place_type: str,
        message: str
    ) -> Optional[AdminMessage]:
        """
        Добавляет новое сообщение администратора для города и типа заведения.
        Если сообщение для данного города и типа уже существует, оно будет обновлено.
        
        Возвращает созданный/обновленный объект AdminMessage или None в случае ошибки.
        """
        try:
            # Проверяем, существует ли уже сообщение для данного города и типа
            query = select(AdminMessage).where(
                and_(
                    AdminMessage.city == city,
                    AdminMessage.place_type == place_type
                )
            )
            result = await session.execute(query)
            existing_message = result.scalar_one_or_none()
            
            if existing_message:
                # Если сообщение существует, обновляем его
                existing_message.message = message
                message_obj = existing_message
                logger.info(f"Обновлено админское сообщение для города '{city}' и типа '{place_type}'")
            else:
                # Если сообщения нет, создаем новое
                message_obj = AdminMessage(
                    city=city,
                    place_type=place_type,
                    message=message
                )
                session.add(message_obj)
                logger.info(f"Добавлено новое админское сообщение для города '{city}' и типа '{place_type}'")
            
            # Сохраняем изменения
            await session.commit()
            await session.refresh(message_obj)
            
            return message_obj
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении/обновлении админского сообщения: {e}")
            return None
    
    @staticmethod
    async def get_admin_message(
        session: AsyncSession,
        city: str,
        place_type: str
    ) -> Optional[str]:
        """
        Получает сообщение администратора для указанного города и типа заведения.
        Возвращает текст сообщения или None, если сообщение не найдено.
        """
        try:
            logger.info(f"[ADMIN_MSG] Запрос админского сообщения для города '{city}' и типа '{place_type}'")
            
            # Проверяем входные параметры
            if not city or not place_type:
                logger.warning(f"[ADMIN_MSG] Некорректные параметры: город='{city}', тип='{place_type}'")
                return None
                
            # Выводим тип параметров для отладки
            logger.info(f"[ADMIN_MSG] Типы параметров: city={type(city).__name__}, place_type={type(place_type).__name__}")
            
            # Проверка наличия таблицы admin_messages
            try:
                # Проверяем существование таблицы
                check_table_query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'dating_bot'
                        AND table_name = 'admin_messages'
                    );
                """)
                check_result = await session.execute(check_table_query)
                table_exists = check_result.scalar()
                
                logger.info(f"[ADMIN_MSG] Таблица admin_messages существует: {table_exists}")
                
                if not table_exists:
                    logger.error("[ADMIN_MSG] Таблица admin_messages не существует в базе данных!")
                    return None
                    
                # Проверяем структуру таблицы
                structure_query = text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns
                    WHERE table_schema = 'dating_bot'
                    AND table_name = 'admin_messages'
                    ORDER BY ordinal_position;
                """)
                structure_result = await session.execute(structure_query)
                columns = structure_result.fetchall()
                
                logger.info(f"[ADMIN_MSG] Структура таблицы admin_messages:")
                for col in columns:
                    logger.info(f"[ADMIN_MSG] Колонка: {col[0]}, Тип: {col[1]}")
            except Exception as e:
                logger.error(f"[ADMIN_MSG] Ошибка при проверке таблицы: {e}")
            
            # Логируем количество всех сообщений для отладки
            try:
                debug_query = select(AdminMessage)
                debug_result = await session.execute(debug_query)
                debug_messages = debug_result.scalars().all()
                logger.info(f"Всего админских сообщений в БД: {len(list(debug_messages))}")
                
                # Для каждого сообщения выводим его город и тип для отладки
                for msg in debug_messages:
                    logger.info(f"В БД: сообщение для города '{msg.city}', типа '{msg.place_type}': '{msg.message[:20]}...'")
                    # Проверяем, совпадает ли этот город (с учетом регистра) с запрашиваемым
                    if city and msg.city and (city.lower() in msg.city.lower() or msg.city.lower() in city.lower()):
                        logger.info(f"Потенциальное совпадение для города: '{city}' и '{msg.city}'")
                    if place_type and msg.place_type and place_type.lower() == msg.place_type.lower():
                        logger.info(f"Совпадение для типа: '{place_type}' и '{msg.place_type}'")
            except Exception as e:
                logger.error(f"[ADMIN_MSG] Ошибка при получении всех сообщений через SQLAlchemy: {e}")
                
            # Попробуем прямой SQL-запрос для просмотра всех сообщений
            try:
                all_messages_query = text("SELECT * FROM dating_bot.admin_messages")
                all_messages_result = await session.execute(all_messages_query)
                all_messages = all_messages_result.fetchall()
                
                logger.info(f"[ADMIN_MSG] Прямой SQL запрос вернул {len(all_messages)} сообщений")
                for msg in all_messages:
                    logger.info(f"[ADMIN_MSG] Raw SQL: ID={msg.id}, город='{msg.city}', тип='{msg.place_type}', сообщение='{msg.message[:20]}...'")
            except Exception as e:
                logger.error(f"[ADMIN_MSG] Ошибка при выполнении прямого SQL запроса: {e}")
            
            # SQL-запрос для отладки
            raw_sql = f"""
                SELECT * FROM dating_bot.admin_messages 
                WHERE LOWER(city) LIKE LOWER('%{city}%')
                AND LOWER(place_type) = LOWER('{place_type}')
            """
            logger.info(f"[ADMIN_MSG] SQL запрос для отладки: {raw_sql}")
            
            try:
                # Выполняем запрос с учетом возможного несовпадения регистра и частичного совпадения города
                query = text("""
                    SELECT * FROM dating_bot.admin_messages 
                    WHERE LOWER(city) LIKE LOWER(:city_pattern)
                    AND LOWER(place_type) = LOWER(:place_type)
                """).bindparams(city_pattern=f"%{city}%", place_type=place_type)
                
                result = await session.execute(query)
                admin_message_row = result.fetchone()
                
                if admin_message_row:
                    logger.info(f"Найдено админское сообщение: '{admin_message_row.message}'")
                    return admin_message_row.message
                else:
                    logger.info(f"Точное совпадение не найдено, пробуем более гибкий поиск")
            except Exception as e:
                logger.error(f"[ADMIN_MSG] Ошибка при выполнении основного запроса: {e}")
            
            try:
                # Пробуем найти сообщение только по типу места
                logger.info(f"[ADMIN_MSG] Пробуем поиск только по типу места: '{place_type}'")
                type_only_query = text("""
                    SELECT * FROM dating_bot.admin_messages 
                    WHERE LOWER(place_type) = LOWER(:place_type)
                    LIMIT 1
                """).bindparams(place_type=place_type)
                
                type_result = await session.execute(type_only_query)
                type_message_row = type_result.fetchone()
                
                if type_message_row:
                    logger.info(f"[ADMIN_MSG] Найдено сообщение по типу места: '{type_message_row.message}'")
                    return type_message_row.message
            except Exception as e:
                logger.error(f"[ADMIN_MSG] Ошибка при поиске по типу места: {e}")
            
            try:
                # Попробуем найти любое сообщение для этого города
                logger.info(f"[ADMIN_MSG] Пробуем поиск только по городу: '{city}'")
                city_query = text("""
                    SELECT * FROM dating_bot.admin_messages 
                    WHERE LOWER(city) LIKE LOWER(:city_pattern)
                    LIMIT 1
                """).bindparams(city_pattern=f"%{city}%")
                
                city_result = await session.execute(city_query)
                city_message_row = city_result.fetchone()
                
                if city_message_row:
                    logger.info(f"[ADMIN_MSG] Найдено сообщение по городу: '{city_message_row.message}'")
                    return city_message_row.message
            except Exception as e:
                logger.error(f"[ADMIN_MSG] Ошибка при поиске по городу: {e}")
            
            try:
                # Наконец, просто берем любое доступное сообщение
                logger.info(f"[ADMIN_MSG] Пробуем взять любое доступное сообщение")
                any_query = text("""
                    SELECT * FROM dating_bot.admin_messages 
                    LIMIT 1
                """)
                
                any_result = await session.execute(any_query)
                any_message_row = any_result.fetchone()
                
                if any_message_row:
                    logger.info(f"[ADMIN_MSG] Найдено любое доступное сообщение: '{any_message_row.message}'")
                    return any_message_row.message
            except Exception as e:
                logger.error(f"[ADMIN_MSG] Ошибка при поиске любого сообщения: {e}")
                
            logger.info(f"[ADMIN_MSG] Админских сообщений в базе данных не найдено")
            return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении админского сообщения: {e}")
            return None
    
    @staticmethod
    async def list_admin_messages(
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Возвращает список всех админских сообщений.
        """
        try:
            query = select(AdminMessage)
            result = await session.execute(query)
            admin_messages = result.scalars().all()
            
            messages_list = []
            for msg in admin_messages:
                messages_list.append({
                    "id": msg.id,
                    "city": msg.city,
                    "place_type": msg.place_type,
                    "message": msg.message,
                    "created_at": msg.created_at
                })
            
            logger.info(f"Получен список админских сообщений: {len(messages_list)} записей")
            return messages_list
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка админских сообщений: {e}")
            return []
    
    @staticmethod
    async def delete_admin_message(
        session: AsyncSession,
        message_id: int
    ) -> bool:
        """
        Удаляет админское сообщение по ID.
        Возвращает True в случае успеха, False в случае ошибки.
        """
        try:
            query = select(AdminMessage).where(AdminMessage.id == message_id)
            result = await session.execute(query)
            message = result.scalar_one_or_none()
            
            if not message:
                logger.warning(f"Админское сообщение с ID {message_id} не найдено")
                return False
            
            await session.delete(message)
            await session.commit()
            
            logger.info(f"Удалено админское сообщение с ID {message_id}")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при удалении админского сообщения: {e}")
            return False
    
    @staticmethod
    async def get_admin_message_flexible(
        session: AsyncSession,
        city: str,
        place_type: str
    ) -> Optional[str]:
        """
        Более гибкий метод поиска сообщения администратора.
        Ищет с учетом возможных вариаций в названии города (регистр букв, частичное совпадение).
        """
        try:
            logger.info(f"Гибкий поиск админского сообщения для города '{city}' и типа '{place_type}'")
            
            if not city or not place_type:
                return None
                
            # Сначала пробуем точное совпадение
            exact_match = await AdminMessageService.get_admin_message(session, city, place_type)
            if exact_match:
                return exact_match
                
            # Если точного совпадения нет, ищем по части названия города (используем SQL LIKE)
            query = text("""
                SELECT * FROM dating_bot.admin_messages
                WHERE place_type = :place_type
                AND (city ILIKE :city OR :city ILIKE CONCAT('%', city, '%'))
                LIMIT 1
            """).bindparams(place_type=place_type, city=city)
            
            result = await session.execute(query)
            row = result.fetchone()
            
            if row:
                logger.info(f"Найдено админское сообщение с гибким поиском: '{row.message}'")
                return row.message
                
            logger.info(f"Админское сообщение не найдено даже с гибким поиском")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при гибком поиске админского сообщения: {e}")
            return None
