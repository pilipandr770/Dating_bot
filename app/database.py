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
            # Виправлено шлях до schema.sql, щоб працювало з будь-якого місця
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            schema_path = os.path.join(base_dir, "schema.sql")
            with open(schema_path, "r", encoding="utf-8") as f:
                # Розділяємо SQL на окремі команди
                sql_commands = f.read().split(';')
                # Виконуємо кожну команду окремо
                for command in sql_commands:
                    # Пропускаємо порожні команди
                    if command.strip():
                        try:
                            await conn.execute(text(command.strip()))
                        except Exception as e:
                            print(f"Помилка при виконанні команди: {e}")
            print("✅ Створено всі таблиці.")
        else:
            print("✅ Таблиці вже існують.")
            
        # Перевіряємо наявність колонки language у таблиці users
        try:
            # Перевіряємо, чи є колонка language
            result = await conn.execute(
                text(f"SELECT column_name FROM information_schema.columns WHERE table_schema = :schema AND table_name = 'users' AND column_name = 'language'"),
                {"schema": DB_SCHEMA}
            )
            column_exists = result.scalar() is not None
            
            # Якщо колонки немає - додаємо її
            if not column_exists:
                print("📦 Додаємо колонку language до таблиці users...")
                await conn.execute(text(f"ALTER TABLE {DB_SCHEMA}.users ADD COLUMN language TEXT"))
                print("✅ Колонку language додано.")
        except Exception as e:
            print(f"Помилка при перевірці колонки language: {e}")


# Генератор сесій
async def get_session():
    async with SessionLocal() as session:
        yield session


# Локальний запуск для перевірки
if __name__ == "__main__":
    asyncio.run(init_db())
