# файл: app/bot.py

import asyncio
from aiogram import Bot, Dispatcher
from app.config import TELEGRAM_BOT_TOKEN
from app.database import init_db

# Імпортуємо всі обробники
from app.handlers.start import register_start_handlers
from app.handlers.registration import register_registration_handlers
from app.handlers.swipes import register_swipe_handlers
from app.handlers.chat import register_chat_handlers

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# Головна асинхронна функція запуску
async def main():
    # Ініціалізація бази
    await init_db()

    # Реєстрація обробників
    register_start_handlers(dp)
    register_registration_handlers(dp)
    register_swipe_handlers(dp)
    register_chat_handlers(dp)

    # Запуск бота
    await dp.start_polling(bot, skip_updates=True)

# Старт
if __name__ == '__main__':
    asyncio.run(main())
