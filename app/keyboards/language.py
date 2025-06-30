# файл: app/keyboards/language.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Українська 🇺🇦", callback_data="lang_ua"),
        InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
        InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        InlineKeyboardButton("Deutsch 🇩🇪", callback_data="lang_de")
    )
    return keyboard
