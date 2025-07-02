# файл: app/services/search_settings_service.py

from app.database import get_session
from app.models.search_settings import SearchSettings
from app.models.user import User
from sqlalchemy import select, update

async def get_user_search_settings(user_id: int) -> SearchSettings:
    """
    Получить настройки поиска для пользователя или создать новые, если их нет
    """
    async for session in get_session():
        try:
            # Пробуем найти существующие настройки
            settings = await session.scalar(
                select(SearchSettings).where(SearchSettings.user_id == user_id)
            )
            
            # Если настроек нет - создаем с значениями по умолчанию
            if not settings:
                settings = SearchSettings(
                    user_id=user_id,
                    min_age=18,
                    max_age=99,
                    preferred_gender=None,  # Любой пол
                    max_distance=100,
                    city_filter=False  # Не ограничиваться только своим городом
                )
                session.add(settings)
                await session.commit()
                
            return settings
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при получении настроек поиска: {e}")
            return None

async def update_search_settings(user_id=None, telegram_id=None, settings_data: dict = None) -> bool:
    """
    Обновить настройки поиска для пользователя
    
    Args:
        user_id: ID пользователя в базе
        telegram_id: Telegram ID пользователя (строка)
        settings_data: Словарь с настройками для обновления
    """
    if not settings_data:
        return False
    
    async for session in get_session():
        try:
            # Если передан telegram_id, находим user_id
            if telegram_id and not user_id:
                user = await session.scalar(
                    select(User).where(User.telegram_id == telegram_id)
                )
                if not user:
                    return False
                user_id = user.id
            
            # Проверяем, существуют ли настройки
            existing = await session.scalar(
                select(SearchSettings).where(SearchSettings.user_id == user_id)
            )
            
            if existing:
                # Обновляем существующие настройки
                for key, value in settings_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                        
                await session.commit()
                return True
            else:
                # Создаем новые настройки
                settings = SearchSettings(user_id=user_id, **settings_data)
                session.add(settings)
                await session.commit()
                return True
                
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при обновлении настроек поиска: {e}")
            return False

async def get_search_settings_by_telegram_id(telegram_id: str) -> SearchSettings:
    """
    Получить настройки поиска по Telegram ID
    """
    async for session in get_session():
        try:
            # Сначала получаем пользователя
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            
            if not user:
                return None
                
            # Затем получаем его настройки поиска
            return await get_user_search_settings(user.id)
            
        except Exception as e:
            print(f"❌ Ошибка при получении настроек поиска по Telegram ID: {e}")
            return None
