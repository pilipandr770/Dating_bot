# файл: app/services/user_service.py

from app.database import get_session
from app.models.user import User
from app.models.user_photos import UserPhoto
from sqlalchemy import select
import asyncio

async def create_user_from_registration(data: dict, telegram_id: str):
    async for session in get_session():
        user = User(
            telegram_id=telegram_id,
            first_name=data.get("name"),
            age=data.get("age"),
            gender=parse_enum(data.get("gender")),
            orientation=parse_enum(data.get("orientation")),
            city=data.get("city"),
            language=data.get("language", "ua"),
            bio=data.get("bio"),
            is_verified=False
        )
        session.add(user)
        await session.flush()  # отримуємо user.id

        photos = data.get("photos", [])
        for file_id in photos[:5]:
            session.add(UserPhoto(user_id=user.id, file_id=file_id))

        await session.commit()
        return user.id

def parse_enum(raw: str) -> str:
    return raw.lower().replace("👨", "").replace("👩", "").replace("⚧", "")\
                     .replace("💞", "").replace("🌈", "").replace("🔁", "").replace("❔", "").strip()
