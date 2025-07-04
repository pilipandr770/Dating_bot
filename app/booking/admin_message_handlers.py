# app/booking/admin_message_handlers.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging

from app.database import get_session
from app.booking.models import PlaceType
from app.booking.services_admin_message import AdminMessageService

# Настройка логирования
logger = logging.getLogger(__name__)

# Состояния для пошагового добавления сообщения администратора
class AdminMessageDialog(StatesGroup):
    waiting_for_city = State()
    waiting_for_place_type = State()
    waiting_for_message = State()
    confirm_add = State()

# Проверка прав администратора (пример, можно заменить на вашу логику)
async def check_admin_rights(user_id: int) -> bool:
    # В реальном приложении здесь должна быть проверка прав админа
    # Например, проверка ID пользователя в базе данных или в конфиге
    admin_ids = [7444992311, 123456789]  # Список ID администраторов
    return user_id in admin_ids

# Команда для запуска диалога добавления сообщения администратора
async def cmd_add_admin_message(message: types.Message, state: FSMContext):
    """Запускает диалог добавления нового админского сообщения"""
    # Проверка прав администратора
    is_admin = await check_admin_rights(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await state.finish()
    
    # Запрашиваем город
    await message.answer(
        "🏙 Шаг 1/3: Введите название города, для которого добавляется сообщение:"
    )
    await AdminMessageDialog.waiting_for_city.set()

# Обработчик ввода города
async def process_city_input(message: types.Message, state: FSMContext):
    """Обрабатывает ввод города для админского сообщения"""
    city = message.text.strip()
    
    # Сохраняем город в состоянии
    await state.update_data(city=city)
    
    # Создаем клавиатуру с типами заведений
    markup = InlineKeyboardMarkup(row_width=2)
    
    for place_type in PlaceType:
        markup.add(InlineKeyboardButton(
            text=place_type.value.capitalize(),
            callback_data=f"admin_msg_type_{place_type.value}"
        ))
    
    await message.answer(
        f"🏙 Город: *{city}*\n\n🔍 Шаг 2/3: Выберите тип заведения:",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    
    await AdminMessageDialog.waiting_for_place_type.set()

# Обработчик выбора типа заведения
async def process_place_type_selection(call: types.CallbackQuery, state: FSMContext):
    """Обрабатывает выбор типа заведения для админского сообщения"""
    await call.answer()
    
    # Извлекаем тип заведения из callback_data
    place_type = call.data.replace("admin_msg_type_", "")
    
    # Сохраняем тип заведения в состоянии
    await state.update_data(place_type=place_type)
    
    # Получаем данные из состояния
    user_data = await state.get_data()
    city = user_data.get("city")
    
    await call.message.edit_text(
        f"🏙 Город: *{city}*\n📍 Тип: *{place_type}*\n\n✏️ Шаг 3/3: Введите сообщение администратора:",
        parse_mode="Markdown"
    )
    
    await AdminMessageDialog.waiting_for_message.set()

# Обработчик ввода сообщения администратора
async def process_admin_message_input(message: types.Message, state: FSMContext):
    """Обрабатывает ввод текста сообщения администратора"""
    admin_message = message.text.strip()
    
    # Сохраняем сообщение в состоянии
    await state.update_data(message=admin_message)
    
    # Получаем данные из состояния
    user_data = await state.get_data()
    city = user_data.get("city")
    place_type = user_data.get("place_type")
    
    # Создаем клавиатуру для подтверждения
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Сохранить", callback_data="admin_msg_confirm"),
        InlineKeyboardButton("❌ Отмена", callback_data="admin_msg_cancel")
    )
    
    await message.answer(
        f"📝 Проверьте данные:\n\n"
        f"🏙 Город: *{city}*\n"
        f"📍 Тип: *{place_type}*\n"
        f"✉️ Сообщение: {admin_message}\n\n"
        f"Сохранить сообщение администратора?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    
    await AdminMessageDialog.confirm_add.set()

# Обработчик подтверждения добавления сообщения администратора
async def process_confirm_admin_message(call: types.CallbackQuery, state: FSMContext):
    """Обрабатывает подтверждение добавления сообщения администратора"""
    await call.answer()
    
    if call.data == "admin_msg_cancel":
        await call.message.edit_text("❌ Добавление сообщения администратора отменено.")
        await state.finish()
        return
    
    # Получаем данные из состояния
    user_data = await state.get_data()
    city = user_data.get("city")
    place_type = user_data.get("place_type")
    admin_message = user_data.get("message")
    
    try:
        async for session in get_session():
            # Добавляем сообщение администратора
            result = await AdminMessageService.add_admin_message(
                session=session,
                city=city,
                place_type=place_type,
                message=admin_message
            )
            
            if result:
                await call.message.edit_text(
                    f"✅ Сообщение администратора успешно сохранено!\n\n"
                    f"🏙 Город: *{city}*\n"
                    f"📍 Тип: *{place_type}*\n"
                    f"✉️ Сообщение: {admin_message}",
                    parse_mode="Markdown"
                )
            else:
                await call.message.edit_text("❌ Не удалось сохранить сообщение администратора. Попробуйте снова позже.")
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении сообщения администратора: {e}")
        await call.message.edit_text(f"❌ Произошла ошибка при сохранении данных: {str(e)}")
    
    await state.finish()

# Команда для просмотра всех сообщений администратора
async def cmd_list_admin_messages(message: types.Message):
    """Показывает список всех сообщений администратора"""
    # Проверка прав администратора
    is_admin = await check_admin_rights(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    try:
        async for session in get_session():
            admin_messages = await AdminMessageService.list_admin_messages(session)
            
            if not admin_messages:
                await message.answer("📝 Сообщения администратора не найдены.")
                return
            
            # Формируем сообщение со списком админских сообщений
            response = "📝 Список сообщений администратора:\n\n"
            
            for idx, msg in enumerate(admin_messages, start=1):
                response += (
                    f"{idx}. ID: {msg['id']}\n"
                    f"   🏙 Город: {msg['city']}\n"
                    f"   📍 Тип: {msg['place_type']}\n"
                    f"   ✉️ Сообщение: {msg['message']}\n\n"
                )
            
            await message.answer(response)
    
    except Exception as e:
        logger.error(f"Ошибка при получении списка сообщений администратора: {e}")
        await message.answer("❌ Произошла ошибка при получении списка сообщений администратора.")

# Команда для удаления сообщения администратора по ID
async def cmd_delete_admin_message(message: types.Message):
    """Удаляет сообщение администратора по ID"""
    # Проверка прав администратора
    is_admin = await check_admin_rights(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    # Получаем ID сообщения из команды
    command_args = message.get_args()
    
    if not command_args or not command_args.isdigit():
        await message.answer(
            "ℹ️ Укажите ID сообщения для удаления.\n"
            "Пример: /delete_admin_message 1"
        )
        return
    
    message_id = int(command_args)
    
    try:
        async for session in get_session():
            result = await AdminMessageService.delete_admin_message(session, message_id)
            
            if result:
                await message.answer(f"✅ Сообщение администратора с ID {message_id} успешно удалено.")
            else:
                await message.answer(f"❌ Сообщение администратора с ID {message_id} не найдено.")
    
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения администратора: {e}")
        await message.answer("❌ Произошла ошибка при удалении сообщения администратора.")

# Регистрация обработчиков
def register_admin_message_handlers(dp: Dispatcher):
    # Команды
    dp.register_message_handler(cmd_add_admin_message, commands=["add_admin_message"])
    dp.register_message_handler(cmd_list_admin_messages, commands=["list_admin_messages"])
    dp.register_message_handler(cmd_delete_admin_message, commands=["delete_admin_message"])
    
    # Диалог добавления сообщения администратора
    dp.register_message_handler(process_city_input, state=AdminMessageDialog.waiting_for_city)
    dp.register_callback_query_handler(process_place_type_selection, lambda c: c.data.startswith("admin_msg_type_"), state=AdminMessageDialog.waiting_for_place_type)
    dp.register_message_handler(process_admin_message_input, state=AdminMessageDialog.waiting_for_message)
    dp.register_callback_query_handler(process_confirm_admin_message, lambda c: c.data.startswith("admin_msg_"), state=AdminMessageDialog.confirm_add)
