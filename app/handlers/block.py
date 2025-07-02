# файл: app/handlers/block.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select, or_
from app.models.user import User
from app.models.match import Match
from app.models.blocked_users import BlockedUser
from app.services.block_service import block_user, unblock_user, get_blocked_users
from app.services.user_service import get_user_language
from app.database import get_session
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для FSM блокировки
class BlockState(StatesGroup):
    waiting_for_reason = State()
    confirm_unblock = State()

# Команда /block для показа списка заблокированных пользователей
async def cmd_block_list(message: types.Message):
    tg_id = str(message.from_user.id)
    lang = await get_user_language(tg_id)
    
    # Получаем список заблокированных пользователей
    blocked_users = await get_blocked_users(tg_id)
    
    if not blocked_users:
        texts = {
            "ua": "У вас немає заблокованих користувачів.",
            "ru": "У вас нет заблокированных пользователей.",
            "en": "You don't have any blocked users.",
            "de": "Sie haben keine blockierten Benutzer."
        }
        return await message.answer(texts.get(lang, texts["ua"]))
    
    # Формируем сообщение со списком заблокированных пользователей
    titles = {
        "ua": "📋 Список заблокованих користувачів:",
        "ru": "📋 Список заблокированных пользователей:",
        "en": "📋 List of blocked users:",
        "de": "📋 Liste der blockierten Benutzer:"
    }
    
    text = titles.get(lang, titles["ua"]) + "\n\n"
    kb = InlineKeyboardMarkup(row_width=1)
    
    for user in blocked_users:
        text += f"👤 {user['name']}, {user['age']}\n"
        if user['reason']:
            text += f"🚫 {user['reason']}\n"
        text += f"📅 {user['blocked_at'].strftime('%d.%m.%Y')}\n\n"
        
        # Добавляем кнопку разблокировки
        unblock_texts = {
            "ua": f"Розблокувати {user['name']}",
            "ru": f"Разблокировать {user['name']}",
            "en": f"Unblock {user['name']}",
            "de": f"Entsperren {user['name']}"
        }
        kb.add(InlineKeyboardButton(
            unblock_texts.get(lang, unblock_texts["ua"]),
            callback_data=f"unblock_{user['id']}"
        ))
    
    await message.answer(text, reply_markup=kb)

# Обработчик для блокировки пользователя из профиля или чата
async def block_user_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    if not data.startswith("block_"):
        return
    
    # Получаем ID пользователя для блокировки
    user_id = int(data.split("_")[1])
    
    # Сохраняем ID в состоянии
    await state.update_data(block_user_id=user_id)
    
    # Запрашиваем причину блокировки
    tg_id = str(callback_query.from_user.id)
    lang = await get_user_language(tg_id)
    
    texts = {
        "ua": "Вкажіть причину блокування (або натисніть /skip щоб пропустити):",
        "ru": "Укажите причину блокировки (или нажмите /skip чтобы пропустить):",
        "en": "Please specify the reason for blocking (or press /skip to skip):",
        "de": "Bitte geben Sie den Grund für die Sperrung an (oder drücken Sie /skip zum Überspringen):"
    }
    
    await callback_query.message.answer(texts.get(lang, texts["ua"]))
    await BlockState.waiting_for_reason.set()
    
    # Отвечаем на callback чтобы убрать часики
    await callback_query.answer()

# Обработчик ввода причины блокировки
async def process_block_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("block_user_id")
    
    if not user_id:
        await state.finish()
        return await message.answer("❌ Ошибка: не удалось определить пользователя для блокировки.")
    
    # Определяем причину блокировки
    reason = None
    if message.text and not message.text.startswith("/skip"):
        reason = message.text
    
    # Блокируем пользователя
    tg_id = str(message.from_user.id)
    success = await block_user(tg_id, user_id, reason)
    
    # Завершаем FSM
    await state.finish()
    
    # Сообщаем о результате
    lang = await get_user_language(tg_id)
    
    if success:
        texts = {
            "ua": "✅ Користувач заблокований.",
            "ru": "✅ Пользователь заблокирован.",
            "en": "✅ User has been blocked.",
            "de": "✅ Benutzer wurde blockiert."
        }
    else:
        texts = {
            "ua": "❌ Не вдалося заблокувати користувача.",
            "ru": "❌ Не удалось заблокировать пользователя.",
            "en": "❌ Failed to block user.",
            "de": "❌ Benutzer konnte nicht blockiert werden."
        }
    
    # Import keyboard for main menu
    from app.keyboards.main_menu import get_main_menu
    main_menu = get_main_menu(lang)
    
    await message.answer(texts.get(lang, texts["ua"]), reply_markup=main_menu)

# Обработчик команды /skip при вводе причины блокировки
async def skip_block_reason(message: types.Message, state: FSMContext):
    # Вызываем тот же обработчик, но с пустым сообщением
    message.text = None
    await process_block_reason(message, state)

# Обработчик для разблокировки пользователя
async def unblock_user_callback(callback_query: types.CallbackQuery):
    data = callback_query.data
    if not data.startswith("unblock_"):
        return
    
    # Получаем ID пользователя для разблокировки
    user_id = int(data.split("_")[1])
    
    # Разблокируем пользователя
    tg_id = str(callback_query.from_user.id)
    success = await unblock_user(tg_id, user_id)
    
    # Сообщаем о результате
    lang = await get_user_language(tg_id)
    
    if success:
        texts = {
            "ua": "✅ Користувач розблокований.",
            "ru": "✅ Пользователь разблокирован.",
            "en": "✅ User has been unblocked.",
            "de": "✅ Benutzer wurde entsperrt."
        }
    else:
        texts = {
            "ua": "❌ Не вдалося розблокувати користувача.",
            "ru": "❌ Не удалось разблокировать пользователя.",
            "en": "❌ Failed to unblock user.",
            "de": "❌ Benutzer konnte nicht entsperrt werden."
        }
    
    await callback_query.message.answer(texts.get(lang, texts["ua"]))
    
    # Обновляем список заблокированных пользователей
    await cmd_block_list(callback_query.message)
    
    # Отвечаем на callback чтобы убрать часики
    await callback_query.answer()

# Регистрация всех обработчиков
def register_block_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_block_list, commands=["block", "blocked"])
    dp.register_callback_query_handler(block_user_callback, lambda c: c.data and c.data.startswith("block_"))
    dp.register_callback_query_handler(unblock_user_callback, lambda c: c.data and c.data.startswith("unblock_"))
    dp.register_message_handler(skip_block_reason, commands=["skip"], state=BlockState.waiting_for_reason)
    dp.register_message_handler(process_block_reason, state=BlockState.waiting_for_reason)
