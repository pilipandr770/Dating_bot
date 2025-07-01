from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Клавіатура для вибору статі
def gender_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Чоловік", callback_data="gender:male"),
        InlineKeyboardButton("Жінка", callback_data="gender:female"),
    )
    return keyboard

# Клавіатура для вибору орієнтації
def orientation_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Чоловіки", callback_data="orientation:men"),
        InlineKeyboardButton("Жінки", callback_data="orientation:women"),
        InlineKeyboardButton("Всі", callback_data="orientation:all"),
    )
    return keyboard
