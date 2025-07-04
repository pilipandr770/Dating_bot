# cinema/services.py

import httpx
import os
import logging
from app.models import User  # твоя таблиця користувачів
from app.database import SessionLocal
from app.cinema.models import FilmPurchase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import uuid4

# Настройка логирования
logger = logging.getLogger(__name__)

HYPERBEAM_API_KEY = os.getenv("HYPERBEAM_API_KEY")
if not HYPERBEAM_API_KEY:
    logger.error("⚠️ HYPERBEAM_API_KEY не найден в переменных окружения")

FILM_LINKS = {
    "inception": "https://www.netflix.com/watch/70131314",
    "interstellar": "https://www.netflix.com/watch/70305903",
    "wolf": "https://www.netflix.com/watch/70266676",
}

async def deduct_tokens(user_id: int, amount: int, session: AsyncSession):
    try:
        logger.info(f"Списание {amount} токенов у пользователя {user_id}")
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"⚠️ Пользователь с ID {user_id} не найден")
            return False
            
        if user.token_balance >= amount:
            user.token_balance -= amount
            logger.info(f"✅ Списано {amount} токенов, остаток: {user.token_balance}")
            return True
        else:
            logger.warning(f"⚠️ Недостаточно токенов: имеется {user.token_balance}, требуется {amount}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при списании токенов: {str(e)}")
        return False

async def create_hyperbeam_room(start_url: str) -> str:
    try:
        logger.info(f"Создание комнаты Hyperbeam для URL: {start_url}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://engine.hyperbeam.com/v0/vm",
                headers={"Authorization": f"Bearer {HYPERBEAM_API_KEY}"},
                json={"url": start_url}
            )
            response.raise_for_status()
            room_url = response.json().get("url")
            if room_url:
                logger.info(f"✅ Комната Hyperbeam создана успешно")
                return room_url
            else:
                logger.error(f"❌ API Hyperbeam вернул ответ без URL комнаты: {response.text}")
                return None
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Ошибка HTTP при создании комнаты Hyperbeam: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при создании комнаты Hyperbeam: {str(e)}")
        return None

async def process_film_purchase(user_id: int, film_id: str, film_title: str) -> str:
    logger.info(f"Обработка покупки фильма: user_id={user_id}, film_id={film_id}")
    
    # Проверка наличия фильма
    start_url = FILM_LINKS.get(film_id)
    if not start_url:
        logger.error(f"❌ Фильм с ID '{film_id}' не найден в базе")
        return None
        
    try:
        async with SessionLocal() as session:
            async with session.begin():
                # Списание токенов
                if not await deduct_tokens(user_id, 15, session):
                    logger.warning(f"⚠️ Недостаточно токенов у пользователя {user_id}")
                    return None
                    
                # Создание комнаты просмотра
                room_url = await create_hyperbeam_room(start_url)
                if not room_url:
                    logger.error(f"❌ Не удалось создать комнату Hyperbeam")
                    # Возвращаем токены пользователю
                    result = await session.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    if user:
                        user.token_balance += 15
                        logger.info(f"✅ Возвращено 15 токенов пользователю {user_id}")
                    return None
                
                # Сохраняем запись о покупке
                session.add(FilmPurchase(
                    user_id=user_id,
                    film_id=film_id,
                    film_title=film_title,
                    room_url=room_url
                ))
                logger.info(f"✅ Запись о покупке фильма создана")
                
            await session.commit()
            logger.info(f"✅ Транзакция успешно завершена")
            return room_url
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке покупки фильма: {str(e)}")
        return None
        return room_url
