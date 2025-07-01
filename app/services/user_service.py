# файл: app/services/user_service.py

from app.database import get_session
from app.models.user import User
from app.models.user_photos import UserPhoto
from sqlalchemy import select, update, text
import asyncio

async def create_user_from_registration(data: dict, telegram_id: str):
    async for session in get_session():
        try:
            # Використовуємо raw SQL замість ORM, щоб уникнути проблем з колонками
            # Вставляємо тільки ті поля, які точно існують у таблиці
            sql = """
            INSERT INTO dating_bot.users 
            (telegram_id, first_name, age, gender, orientation, city, language, bio, is_verified)
            VALUES (:telegram_id, :first_name, :age, :gender, :orientation, :city, :language, :bio, :is_verified)
            RETURNING id
            """
            
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
            
            result = await session.execute(text(sql), params)
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

async def save_user_photos(telegram_id: str, file_ids: list) -> bool:
    """
    Зберігає фото користувача в базу даних
    """
    async for session in get_session():
        try:
            # Спочатку отримуємо ID користувача
            result = await session.execute(
                select(User.id).filter(User.telegram_id == telegram_id)
            )
            user_id = result.scalar()
            
            if not user_id:
                print(f"❌ Користувача з telegram_id={telegram_id} не знайдено")
                return False
            
            # Видаляємо старі фотографії користувача (якщо є)
            await session.execute(
                text("DELETE FROM dating_bot.user_photos WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            
            # Додаємо нові фотографії
            for file_id in file_ids:
                user_photo = UserPhoto(user_id=user_id, file_id=file_id)
                session.add(user_photo)
            
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            print(f"❌ Помилка при збереженні фото: {e}")
            return False
    
    return False
