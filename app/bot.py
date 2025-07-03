# файл: app/bot.py

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from app.config import TELEGRAM_BOT_TOKEN
from app.database import init_db

# Імпортуємо всі обробники
from app.handlers.start import register_start_handlers
from app.handlers.registration import register_registration_handlers
from app.handlers.swipes import register_swipe_handlers
from app.handlers.chat import register_chat_handlers
from app.handlers.search_settings import register_search_settings_handlers
from app.handlers.tokens import register_token_handlers
from app.handlers.admin import register_admin_handlers
from app.handlers.reservations import register_reservation_handlers
from app.booking import register_booking_handlers

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Головна асинхронна функція запуску
async def main():
    # Ініціалізація бази
    await init_db()

    # Реєстрація обробників
    register_start_handlers(dp)
    register_search_settings_handlers(dp)  # Регистрируем первым для приоритета
    register_registration_handlers(dp)
    register_swipe_handlers(dp)
    register_chat_handlers(dp)
    register_token_handlers(dp)  # Регистрируем обработчики токенов
    register_admin_handlers(dp)  # Регистрируем обработчики администратора
    register_reservation_handlers(dp)  # Регистрируем обработчики бронирования
    register_booking_handlers(dp)  # Регистрируем обработчики бронирования из модуля booking

    # Запуск бота
    # Версія aiogram 2.25.1 
    await dp.start_polling()

# Старт
if __name__ == '__main__':
    asyncio.run(main())
