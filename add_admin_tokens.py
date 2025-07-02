import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Подключение к базе данных
POSTGRES_URL = os.getenv("POSTGRES_URL")
DB_SCHEMA = os.getenv("DB_SCHEMA", "dating_bot")
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

engine = create_async_engine(POSTGRES_URL)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def add_admin_tokens():
    """Добавляет токены администраторам для тестирования"""
    
    if not ADMIN_IDS:
        print("❌ Список администраторов (ADMIN_IDS) пуст.")
        return
    
    async with async_session() as session:
        try:
            for admin_id in ADMIN_IDS:
                admin_id = admin_id.strip()
                if not admin_id:
                    continue
                
                # Сначала проверим, существует ли пользователь
                check_sql = f"""
                SELECT id, token_balance, is_admin FROM {DB_SCHEMA}.users 
                WHERE telegram_id = :telegram_id
                """
                result = await session.execute(text(check_sql), {"telegram_id": admin_id})
                user_row = result.fetchone()
                
                if user_row:
                    user_id, current_balance, is_admin = user_row
                    
                    # Обновляем баланс и флаг администратора
                    tokens_to_add = 1000  # Добавляем 1000 токенов для тестирования
                    update_sql = f"""
                    UPDATE {DB_SCHEMA}.users 
                    SET token_balance = :new_balance, is_admin = true
                    WHERE id = :user_id
                    """
                    
                    new_balance = current_balance + tokens_to_add
                    await session.execute(
                        text(update_sql), 
                        {"new_balance": new_balance, "user_id": user_id}
                    )
                    
                    print(f"✅ Администратору {admin_id} добавлено {tokens_to_add} токенов. Новый баланс: {new_balance}")
                    print(f"✅ Установлен флаг is_admin=true для пользователя {admin_id}")
                else:
                    print(f"⚠️ Пользователь с telegram_id {admin_id} не найден в базе. Нужно создать анкету в боте.")
            
            await session.commit()
            print("✅ Операция успешно выполнена.")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при обновлении баланса: {e}")

async def main():
    await add_admin_tokens()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
