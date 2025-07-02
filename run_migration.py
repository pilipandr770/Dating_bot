import asyncio
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Подключение к базе данных
POSTGRES_URL = os.getenv("POSTGRES_URL")

async def run_migration():
    """Выполняет миграцию для добавления столбца is_admin в таблицу users"""
    
    if not POSTGRES_URL:
        logger.error("❌ Ошибка: не найдена переменная окружения POSTGRES_URL")
        return
    
    # Создаем подключение к БД
    engine = create_async_engine(POSTGRES_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        # Выполняем SQL-запросы для миграции
        async with async_session() as session:
            # Добавляем столбец is_admin
            await session.execute(
                text("ALTER TABLE dating_bot.users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE")
            )
            
            # Устанавливаем флаг is_admin=true для администраторов
            await session.execute(
                text("UPDATE dating_bot.users SET is_admin = TRUE WHERE telegram_id = '7444992311'")
            )
            
            # Фиксируем транзакцию
            await session.commit()
        
        logger.info("✅ Миграция успешно выполнена: добавлен столбец is_admin в таблицу users")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении миграции: {str(e)}")
    
    finally:
        # Закрываем подключение к БД
        await engine.dispose()

async def main():
    await run_migration()

if __name__ == "__main__":
    asyncio.run(main())
