# app/booking/handlers.py

from aiogram import types, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime, timedelta
import logging

from app.booking.services import BookingService
from app.booking.keyboards import (
    booking_menu_keyboard, places_keyboard, confirm_keyboard,
    date_keyboard, place_type_keyboard, my_bookings_keyboard
)
from app.database import get_session
from app.services.user_service import get_user_by_telegram_id, get_user_language
from app.models.user import User

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем экземпляр сервиса
service = BookingService()

# Определяем состояния FSM для бронирования
class BookingStates(StatesGroup):
    choosing_city = State()
    choosing_place_type = State()
    choosing_date = State()
    entering_custom_date = State()
    viewing_places = State()
    confirming_booking = State()

# Локализованные тексты
texts = {
    "ua": {
        "greeting": "📅 *Бронювання місця для зустрічі*\n\nОберіть дію:",
        "choose_city": "🌆 Введіть назву міста, де ви бажаєте забронювати місце:",
        "choose_place_type": "🏙 Обрано місто: *{city}*\n\nОберіть тип закладу:",
        "choose_date": "📆 Обрано тип: *{place_type}*\n\nОберіть дату для бронювання:",
        "enter_date": "📝 Будь ласка, введіть дату у форматі РРРР-ММ-ДД (наприклад, 2023-12-25):",
        "select_place": "🔎 Знайдені варіанти для {city} на {date}:",
        "no_places": "😔 На жаль, місць не знайдено. Спробуйте змінити параметри пошуку.",
        "confirm_booking": "✅ Ви обрали *{place_name}*\n\n📍 Адреса: {address}\n🕒 Дата: {date}\n\nПідтвердіть бронювання:",
        "booking_confirmed": "🎉 Ваше бронювання підтверджено!\n\n🏢 Місце: *{place_name}*\n📍 Адреса: {address}\n🕒 Дата: {date}\n🔑 Номер бронювання: `{reference}`",
        "booking_cancelled": "❌ Бронювання скасовано.",
        "my_bookings": "📋 *Ваші бронювання:*\n\n{bookings_list}",
        "no_bookings": "📋 *Ваші бронювання:*\n\nУ вас поки що немає бронювань.",
        "cancel_confirm": "❓ Ви впевнені, що бажаєте скасувати бронювання *{place_name}* на {date}?",
        "booking_delete_success": "✅ Бронювання успішно скасовано."
    },
    "ru": {
        "greeting": "📅 *Бронирование места для встречи*\n\nВыберите действие:",
        "choose_city": "🌆 Введите название города, где вы хотите забронировать место:",
        "choose_place_type": "🏙 Выбран город: *{city}*\n\nВыберите тип заведения:",
        "choose_date": "📆 Выбран тип: *{place_type}*\n\nВыберите дату для бронирования:",
        "enter_date": "📝 Пожалуйста, введите дату в формате ГГГГ-ММ-ДД (например, 2023-12-25):",
        "select_place": "🔎 Найденные варианты для {city} на {date}:",
        "no_places": "😔 К сожалению, мест не найдено. Попробуйте изменить параметры поиска.",
        "confirm_booking": "✅ Вы выбрали *{place_name}*\n\n📍 Адрес: {address}\n🕒 Дата: {date}\n\nПодтвердите бронирование:",
        "booking_confirmed": "🎉 Ваше бронирование подтверждено!\n\n🏢 Место: *{place_name}*\n📍 Адрес: {address}\n🕒 Дата: {date}\n🔑 Номер бронирования: `{reference}`",
        "booking_cancelled": "❌ Бронирование отменено.",
        "my_bookings": "📋 *Ваши бронирования:*\n\n{bookings_list}",
        "no_bookings": "📋 *Ваши бронирования:*\n\nУ вас пока нет бронирований.",
        "cancel_confirm": "❓ Вы уверены, что хотите отменить бронирование *{place_name}* на {date}?",
        "booking_delete_success": "✅ Бронирование успешно отменено."
    },
    "en": {
        "greeting": "📅 *Book a place for your date*\n\nChoose an action:",
        "choose_city": "🌆 Enter the name of the city where you want to book a place:",
        "choose_place_type": "🏙 Selected city: *{city}*\n\nChoose the type of venue:",
        "choose_date": "📆 Selected type: *{place_type}*\n\nChoose a date for booking:",
        "enter_date": "📝 Please enter a date in YYYY-MM-DD format (for example, 2023-12-25):",
        "select_place": "🔎 Found options for {city} on {date}:",
        "no_places": "😔 Unfortunately, no places were found. Try changing your search parameters.",
        "confirm_booking": "✅ You have selected *{place_name}*\n\n📍 Address: {address}\n🕒 Date: {date}\n\nConfirm booking:",
        "booking_confirmed": "🎉 Your booking is confirmed!\n\n🏢 Place: *{place_name}*\n📍 Address: {address}\n🕒 Date: {date}\n🔑 Booking number: `{reference}`",
        "booking_cancelled": "❌ Booking cancelled.",
        "my_bookings": "📋 *Your bookings:*\n\n{bookings_list}",
        "no_bookings": "📋 *Your bookings:*\n\nYou don't have any bookings yet.",
        "cancel_confirm": "❓ Are you sure you want to cancel the booking for *{place_name}* on {date}?",
        "booking_delete_success": "✅ Booking successfully cancelled."
    },
    "de": {
        "greeting": "📅 *Einen Ort für Ihr Date buchen*\n\nWählen Sie eine Aktion:",
        "choose_city": "🌆 Geben Sie den Namen der Stadt ein, in der Sie einen Platz buchen möchten:",
        "choose_place_type": "🏙 Ausgewählte Stadt: *{city}*\n\nWählen Sie die Art des Veranstaltungsortes:",
        "choose_date": "📆 Ausgewählter Typ: *{place_type}*\n\nWählen Sie ein Datum für die Buchung:",
        "enter_date": "📝 Bitte geben Sie ein Datum im Format JJJJ-MM-TT ein (zum Beispiel 2023-12-25):",
        "select_place": "🔎 Gefundene Optionen für {city} am {date}:",
        "no_places": "😔 Leider wurden keine Plätze gefunden. Versuchen Sie, Ihre Suchparameter zu ändern.",
        "confirm_booking": "✅ Sie haben *{place_name}* ausgewählt\n\n📍 Adresse: {address}\n🕒 Datum: {date}\n\nBuchung bestätigen:",
        "booking_confirmed": "🎉 Ihre Buchung ist bestätigt!\n\n🏢 Ort: *{place_name}*\n📍 Adresse: {address}\n🕒 Datum: {date}\n🔑 Buchungsnummer: `{reference}`",
        "booking_cancelled": "❌ Buchung storniert.",
        "my_bookings": "📋 *Ihre Buchungen:*\n\n{bookings_list}",
        "no_bookings": "📋 *Ihre Buchungen:*\n\nSie haben noch keine Buchungen.",
        "cancel_confirm": "❓ Sind Sie sicher, dass Sie die Buchung für *{place_name}* am {date} stornieren möchten?",
        "booking_delete_success": "✅ Buchung erfolgreich storniert."
    }
}

# Вспомогательные функции для работы с локализацией
async def get_text(key, lang, **kwargs):
    """Получение локализованного текста с подстановкой параметров"""
    text = texts.get(lang, texts["en"]).get(key, texts["en"][key])
    return text.format(**kwargs) if kwargs else text

async def get_user_city(telegram_id):
    """Получение города пользователя из профиля"""
    async for session in get_session():
        user = await get_user_by_telegram_id(session, telegram_id)
        return user.city if user and user.city else None

# Обработчики команд и колбэков
async def cmd_booking(message: Message, state: FSMContext):
    """Обработчик команды бронирования"""
    telegram_id = str(message.from_user.id)
    lang = await get_user_language(telegram_id)
    
    # Сбрасываем состояние FSM
    await state.finish()
    
    # Проверяем, есть ли у пользователя город в профиле
    user_city = await get_user_city(telegram_id)
    
    if user_city:
        # Если город известен, сохраняем его в состоянии
        await state.update_data(city=user_city)
        # И переходим к выбору типа места
        await BookingStates.choosing_place_type.set()
        
        # Показываем сообщение с выбранным городом и клавиатурой для выбора типа места
        message_text = await get_text("choose_place_type", lang, city=user_city)
        await message.answer(message_text, reply_markup=place_type_keyboard(lang), parse_mode="Markdown")
    else:
        # Если город не известен, просим пользователя ввести город
        await BookingStates.choosing_city.set()
        message_text = await get_text("choose_city", lang)
        await message.answer(message_text)

async def process_city(message: Message, state: FSMContext):
    """Обработчик для получения города"""
    telegram_id = str(message.from_user.id)
    city = message.text.strip()
    lang = await get_user_language(telegram_id)
    
    # Сохраняем город в состоянии
    await state.update_data(city=city)
    
    # Переходим к выбору типа места
    await BookingStates.choosing_place_type.set()
    
    message_text = await get_text("choose_place_type", lang, city=city)
    await message.answer(message_text, reply_markup=place_type_keyboard(lang), parse_mode="Markdown")

async def process_place_type(call: CallbackQuery, state: FSMContext):
    """Обработчик для выбора типа места"""
    await call.answer()
    telegram_id = str(call.from_user.id)
    lang = await get_user_language(telegram_id)
    
    # Получаем тип места из колбэка
    _, _, place_type = call.data.split(":")
    
    # Сохраняем тип места в состоянии
    await state.update_data(place_type=place_type)
    
    # Переходим к выбору даты
    await BookingStates.choosing_date.set()
    
    # Локализованные названия типов мест
    place_type_names = {
        "ua": {"restaurant": "Ресторан", "cafe": "Кафе", "bar": "Бар", "cinema": "Кінотеатр", "event": "Подія"},
        "ru": {"restaurant": "Ресторан", "cafe": "Кафе", "bar": "Бар", "cinema": "Кинотеатр", "event": "Событие"},
        "en": {"restaurant": "Restaurant", "cafe": "Cafe", "bar": "Bar", "cinema": "Cinema", "event": "Event"},
        "de": {"restaurant": "Restaurant", "cafe": "Café", "bar": "Bar", "cinema": "Kino", "event": "Veranstaltung"}
    }
    
    place_type_localized = place_type_names.get(lang, place_type_names["en"]).get(place_type, place_type)
    
    message_text = await get_text("choose_date", lang, place_type=place_type_localized)
    await call.message.edit_text(message_text, reply_markup=date_keyboard(lang), parse_mode="Markdown")

async def process_date(call: CallbackQuery, state: FSMContext):
    """Обработчик для выбора даты"""
    await call.answer()
    telegram_id = str(call.from_user.id)
    lang = await get_user_language(telegram_id)
    
    if call.data == "booking:custom_date":
        # Если пользователь выбрал "Другая дата", просим ввести дату вручную
        await BookingStates.entering_custom_date.set()
        message_text = await get_text("enter_date", lang)
        await call.message.edit_text(message_text)
        return
    
    # Получаем дату из колбэка
    _, _, date = call.data.split(":")
    
    # Сохраняем дату в состоянии
    await state.update_data(date=date)
    
    # Переходим к просмотру мест
    await show_places_for_booking(call, state)

async def process_custom_date(message: Message, state: FSMContext):
    """Обработчик для пользовательской даты"""
    telegram_id = str(message.from_user.id)
    lang = await get_user_language(telegram_id)
    
    date = message.text.strip()
    
    # Проверяем формат даты (очень примитивно)
    if len(date) != 10 or date[4] != '-' or date[7] != '-':
        message_text = await get_text("enter_date", lang)
        await message.answer(f"❌ Неверный формат даты. {message_text}")
        return
    
    # Сохраняем дату в состоянии
    await state.update_data(date=date)
    
    # Переходим к просмотру мест
    await show_places_for_booking_message(message, state)

async def show_places_for_booking(call: CallbackQuery, state: FSMContext):
    """Показывает варианты мест для бронирования"""
    telegram_id = str(call.from_user.id)
    lang = await get_user_language(telegram_id)
    
    # Получаем данные из состояния
    data = await state.get_data()
    city = data.get('city')
    date = data.get('date')
    place_type = data.get('place_type')
    
    # Переходим к просмотру мест
    await BookingStates.viewing_places.set()
    
    # Получаем рекомендации мест
    recommendations = await service.get_recommendations(city, date, place_type)
    
    if not recommendations:
        message_text = await get_text("no_places", lang)
        await call.message.edit_text(message_text)
        return
    
    # Сохраняем рекомендации в состоянии для дальнейшего использования
    await state.update_data(recommendations=recommendations)
    
    message_text = await get_text("select_place", lang, city=city, date=date)
    await call.message.edit_text(message_text, reply_markup=places_keyboard(recommendations, lang))

async def show_places_for_booking_message(message: Message, state: FSMContext):
    """Показывает варианты мест для бронирования (для случая с вводом текста)"""
    telegram_id = str(message.from_user.id)
    lang = await get_user_language(telegram_id)
    
    # Получаем данные из состояния
    data = await state.get_data()
    city = data.get('city')
    date = data.get('date')
    place_type = data.get('place_type')
    
    # Переходим к просмотру мест
    await BookingStates.viewing_places.set()
    
    # Получаем рекомендации мест
    recommendations = await service.get_recommendations(city, date, place_type)
    
    if not recommendations:
        message_text = await get_text("no_places", lang)
        await message.answer(message_text)
        return
    
    # Сохраняем рекомендации в состоянии для дальнейшего использования
    await state.update_data(recommendations=recommendations)
    
    message_text = await get_text("select_place", lang, city=city, date=date)
    await message.answer(message_text, reply_markup=places_keyboard(recommendations, lang))

async def select_place(call: CallbackQuery, state: FSMContext):
    """Обработчик для выбора конкретного места"""
    await call.answer()
    telegram_id = str(call.from_user.id)
    lang = await get_user_language(telegram_id)
    
    # Получаем тип места и его ID из колбэка
    _, _, place_type, place_id = call.data.split(":")
    
    # Получаем данные из состояния
    data = await state.get_data()
    recommendations = data.get('recommendations', [])
    date = data.get('date')
    
    # Находим выбранное место в рекомендациях
    selected_place = None
    for rec in recommendations:
        if rec['type'] == place_type and str(rec['id']) == place_id:
            selected_place = rec
            break
    
    if not selected_place:
        # Если место не найдено в рекомендациях, это ошибка
        await call.message.edit_text("❌ Произошла ошибка. Пожалуйста, начните бронирование заново.")
        await state.finish()
        return
    
    # Сохраняем выбранное место в состоянии
    await state.update_data(selected_place=selected_place)
    
    # Переходим к подтверждению бронирования
    await BookingStates.confirming_booking.set()
    
    # Форматируем дату для отображения
    display_date = date
    if "T" in selected_place['time']:
        try:
            dt = datetime.fromisoformat(selected_place['time'].replace("Z", "+00:00"))
            display_date = dt.strftime("%d.%m.%Y %H:%M")
        except:
            pass
    
    # Отображаем информацию о выбранном месте и предлагаем подтвердить бронирование
    message_text = await get_text(
        "confirm_booking", 
        lang, 
        place_name=selected_place['name'],
        address=selected_place.get('address', 'Нет данных'),
        date=display_date
    )
    
    # Получаем match_id если он есть в данных состояния
    match_id = data.get('match_id')
    
    await call.message.edit_text(
        message_text, 
        reply_markup=confirm_keyboard(selected_place, lang, match_id),
        parse_mode="Markdown"
    )

async def confirm_booking(call: CallbackQuery, state: FSMContext):
    """Обработчик для подтверждения бронирования"""
    await call.answer("Бронирование…")
    telegram_id = str(call.from_user.id)
    lang = await get_user_language(telegram_id)
    
    # Разбираем данные колбэка
    parts = call.data.split(":")
    # place_type, place_id и опционально match_id
    place_type = parts[2]
    place_id = parts[3]
    match_id = int(parts[4]) if len(parts) > 4 else None
    
    # Получаем данные из состояния
    data = await state.get_data()
    selected_place = data.get('selected_place')
    city = data.get('city')
    date = data.get('date')
    
    if not selected_place:
        await call.message.edit_text("❌ Произошла ошибка. Пожалуйста, начните бронирование заново.")
        await state.finish()
        return
    
    # Создаем бронирование
    try:
        # Получаем данные пользователя для передачи в API
        async for session in get_session():
            user = await get_user_by_telegram_id(session, telegram_id)
            user_name = f"{user.first_name}" if user else f"User {telegram_id}"
            
            # Добавляем город в данные места, если его нет
            if 'city' not in selected_place:
                selected_place['city'] = city
                
            # Создаем бронирование
            new_res = await service.create_reservation(
                session, 
                user.id if user else int(telegram_id), 
                match_id, 
                selected_place,
                user_name
            )
            await session.commit()
            
            # Форматируем дату для отображения
            display_date = date
            if "T" in selected_place['time']:
                try:
                    dt = datetime.fromisoformat(selected_place['time'].replace("Z", "+00:00"))
                    display_date = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    pass
            
            # Отображаем подтверждение бронирования
            message_text = await get_text(
                "booking_confirmed", 
                lang, 
                place_name=selected_place['name'],
                address=selected_place.get('address', 'Нет данных'),
                date=display_date,
                reference=new_res.external_reference
            )
            
            await call.message.edit_text(message_text, parse_mode="Markdown")
            
            # Сбрасываем состояние
            await state.finish()
            
    except Exception as e:
        logger.error(f"Ошибка при создании бронирования: {e}")
        await call.message.edit_text(f"❌ Произошла ошибка при бронировании. Пожалуйста, попробуйте позже.")
        await state.finish()

async def my_bookings(call: CallbackQuery):
    """Обработчик для просмотра своих бронирований"""
    await call.answer()
    telegram_id = str(call.from_user.id)
    lang = await get_user_language(telegram_id)
    
    try:
        async for session in get_session():
            user = await get_user_by_telegram_id(session, telegram_id)
            
            if not user:
                await call.message.edit_text("❌ Пользователь не найден.")
                return
            
            # Получаем бронирования пользователя
            reservations = await service.get_user_reservations(session, user.id)
            
            if not reservations:
                message_text = await get_text("no_bookings", lang)
                await call.message.edit_text(message_text, parse_mode="Markdown")
                return
            
            # Формируем список бронирований
            bookings_list = []
            for reservation, place in reservations:
                if reservation.status == "cancelled":
                    continue
                    
                # Форматируем дату для отображения
                display_date = "неизвестно"
                if reservation.reservation_time:
                    try:
                        dt = datetime.fromisoformat(str(reservation.reservation_time).replace("Z", "+00:00"))
                        display_date = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        pass
                
                booking_text = f"🏢 *{place.name}*\n"
                booking_text += f"📅 {display_date}\n"
                booking_text += f"🔑 `{reservation.external_reference}`\n"
                booking_text += f"📍 {place.city or 'Город не указан'}\n\n"
                
                bookings_list.append(booking_text)
            
            # Объединяем все бронирования в одно сообщение
            message_text = await get_text("my_bookings", lang, bookings_list="".join(bookings_list))
            
            # Показываем бронирования с клавиатурой для управления
            await call.message.edit_text(
                message_text, 
                reply_markup=my_bookings_keyboard(reservations, lang),
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error(f"Ошибка при получении бронирований: {e}")
        await call.message.edit_text("❌ Произошла ошибка при получении бронирований.")

async def cancel_reservation(call: CallbackQuery):
    """Обработчик для отмены бронирования"""
    await call.answer()
    telegram_id = str(call.from_user.id)
    lang = await get_user_language(telegram_id)
    
    # Получаем ID бронирования из колбэка
    _, _, reservation_id = call.data.split(":")
    
    try:
        async for session in get_session():
            user = await get_user_by_telegram_id(session, telegram_id)
            
            if not user:
                await call.message.edit_text("❌ Пользователь не найден.")
                return
            
            # Отменяем бронирование
            cancelled = await service.cancel_reservation(session, int(reservation_id), user.id)
            await session.commit()
            
            if not cancelled:
                await call.message.edit_text("❌ Бронирование не найдено или уже отменено.")
                return
            
            # Возвращаемся к списку бронирований
            await my_bookings(call)
    
    except Exception as e:
        logger.error(f"Ошибка при отмене бронирования: {e}")
        await call.message.edit_text("❌ Произошла ошибка при отмене бронирования.")

async def cancel_booking(call: CallbackQuery, state: FSMContext):
    """Обработчик для отмены процесса бронирования"""
    await call.answer()
    telegram_id = str(call.from_user.id)
    lang = await get_user_language(telegram_id)
    
    message_text = await get_text("booking_cancelled", lang)
    await call.message.edit_text(message_text)
    
    # Сбрасываем состояние
    await state.finish()

async def back_to_menu(call: CallbackQuery, state: FSMContext):
    """Обработчик для возврата в меню бронирования"""
    await call.answer()
    telegram_id = str(call.from_user.id)
    lang = await get_user_language(telegram_id)
    
    # Получаем данные из состояния
    data = await state.get_data()
    
    current_state = await state.get_state()
    
    if current_state == "BookingStates:viewing_places":
        # Если мы просматривали места, возвращаемся к выбору даты
        await BookingStates.choosing_date.set()
        
        place_type = data.get('place_type', 'venue')
        
        # Локализованные названия типов мест
        place_type_names = {
            "ua": {"restaurant": "Ресторан", "cafe": "Кафе", "bar": "Бар", "cinema": "Кінотеатр", "event": "Подія"},
            "ru": {"restaurant": "Ресторан", "cafe": "Кафе", "bar": "Бар", "cinema": "Кинотеатр", "event": "Событие"},
            "en": {"restaurant": "Restaurant", "cafe": "Cafe", "bar": "Bar", "cinema": "Cinema", "event": "Event"},
            "de": {"restaurant": "Restaurant", "cafe": "Café", "bar": "Bar", "cinema": "Kino", "event": "Veranstaltung"}
        }
        
        place_type_localized = place_type_names.get(lang, place_type_names["en"]).get(place_type, place_type)
        
        message_text = await get_text("choose_date", lang, place_type=place_type_localized)
        await call.message.edit_text(message_text, reply_markup=date_keyboard(lang), parse_mode="Markdown")
        
    elif current_state == "BookingStates:confirming_booking":
        # Если мы подтверждали бронирование, возвращаемся к просмотру мест
        await BookingStates.viewing_places.set()
        
        city = data.get('city', '')
        date = data.get('date', '')
        recommendations = data.get('recommendations', [])
        
        message_text = await get_text("select_place", lang, city=city, date=date)
        await call.message.edit_text(message_text, reply_markup=places_keyboard(recommendations, lang))
        
    else:
        # В остальных случаях возвращаемся к началу бронирования
        await state.finish()
        
        message_text = await get_text("greeting", lang)
        await call.message.edit_text(message_text, reply_markup=booking_menu_keyboard(lang), parse_mode="Markdown")

def register_booking_handlers(dp: Dispatcher):
    """Регистрация обработчиков для бронирования"""
    # Команды для входа в меню бронирования
    dp.register_message_handler(
        cmd_booking, 
        lambda m: any(word in m.text for word in ["📅 Бронювання", "📅 Бронирование", "📅 Booking", "📅 Buchung"]),
        state="*"
    )
    
    # Обработчики состояний FSM
    dp.register_message_handler(process_city, state=BookingStates.choosing_city)
    dp.register_message_handler(process_custom_date, state=BookingStates.entering_custom_date)
    
    # Обработчики колбэков
    dp.register_callback_query_handler(process_place_type, lambda c: c.data.startswith("booking:type:"), state=BookingStates.choosing_place_type)
    dp.register_callback_query_handler(process_date, lambda c: c.data.startswith("booking:date:") or c.data == "booking:custom_date", state=BookingStates.choosing_date)
    dp.register_callback_query_handler(select_place, lambda c: c.data.startswith("booking:select:"), state=BookingStates.viewing_places)
    dp.register_callback_query_handler(confirm_booking, lambda c: c.data.startswith("booking:confirm:"), state=BookingStates.confirming_booking)
    
    # Служебные колбэки
    dp.register_callback_query_handler(my_bookings, lambda c: c.data == "booking:my_bookings", state="*")
    dp.register_callback_query_handler(cancel_reservation, lambda c: c.data.startswith("booking:cancel_reservation:"), state="*")
    dp.register_callback_query_handler(cancel_booking, lambda c: c.data == "booking:cancel", state="*")
    dp.register_callback_query_handler(back_to_menu, lambda c: c.data == "booking:back", state="*")
