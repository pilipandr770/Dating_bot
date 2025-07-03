# app/booking/keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

def booking_menu_keyboard(lang="ru"):
    """Клавиатура основного меню бронирования с учетом языка пользователя"""
    texts = {
        "ua": {"show": "🔍 Показати варіанти", "my": "📋 Мої бронювання", "cancel": "❌ Скасувати"},
        "ru": {"show": "🔍 Показать варианты", "my": "📋 Мои бронирования", "cancel": "❌ Отмена"},
        "en": {"show": "🔍 Show options", "my": "📋 My bookings", "cancel": "❌ Cancel"},
        "de": {"show": "🔍 Optionen anzeigen", "my": "📋 Meine Buchungen", "cancel": "❌ Abbrechen"}
    }
    
    t = texts.get(lang, texts["en"])
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(t["show"], callback_data="booking:show"),
        InlineKeyboardButton(t["my"], callback_data="booking:my_bookings")
    )
    kb.add(InlineKeyboardButton(t["cancel"], callback_data="booking:cancel"))
    return kb

def date_keyboard(lang="ru"):
    """Клавиатура для выбора даты"""
    texts = {
        "ua": {"today": "🔹 Сьогодні", "tomorrow": "🔸 Завтра", "other": "📆 Інша дата", "cancel": "🔙 Назад"},
        "ru": {"today": "🔹 Сегодня", "tomorrow": "🔸 Завтра", "other": "📆 Другая дата", "cancel": "🔙 Назад"},
        "en": {"today": "🔹 Today", "tomorrow": "🔸 Tomorrow", "other": "📆 Other date", "cancel": "🔙 Back"},
        "de": {"today": "🔹 Heute", "tomorrow": "🔸 Morgen", "other": "📆 Anderes Datum", "cancel": "🔙 Zurück"}
    }
    
    t = texts.get(lang, texts["en"])
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(t["today"], callback_data=f"booking:date:{today}"),
        InlineKeyboardButton(t["tomorrow"], callback_data=f"booking:date:{tomorrow}")
    )
    kb.add(
        InlineKeyboardButton(f"📅 {day_after}", callback_data=f"booking:date:{day_after}"),
        InlineKeyboardButton(t["other"], callback_data="booking:custom_date")
    )
    kb.add(InlineKeyboardButton(t["cancel"], callback_data="booking:cancel"))
    return kb

def place_type_keyboard(lang="ru"):
    """Клавиатура для выбора типа места"""
    texts = {
        "ua": {
            "restaurant": "🍽 Ресторан", "cafe": "☕️ Кафе", "bar": "🍸 Бар",
            "cinema": "🎬 Кінотеатр", "event": "🎭 Подія", "back": "🔙 Назад"
        },
        "ru": {
            "restaurant": "🍽 Ресторан", "cafe": "☕️ Кафе", "bar": "🍸 Бар",
            "cinema": "🎬 Кинотеатр", "event": "🎭 Событие", "back": "🔙 Назад"
        },
        "en": {
            "restaurant": "🍽 Restaurant", "cafe": "☕️ Cafe", "bar": "🍸 Bar",
            "cinema": "🎬 Cinema", "event": "🎭 Event", "back": "🔙 Back"
        },
        "de": {
            "restaurant": "🍽 Restaurant", "cafe": "☕️ Café", "bar": "🍸 Bar",
            "cinema": "🎬 Kino", "event": "🎭 Veranstaltung", "back": "🔙 Zurück"
        }
    }
    
    t = texts.get(lang, texts["en"])
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(t["restaurant"], callback_data="booking:type:restaurant"),
        InlineKeyboardButton(t["cafe"], callback_data="booking:type:cafe")
    )
    kb.add(
        InlineKeyboardButton(t["bar"], callback_data="booking:type:bar"),
        InlineKeyboardButton(t["cinema"], callback_data="booking:type:cinema")
    )
    kb.add(InlineKeyboardButton(t["event"], callback_data="booking:type:event"))
    kb.add(InlineKeyboardButton(t["back"], callback_data="booking:back"))
    return kb

def places_keyboard(recommendations: list, lang="ru"):
    """Клавиатура для выбора конкретного места из списка рекомендаций"""
    texts = {
        "ua": {"back": "🔙 Назад", "more": "🔄 Більше варіантів"},
        "ru": {"back": "🔙 Назад", "more": "🔄 Больше вариантов"},
        "en": {"back": "🔙 Back", "more": "🔄 More options"},
        "de": {"back": "🔙 Zurück", "more": "🔄 Weitere Optionen"}
    }
    
    t = texts.get(lang, texts["en"])
    kb = InlineKeyboardMarkup(row_width=1)
    
    for i, rec in enumerate(recommendations[:5]):  # Ограничиваем количество кнопок
        # Форматируем время для отображения
        time_str = rec['time']
        if isinstance(time_str, str) and "T" in time_str:
            try:
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                time_str = dt.strftime("%d.%m %H:%M")
            except:
                pass
                
        # Формируем название места и дату
        label = f"{rec['name']} — {time_str}"
        data = f"booking:select:{rec['type']}:{rec['id']}"
        kb.add(InlineKeyboardButton(label, callback_data=data))
        
    if len(recommendations) > 5:
        kb.add(InlineKeyboardButton(t["more"], callback_data="booking:more"))
        
    kb.add(InlineKeyboardButton(t["back"], callback_data="booking:back"))
    return kb

def confirm_keyboard(rec: dict, lang="ru", match_id=None):
    """Клавиатура для подтверждения бронирования"""
    texts = {
        "ua": {"confirm": "✅ Підтвердити", "cancel": "❌ Скасувати"},
        "ru": {"confirm": "✅ Подтвердить", "cancel": "❌ Отмена"},
        "en": {"confirm": "✅ Confirm", "cancel": "❌ Cancel"},
        "de": {"confirm": "✅ Bestätigen", "cancel": "❌ Abbrechen"}
    }
    
    t = texts.get(lang, texts["en"])
    kb = InlineKeyboardMarkup(row_width=2)
    
    # Добавляем ID матча, если он есть
    callback_data = f"booking:confirm:{rec['type']}:{rec['id']}"
    if match_id:
        callback_data += f":{match_id}"
    
    kb.add(
        InlineKeyboardButton(t["confirm"], callback_data=callback_data),
        InlineKeyboardButton(t["cancel"], callback_data="booking:cancel")
    )
    return kb

def my_bookings_keyboard(reservations, lang="ru"):
    """Клавиатура для просмотра и управления бронированиями пользователя"""
    texts = {
        "ua": {"cancel_booking": "❌ Скасувати", "back": "🔙 Назад"},
        "ru": {"cancel_booking": "❌ Отменить", "back": "🔙 Назад"},
        "en": {"cancel_booking": "❌ Cancel booking", "back": "🔙 Back"},
        "de": {"cancel_booking": "❌ Buchung stornieren", "back": "🔙 Zurück"}
    }
    
    t = texts.get(lang, texts["en"])
    kb = InlineKeyboardMarkup(row_width=2)
    
    for reservation, place in reservations:
        if reservation.status != "cancelled":
            # Форматируем дату для отображения
            time_str = "неизвестно"
            if reservation.reservation_time:
                try:
                    dt = datetime.fromisoformat(str(reservation.reservation_time).replace("Z", "+00:00"))
                    time_str = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    pass
            
            label = f"{place.name} - {time_str}"
            kb.add(
                InlineKeyboardButton(label, callback_data=f"booking:view:{reservation.id}"),
                InlineKeyboardButton(t["cancel_booking"], callback_data=f"booking:cancel_reservation:{reservation.id}")
            )
    
    kb.add(InlineKeyboardButton(t["back"], callback_data="booking:back"))
    return kb
