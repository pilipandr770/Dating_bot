# cinema/router.py

from aiogram import Dispatcher, types
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Text
from app.cinema.keyboards import get_film_selection_keyboard
from app.cinema.services import process_film_purchase
import logging

logger = logging.getLogger(__name__)

def cinema_filter(message: Message):
    if not message.text:
        return False
    return message.text.lower() in ["🎬 кіно", "🎬 кино", "🎬 cinema"]

async def show_film_menu(message: Message):
    try:
        await message.answer(
            "🎬 *Онлайн-кінотеатр*\n\n"
            "Оберіть фільм для перегляду. Кожен фільм коштує 15 токенів.\n"
            "Після оплати ви отримаєте посилання на віртуальну кімнату перегляду.",
            parse_mode="Markdown",
            reply_markup=get_film_selection_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при показе меню фильмов: {str(e)}")
        await message.answer("❌ Сталася помилка при завантаженні меню фільмів. Будь ласка, спробуйте пізніше.")

async def handle_film_purchase(call: CallbackQuery):
    if not call.data or not call.data.startswith("cinema_buy_"):
        await call.answer("❌ Неверный формат данных", show_alert=True)
        return
        
    try:
        # Получаем информацию о фильме
        film_map = {
            "cinema_buy_inception": ("inception", "Inception"),
            "cinema_buy_interstellar": ("interstellar", "Interstellar"),
            "cinema_buy_wolf": ("wolf", "Wolf of Wall Street"),
        }
        
        if call.data not in film_map:
            await call.answer("❌ Недійсний вибір фільму", show_alert=True)
            return
            
        film_id, film_title = film_map.get(call.data)
        
        # Отображаем процесс обработки
        await call.answer()
        await call.message.edit_text(f"🎟 Купівля квитка на *{film_title}*...", parse_mode="Markdown")

        # Обрабатываем покупку
        room_url = await process_film_purchase(call.from_user.id, film_id, film_title)
        
        # Показываем результат
        if room_url:
            # Успешная покупка
            await call.message.answer(
                f"✅ Посилання на кімнату перегляду *{film_title}*:\n\n{room_url}\n\n"
                f"🔸 Посилання діє протягом 24 годин\n"
                f"🔸 Фільм можна дивитися з друзями (просто поділіться посиланням)\n"
                f"🔸 Якщо виникли проблеми, зверніться до підтримки",
                parse_mode="Markdown"
            )
        else:
            # Ошибка покупки
            await call.message.answer(
                "❌ Не вдалося оформити покупку. Можливі причини:\n"
                "• Недостатньо токенів на балансі\n"
                "• Технічні проблеми з сервісом перегляду\n\n"
                "Спробуйте пізніше або зверніться до підтримки."
            )
    except Exception as e:
        # Обрабатываем любые ошибки
        logger.error(f"Ошибка при покупке фильма: {str(e)}")
        
        await call.message.answer(
            "❌ Сталася помилка при обробці запиту. Будь ласка, спробуйте пізніше."
        )

def register_cinema_handlers(dp: Dispatcher):
    """Регистрация обработчиков для модуля кинотеатра"""
    try:
        # Регистрация обработчика меню фильмов
        dp.register_message_handler(show_film_menu, cinema_filter)
        
        # Регистрация обработчика покупки фильмов
        dp.register_callback_query_handler(handle_film_purchase, lambda c: c.data and c.data.startswith("cinema_buy_"))
        
        logger.info("✅ cinema_handlers registered successfully")
    except Exception as e:
        logger.error(f"❌ Error registering cinema_handlers: {str(e)}")
