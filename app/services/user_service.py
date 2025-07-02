# файл: app/services/user_service.py

from app.database import get_session
from app.models.user import User
from app.models.user_photos import UserPhoto
from sqlalchemy import select, update, text
import asyncio

async def create_user_from_registration(data: dict, telegram_id: str):
    async for session in get_session():
        try:
            # Проверяем, существует ли пользователь
            check_sql = "SELECT id FROM dating_bot.users WHERE telegram_id = :telegram_id"
            result = await session.execute(text(check_sql), {"telegram_id": telegram_id})
            existing_user_id = result.scalar()
            
            if existing_user_id:
                # Если пользователь существует, обновляем его данные
                update_sql = """
                UPDATE dating_bot.users 
                SET first_name = :first_name, age = :age, gender = :gender, 
                    orientation = :orientation, city = :city, 
                    bio = :bio, is_verified = :is_verified
                WHERE telegram_id = :telegram_id
                RETURNING id
                """
            else:
                # Если пользователя нет, создаем нового
                update_sql = """
                INSERT INTO dating_bot.users 
                (telegram_id, first_name, age, gender, orientation, city, language, bio, is_verified)
                VALUES (:telegram_id, :first_name, :age, :gender, :orientation, :city, :language, :bio, :is_verified)
                RETURNING id
                """
            
            # Общие параметры для обоих запросов
            params = {
                "telegram_id": telegram_id,
                "first_name": data.get("name", "Anonymous"),
                "age": data.get("age"),
                "gender": parse_enum(data.get("gender")),
                "orientation": parse_enum(data.get("orientation")),
                "city": data.get("city"),
                "language": data.get("language", "ua"),
                "bio": data.get("bio"),
                "is_verified": False
            }
            
            # Выполняем запрос (INSERT или UPDATE)
            result = await session.execute(text(update_sql), params)
            user_id = result.scalar()
            
            # Зберігаємо фото
            photos = data.get("photos", [])
            for file_id in photos[:5]:
                photo_sql = """
                INSERT INTO dating_bot.user_photos (user_id, file_id)
                VALUES (:user_id, :file_id)
                """
                await session.execute(text(photo_sql), {"user_id": user_id, "file_id": file_id})

            await session.commit()
            return user_id
        except Exception as e:
            await session.rollback()
            print(f"❌ Виникла помилка при збереженні анкети: {e}")
            return None

def parse_enum(raw: str) -> str:
    if not raw:
        return None
    return raw.lower().replace("👨", "").replace("👩", "").replace("⚧", "")\
                     .replace("💞", "").replace("🌈", "").replace("🔁", "").replace("❔", "").strip()

async def create_or_get_user(telegram_id: str) -> User:
    """
    Створює або повертає користувача за Telegram ID
    """
    async for session in get_session():
        try:
            # Шукаємо користувача використовуючи SQL
            sql = "SELECT * FROM dating_bot.users WHERE telegram_id = :telegram_id"
            result = await session.execute(text(sql), {"telegram_id": telegram_id})
            user_row = result.fetchone()
            
            # Якщо не знайдено — створюємо
            if not user_row:
                insert_sql = """
                INSERT INTO dating_bot.users (telegram_id, first_name)
                VALUES (:telegram_id, :first_name)
                RETURNING *
                """
                result = await session.execute(
                    text(insert_sql), 
                    {"telegram_id": telegram_id, "first_name": "Anonymous"}
                )
                await session.commit()
                user_row = result.fetchone()
            
            # Перетворюємо рядок з БД на об'єкт User
            if user_row:
                user = User()
                for key in User.__table__.columns.keys():
                    if key in user_row._mapping:
                        setattr(user, key, user_row._mapping[key])
                return user
            
            return None
        except Exception as e:
            await session.rollback()
            print(f"❌ Помилка при створенні/отриманні користувача: {e}")
            return None

async def update_user_field(user_id: str, field: str, value: any) -> bool:
    """
    Оновлює одне поле користувача за Telegram ID
    """
    async for session in get_session():
        try:
            # Особлива обробка для поля language
            if field == "language":
                # Виконуємо безпосередній SQL запит
                await session.execute(
                    text("UPDATE dating_bot.users SET language = :lang WHERE telegram_id = :user_id"),
                    {"lang": value, "user_id": user_id}
                )
            # Особлива обробка для полів gender та orientation
            elif field in ["gender", "orientation"]:
                # Обробляємо, щоб зберігати тільки текстове значення
                clean_value = parse_enum(value)
                query = (
                    update(User)
                    .where(User.telegram_id == user_id)
                    .values(**{field: clean_value})
                )
                await session.execute(query)
            else:
                query = (
                    update(User)
                    .where(User.telegram_id == user_id)
                    .values(**{field: value})
                )
                await session.execute(query)
            
            await session.commit()
            return True
        except Exception as e:
            print(f"Помилка при оновленні поля {field}: {e}")
            await session.rollback()
            return False
        
    return False

async def get_user_language(telegram_id: str) -> str:
    """
    Повертає мову користувача
    """
    async for session in get_session():
        try:
            result = await session.execute(
                text("SELECT language FROM dating_bot.users WHERE telegram_id = :telegram_id"),
                {"telegram_id": telegram_id}
            )
            language = result.scalar()
            return language or "ua"  # За замовчуванням українська
        except Exception as e:
            print(f"❌ Помилка при отриманні мови користувача: {e}")
            return "ua"  # За замовчуванням українська

async def save_user_photos(telegram_id: str, photo_file_ids: list) -> bool:
    """
    Сохраняет фотографии пользователя в базу данных
    """
    if not photo_file_ids:
        return True  # Нет фото для сохранения
        
    async for session in get_session():
        try:
            # Находим пользователя
            sql = "SELECT id FROM dating_bot.users WHERE telegram_id = :telegram_id"
            result = await session.execute(text(sql), {"telegram_id": telegram_id})
            user_id = result.scalar()
            
            if not user_id:
                print(f"❌ Пользователь с telegram_id {telegram_id} не найден")
                return False
                
            # Удаляем старые фотографии
            delete_sql = "DELETE FROM dating_bot.user_photos WHERE user_id = :user_id"
            await session.execute(text(delete_sql), {"user_id": user_id})
            
            # Добавляем новые фотографии
            for file_id in photo_file_ids[:5]:  # Максимум 5 фото
                insert_sql = """
                INSERT INTO dating_bot.user_photos (user_id, file_id)
                VALUES (:user_id, :file_id)
                """
                await session.execute(text(insert_sql), {"user_id": user_id, "file_id": file_id})
                
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при сохранении фотографий: {e}")
            return False

async def get_user_by_telegram_id(telegram_id: str) -> User:
    """
    Получает пользователя по его Telegram ID
    
    Args:
        telegram_id: Telegram ID пользователя
    
    Returns:
        User: Объект пользователя или None, если не найден
    """
    async for session in get_session():
        try:
            # Ищем пользователя через SQLAlchemy
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            return user
            
        except Exception as e:
            print(f"❌ Ошибка при получении пользователя по Telegram ID: {e}")
            return None

async def get_user_photos(user_id: int):
    """
    Получает список file_id фотографий пользователя по его ID
    """
    photo_file_ids = []
    print(f"📸 Запрос фотографий для пользователя с ID {user_id}")
    
    async for session in get_session():
        try:
            # Используем более простой запрос без сортировки по uploaded_at
            sql = """
            SELECT file_id FROM dating_bot.user_photos 
            WHERE user_id = :user_id
            """
            result = await session.execute(text(sql), {"user_id": user_id})
            rows = result.fetchall()
            
            for row in rows:
                photo_file_ids.append(row[0])
            
            print(f"📸 Найдено {len(photo_file_ids)} фотографий для пользователя с ID {user_id}: {photo_file_ids}")
            return photo_file_ids
        except Exception as e:
            print(f"❌ Ошибка при получении фотографий пользователя: {e}")
            return []
