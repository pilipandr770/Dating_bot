#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv
import asyncpg
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL")

async def run_migration():
    # Чтение SQL скрипта
    migration_path = os.path.join(os.path.dirname(__file__), 'migrations', 'update_places_reservations.sql')
    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    # Применение миграции
    logger.info("Подключение к базе данных...")
    conn = None
    try:
        # Извлекаем параметры подключения из URL
        if POSTGRES_URL.startswith("postgresql+asyncpg://"):
            # Преобразуем формат asyncpg в формат для asyncpg
            postgres_url = POSTGRES_URL.replace("postgresql+asyncpg://", "postgresql://")
        else:
            postgres_url = POSTGRES_URL
            
        # Подключаемся к БД
        conn = await asyncpg.connect(postgres_url)
        
        logger.info("Запуск миграции...")
        # Выполняем SQL запрос
        await conn.execute(migration_sql)
        
        logger.info("Миграция успешно применена!")
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении миграции: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
