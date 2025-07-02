# файл: app/services/block_service.py

from app.database import get_session
from app.models.blocked_users import BlockedUser
from app.models.user import User
from sqlalchemy import select, delete, text
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def block_user(blocker_telegram_id: str, blocked_user_id: int, reason: str = None) -> bool:
    """
    Блокирует пользователя по его ID
    
    Args:
        blocker_telegram_id: Telegram ID пользователя, который блокирует
        blocked_user_id: ID пользователя в БД, которого блокируют
        reason: Причина блокировки (опционально)
    
    Returns:
        bool: True если блокировка успешна, False в случае ошибки
    """
    try:
        async for session in get_session():
            # Получаем ID блокирующего пользователя
            blocker = await session.scalar(
                select(User).where(User.telegram_id == blocker_telegram_id)
            )
            
            if not blocker:
                logger.error(f"Пользователь с telegram_id {blocker_telegram_id} не найден")
                return False
                
            # Проверяем, существует ли блокируемый пользователь
            blocked_exists = await session.scalar(
                select(User).where(User.id == blocked_user_id)
            )
            
            if not blocked_exists:
                logger.error(f"Пользователь с ID {blocked_user_id} не найден")
                return False
            
            # Проверяем, не пытается ли пользователь заблокировать сам себя
            if blocker.id == blocked_user_id:
                logger.error(f"Пользователь пытается заблокировать сам себя")
                return False
            
            # Проверяем, не заблокирован ли пользователь уже
            existing_block = await session.scalar(
                select(BlockedUser).where(
                    BlockedUser.blocker_id == blocker.id,
                    BlockedUser.blocked_id == blocked_user_id
                )
            )
            
            if existing_block:
                logger.info(f"Пользователь {blocked_user_id} уже заблокирован")
                return True  # Считаем это успешным результатом
            
            # Создаем запись о блокировке
            block = BlockedUser(
                blocker_id=blocker.id,
                blocked_id=blocked_user_id,
                reason=reason
            )
            
            session.add(block)
            await session.commit()
            
            logger.info(f"Пользователь {blocker.id} заблокировал пользователя {blocked_user_id}")
            return True
    except Exception as e:
        logger.error(f"Ошибка при блокировке пользователя: {e}")
        return False

async def unblock_user(blocker_telegram_id: str, blocked_user_id: int) -> bool:
    """
    Разблокирует пользователя
    
    Args:
        blocker_telegram_id: Telegram ID пользователя, который разблокирует
        blocked_user_id: ID пользователя в БД, которого разблокируют
    
    Returns:
        bool: True если разблокировка успешна, False в случае ошибки
    """
    try:
        async for session in get_session():
            # Получаем ID разблокирующего пользователя
            blocker = await session.scalar(
                select(User).where(User.telegram_id == blocker_telegram_id)
            )
            
            if not blocker:
                logger.error(f"Пользователь с telegram_id {blocker_telegram_id} не найден")
                return False
            
            # Удаляем запись о блокировке
            stmt = delete(BlockedUser).where(
                BlockedUser.blocker_id == blocker.id,
                BlockedUser.blocked_id == blocked_user_id
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Пользователь {blocker.id} разблокировал пользователя {blocked_user_id}")
                return True
            else:
                logger.info(f"Запись о блокировке не найдена")
                return False
    except Exception as e:
        logger.error(f"Ошибка при разблокировке пользователя: {e}")
        return False

async def is_user_blocked(user_id: int, by_user_id: int) -> bool:
    """
    Проверяет, заблокирован ли пользователь
    
    Args:
        user_id: ID пользователя, которого проверяют
        by_user_id: ID пользователя, который мог заблокировать
    
    Returns:
        bool: True если пользователь заблокирован, False если нет
    """
    try:
        async for session in get_session():
            # Проверяем наличие записи о блокировке
            block = await session.scalar(
                select(BlockedUser).where(
                    BlockedUser.blocker_id == by_user_id,
                    BlockedUser.blocked_id == user_id
                )
            )
            
            return block is not None
    except Exception as e:
        logger.error(f"Ошибка при проверке блокировки пользователя: {e}")
        return False

async def get_blocked_users(telegram_id: str):
    """
    Получает список заблокированных пользователей
    
    Args:
        telegram_id: Telegram ID пользователя
    
    Returns:
        list: Список заблокированных пользователей
    """
    blocked_users = []
    
    try:
        async for session in get_session():
            # Получаем ID пользователя
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            
            if not user:
                logger.error(f"Пользователь с telegram_id {telegram_id} не найден")
                return []
            
            # SQL запрос для получения информации о заблокированных пользователях
            sql = """
            SELECT u.id, u.first_name, u.age, b.reason, b.created_at
            FROM dating_bot.blocked_users b
            JOIN dating_bot.users u ON b.blocked_id = u.id
            WHERE b.blocker_id = :blocker_id
            ORDER BY b.created_at DESC
            """
            
            result = await session.execute(text(sql), {"blocker_id": user.id})
            rows = result.fetchall()
            
            for row in rows:
                blocked_users.append({
                    "id": row[0],
                    "name": row[1],
                    "age": row[2],
                    "reason": row[3],
                    "blocked_at": row[4]
                })
            
            return blocked_users
    except Exception as e:
        logger.error(f"Ошибка при получении списка заблокированных пользователей: {e}")
        return []
