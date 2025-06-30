# файл: app/database.py

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
import asyncio

load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL")
DB_SCHEMA = os.getenv("DB_SCHEMA")

engine = create_async_engine(POSTGRES_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """
    Перевіряє наявність таблиць у схемі та створює їх із schema.sql при першому запуску.
    """
    async with engine.begin() as conn:
        # Створюємо схему, якщо її ще нема
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))

        # Перевіряємо, чи таблиці вже є
        result = await conn.execute(
            text(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = :schema"),
            {"schema": DB_SCHEMA}
        )
        tables_count = result.scalar()

        # Якщо таблиць нема, виконуємо schema.sql
        if tables_count == 0:
            print("📦 Таблиці не знайдено — створюємо з schema.sql...")
            with open("schema.sql", "r", encoding="utf-8") as f:
                sql = f.read()
            await conn.execute(text(sql))
            print("✅ Створено всі таблиці.")
        else:
            print("✅ Таблиці вже існують.")


# Генератор сесій
async def get_session():
    async with SessionLocal() as session:
        yield session


# Локальний запуск для перевірки
if __name__ == "__main__":
    asyncio.run(init_db())
