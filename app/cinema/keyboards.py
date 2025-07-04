# cinema/keyboards.py

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_film_selection_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Inception (15 токенів)", callback_data="cinema_buy_inception")],
        [InlineKeyboardButton(text="🚀 Interstellar (15 токенів)", callback_data="cinema_buy_interstellar")],
        [InlineKeyboardButton(text="🐺 Wolf of Wall Street (15 токенів)", callback_data="cinema_buy_wolf")]
    ])
    return keyboard
