# файл: app/handlers/start.py

from aiogram import types
from aiogram.dispatcher import Dispatcher
from app.keyboards.language import get_language_keyboard
from app.keyboards.main_menu import get_main_menu

from app.config import TELEGRAM_BOT_TOKEN
from aiogram import Bot

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Вибір мови
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Вітаємо у SoulLink! Оберіть мову для роботи з ботом:",
        reply_markup=get_language_keyboard()
    )

# Встановлення мови
async def set_language_handler(callback_query: types.CallbackQuery):
    lang = callback_query.data.replace("lang_", "")
    await callback_query.message.delete()
    await callback_query.message.answer(
        "✅ Мову встановлено. Оберіть наступну дію:",
        reply_markup=get_main_menu(lang)
    )

def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_callback_query_handler(set_language_handler, lambda c: c.data.startswith("lang_"))

# Обробка юридичних кнопок
async def show_datenschutz(message: types.Message):
    await message.answer(
        "🔐 **Захист персональних даних**\n\n"
        "Ваші дані зберігаються виключно на серверах у межах ЄС згідно з регламентом GDPR.",
        parse_mode="Markdown"
    )

async def show_agb(message: types.Message):
    await message.answer(
        "📜 **AGB — Правила користування**\n\n"
        "Використовуючи бот, ви погоджуєтесь із правилами платформи. Повна версія буде доступна на сайті.",
        parse_mode="Markdown"
    )

async def show_impressum(message: types.Message):
    await message.answer(
        "ℹ️ **Impressum — Юридична інформація**\n\n"
        "SoulLink Bot розроблено як приватний проєкт. Контактна особа: [Ваше ім’я]\n"
        "Email: example@email.com",
        parse_mode="Markdown"
    )

# Зареєструвати всі обробники
def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_callback_query_handler(set_language_handler, lambda c: c.data.startswith("lang_"))
    dp.register_message_handler(show_datenschutz, lambda m: "Datenschutz" in m.text)
    dp.register_message_handler(show_agb, lambda m: "AGB" in m.text)
    dp.register_message_handler(show_impressum, lambda m: "Impressum" in m.text)
