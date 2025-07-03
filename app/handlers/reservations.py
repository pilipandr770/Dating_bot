# файл: app/handlers/reservations.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.services.user_service import get_user_language
from app.keyboards.main_menu import get_main_menu
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.database import get_session
from sqlalchemy import select
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для работы с бронированиями
class ReservationStates(StatesGroup):
    waiting_for_city = State()  # Ожидание ввода города
    waiting_for_place_type = State()  # Ожидание выбора типа места
    waiting_for_date = State()  # Ожидание ввода даты
    waiting_for_time = State()  # Ожидание ввода времени
    waiting_for_confirmation = State()  # Ожидание подтверждения

# Обработчик команды /reservation или нажатия кнопки "Бронирование"
async def cmd_reservation(message: types.Message):
    telegram_id = str(message.from_user.id)
    
    # Получаем язык пользователя
    lang = await get_user_language(telegram_id)
    
    # Локализованные сообщения
    texts = {
        "ua": "📅 *Бронювання місця для зустрічі*\n\nОберіть дію:",
        "ru": "📅 *Бронирование места для встречи*\n\nВыберите действие:",
        "en": "📅 *Book a place for a date*\n\nChoose an action:",
        "de": "📅 *Einen Platz für ein Date buchen*\n\nWählen Sie eine Aktion:"
    }
    
    # Локализованные кнопки
    button_texts = {
        "ua": {"new": "🔍 Знайти місце", "my": "📋 Мої бронювання", "back": "⬅️ Назад"},
        "ru": {"new": "🔍 Найти место", "my": "📋 Мои бронирования", "back": "⬅️ Назад"},
        "en": {"new": "🔍 Find a place", "my": "📋 My reservations", "back": "⬅️ Back"},
        "de": {"new": "🔍 Einen Platz finden", "my": "📋 Meine Buchungen", "back": "⬅️ Zurück"}
    }
    
    t = button_texts.get(lang, button_texts["en"])
    
    # Создаем инлайн-клавиатуру
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(t["new"], callback_data="reservation_new"),
        InlineKeyboardButton(t["my"], callback_data="reservation_my")
    )
    markup.add(InlineKeyboardButton(t["back"], callback_data="reservation_back"))
    
    await message.answer(texts.get(lang, texts["en"]), reply_markup=markup, parse_mode="Markdown")

# Обработчик для начала нового бронирования
async def on_reservation_new(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = str(callback_query.from_user.id)
    
    # Получаем язык пользователя
    lang = await get_user_language(telegram_id)
    
    # Локализованные сообщения
    texts = {
        "ua": "🌆 Введіть назву міста, де ви бажаєте забронювати місце:",
        "ru": "🌆 Введите название города, где вы хотите забронировать место:",
        "en": "🌆 Enter the name of the city where you want to book a place:",
        "de": "🌆 Geben Sie den Namen der Stadt ein, in der Sie einen Platz buchen möchten:"
    }
    
    # Устанавливаем состояние ожидания ввода города
    await ReservationStates.waiting_for_city.set()
    
    await callback_query.message.edit_text(texts.get(lang, texts["en"]))
    await callback_query.answer()

# Обработчик для просмотра текущих бронирований
async def on_reservation_my(callback_query: types.CallbackQuery):
    telegram_id = str(callback_query.from_user.id)
    
    # Получаем язык пользователя
    lang = await get_user_language(telegram_id)
    
    # Локализованные сообщения
    texts = {
        "ua": "📋 *Ваші бронювання:*\n\nУ вас поки немає бронювань.",
        "ru": "📋 *Ваши бронирования:*\n\nУ вас пока нет бронирований.",
        "en": "📋 *Your reservations:*\n\nYou don't have any reservations yet.",
        "de": "📋 *Ihre Buchungen:*\n\nSie haben noch keine Buchungen."
    }
    
    # Здесь будем загружать бронирования из базы данных
    reservations = []
    
    if not reservations:
        # Если бронирований нет
        message = texts.get(lang, texts["en"])
    else:
        # Если есть бронирования, формируем сообщение
        pass
    
    # Локализованные кнопки
    button_texts = {
        "ua": "⬅️ Назад",
        "ru": "⬅️ Назад",
        "en": "⬅️ Back",
        "de": "⬅️ Zurück"
    }
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(button_texts.get(lang, button_texts["en"]), callback_data="reservation_back_to_menu"))
    
    await callback_query.message.edit_text(message, reply_markup=markup, parse_mode="Markdown")
    await callback_query.answer()

# Обработчик для возврата в основное меню
async def on_reservation_back(callback_query: types.CallbackQuery):
    telegram_id = str(callback_query.from_user.id)
    
    # Получаем язык пользователя
    lang = await get_user_language(telegram_id)
    
    # Просто удаляем инлайн-клавиатуру и оставляем обычное меню
    await callback_query.message.delete()
    await callback_query.answer()

# Обработчик для возврата в меню бронирования
async def on_reservation_back_to_menu(callback_query: types.CallbackQuery):
    # Просто вызываем обработчик команды бронирования
    await cmd_reservation(callback_query.message)
    await callback_query.answer()

# Обработчик для получения города
async def process_city(message: types.Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    city = message.text.strip()
    
    # Сохраняем город в состоянии
    await state.update_data(city=city)
    
    # Получаем язык пользователя
    lang = await get_user_language(telegram_id)
    
    # Локализованные сообщения
    texts = {
        "ua": f"🏙 Обрано місто: *{city}*\n\nОберіть тип закладу:",
        "ru": f"🏙 Выбран город: *{city}*\n\nВыберите тип заведения:",
        "en": f"🏙 Selected city: *{city}*\n\nChoose the type of place:",
        "de": f"🏙 Ausgewählte Stadt: *{city}*\n\nWählen Sie die Art des Ortes:"
    }
    
    # Локализованные кнопки типов заведений
    button_texts = {
        "ua": {
            "restaurant": "🍽 Ресторан",
            "cafe": "☕️ Кафе",
            "bar": "🍸 Бар",
            "park": "🌳 Парк",
            "cinema": "🎬 Кінотеатр",
            "other": "🏢 Інше",
            "back": "⬅️ Назад"
        },
        "ru": {
            "restaurant": "🍽 Ресторан",
            "cafe": "☕️ Кафе",
            "bar": "🍸 Бар",
            "park": "🌳 Парк",
            "cinema": "🎬 Кинотеатр",
            "other": "🏢 Другое",
            "back": "⬅️ Назад"
        },
        "en": {
            "restaurant": "🍽 Restaurant",
            "cafe": "☕️ Cafe",
            "bar": "🍸 Bar",
            "park": "🌳 Park",
            "cinema": "🎬 Cinema",
            "other": "🏢 Other",
            "back": "⬅️ Back"
        },
        "de": {
            "restaurant": "🍽 Restaurant",
            "cafe": "☕️ Café",
            "bar": "🍸 Bar",
            "park": "🌳 Park",
            "cinema": "🎬 Kino",
            "other": "🏢 Andere",
            "back": "⬅️ Zurück"
        }
    }
    
    t = button_texts.get(lang, button_texts["en"])
    
    # Создаем инлайн-клавиатуру с типами заведений
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(t["restaurant"], callback_data="place_type_restaurant"),
        InlineKeyboardButton(t["cafe"], callback_data="place_type_cafe")
    )
    markup.add(
        InlineKeyboardButton(t["bar"], callback_data="place_type_bar"),
        InlineKeyboardButton(t["park"], callback_data="place_type_park")
    )
    markup.add(
        InlineKeyboardButton(t["cinema"], callback_data="place_type_cinema"),
        InlineKeyboardButton(t["other"], callback_data="place_type_other")
    )
    markup.add(InlineKeyboardButton(t["back"], callback_data="reservation_back_to_menu"))
    
    # Устанавливаем состояние ожидания выбора типа места
    await ReservationStates.waiting_for_place_type.set()
    
    await message.answer(texts.get(lang, texts["en"]), reply_markup=markup, parse_mode="Markdown")

# Регистрация обработчиков
def register_reservation_handlers(dp: Dispatcher):
    # Команды для бронирования
    dp.register_message_handler(
        cmd_reservation, 
        lambda m: any(word in m.text for word in ["Бронювання", "Бронирование", "Reservation", "Buchung"]),
        state="*"
    )
    dp.register_message_handler(cmd_reservation, commands="reservation", state="*")
    
    # Инлайн-кнопки меню бронирования
    dp.register_callback_query_handler(on_reservation_new, lambda c: c.data == "reservation_new", state="*")
    dp.register_callback_query_handler(on_reservation_my, lambda c: c.data == "reservation_my", state="*")
    dp.register_callback_query_handler(on_reservation_back, lambda c: c.data == "reservation_back", state="*")
    dp.register_callback_query_handler(on_reservation_back_to_menu, lambda c: c.data == "reservation_back_to_menu", state="*")
    
    # Обработчики состояний для бронирования
    dp.register_message_handler(process_city, state=ReservationStates.waiting_for_city)
