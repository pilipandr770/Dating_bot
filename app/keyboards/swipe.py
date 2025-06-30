from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def swipe_keyboard(user_id: int):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("❤️", callback_data=f"like_{user_id}"),
        InlineKeyboardButton("❌", callback_data=f"dislike_{user_id}")
    )
    kb.add(
        InlineKeyboardButton("🚫 Поскаржитися", callback_data=f"report_{user_id}")
    )
    return kb

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def swipe_keyboard(user_id: int):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("❤️", callback_data=f"like_{user_id}"),
        InlineKeyboardButton("❌", callback_data=f"dislike_{user_id}")
    )
    kb.add(
        InlineKeyboardButton("🚫 Поскаржитися", callback_data=f"report_{user_id}")
    )
    return kb

