# app/booking/admin_message_service.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.booking.models import AdminMessage

# Настройка логирования
logger = logging.getLogger(__name__)

class AdminMessageService:
    """Сервис для работы с сообщениями админа в базе данных"""

    @staticmethod
    async def add_admin_message(
        session: AsyncSession,
        city: str,
        place_type: str,
        message: str
    ) -> Optional[AdminMessage]:
        """
        Добавляет новое сообщение админа в базу данных или обновляет существующее
        для указанного города и типа заведения.
        """
        try:
            # Проверяем, есть ли уже сообщение для этого города и типа
            query = select(AdminMessage).where(
                and_(
                    AdminMessage.city == city,
                    AdminMessage.place_type == place_type
                )
            )
            result = await session.execute(query)
            existing_message = result.scalar_one_or_none()
            
            if existing_message:
                # Если сообщение уже существует - обновляем его
                existing_message.message = message
                await session.commit()
                logger.info(f"Обновлено сообщение админа для {city} и типа {place_type}")
                return existing_message
            else:
                # Если сообщения нет - создаем новое
                new_message = AdminMessage(
                    city=city,
                    place_type=place_type,
                    message=message
                )
                session.add(new_message)
                await session.commit()
                await session.refresh(new_message)
                logger.info(f"Добавлено новое сообщение админа для {city} и типа {place_type}")
                return new_message
                
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении/обновлении сообщения админа: {e}")
            return None
    
    @staticmethod
    async def get_admin_message(
        session: AsyncSession,
        city: str,
        place_type: str
    ) -> Optional[str]:
        """
        Получает сообщение админа для указанного города и типа заведения.
        Возвращает текст сообщения или None, если сообщение не найдено.
        """
        try:
            query = select(AdminMessage).where(
                and_(
                    AdminMessage.city == city,
                    AdminMessage.place_type == place_type
                )
            )
            result = await session.execute(query)
            message_obj = result.scalar_one_or_none()
            
            if message_obj:
                return message_obj.message
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении сообщения админа: {e}")
            return None
    
    @staticmethod
    async def delete_admin_message(
        session: AsyncSession,
        city: str,
        place_type: str
    ) -> bool:
        """
        Удаляет сообщение админа для указанного города и типа заведения.
        Возвращает True в случае успеха, False в случае ошибки.
        """
        try:
            query = select(AdminMessage).where(
                and_(
                    AdminMessage.city == city,
                    AdminMessage.place_type == place_type
                )
            )
            result = await session.execute(query)
            message_obj = result.scalar_one_or_none()
            
            if message_obj:
                await session.delete(message_obj)
                await session.commit()
                logger.info(f"Удалено сообщение админа для {city} и типа {place_type}")
                return True
            
            logger.warning(f"Попытка удалить несуществующее сообщение для {city} и типа {place_type}")
            return False
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при удалении сообщения админа: {e}")
            return False
    
    @staticmethod
    async def get_all_admin_messages(
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Получает список всех сообщений админа.
        Возвращает список словарей с полями city, place_type, message.
        """
        try:
            query = select(AdminMessage)
            result = await session.execute(query)
            messages = result.scalars().all()
            
            return [
                {
                    "id": msg.id,
                    "city": msg.city,
                    "place_type": msg.place_type,
                    "message": msg.message,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка сообщений админа: {e}")
            return []
