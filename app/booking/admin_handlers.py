# app/booking/admin_handlers.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import json
from app.database import get_session
from app.booking.models import PlaceType
from app.booking.services_db import VenueService

# Настройка логирования
logger = logging.getLogger(__name__)

# Состояния для админки заведений
class AdminVenueStates(StatesGroup):
    waiting_for_venue_data = State()
    confirm_add = State()
    confirm_edit = State()
    confirm_delete = State()
    waiting_for_admin_message = State()

# Команда для добавления нового заведения
async def cmd_admin_add_venue(message: types.Message, state: FSMContext):
    """Обработчик команды для добавления нового заведения"""
    # Проверяем, является ли пользователь администратором
    # Здесь должна быть ваша логика проверки прав администратора
    is_admin = await check_admin_rights(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await state.finish()
    
    # Отправляем инструкции по формату данных
    instructions = (
        "Для добавления нового заведения отправьте данные в формате JSON:\n\n"
        "```json\n"
        "{\n"
        '  "name": "Название заведения",\n'
        '  "type": "restaurant",  // restaurant, cafe, bar, park, cinema, event или other\n'
        '  "city": "Название города",\n'
        '  "url": "https://example.com",  // необязательно\n'
        '  "description": "Описание заведения",  // необязательно\n'
        '  "address": "Адрес заведения",  // необязательно\n'
        '  "admin_message": "Сообщение от администратора"  // необязательно\n'
        "}\n"
        "```\n\n"
        "Поля name, type и city являются обязательными."
    )
    
    await message.answer(instructions, parse_mode="Markdown")
    await AdminVenueStates.waiting_for_venue_data.set()

# Обработчик для получения данных о заведении
async def process_venue_data(message: types.Message, state: FSMContext):
    """Обрабатывает данные о заведении в формате JSON"""
    try:
        # Пытаемся распарсить JSON
        try:
            venue_data = json.loads(message.text)
        except json.JSONDecodeError:
            await message.answer("❌ Неверный формат JSON. Пожалуйста, проверьте данные и попробуйте снова.")
            return
        
        # Проверяем обязательные поля
        required_fields = ["name", "type", "city"]
        missing_fields = [field for field in required_fields if field not in venue_data]
        
        if missing_fields:
            await message.answer(f"❌ Отсутствуют обязательные поля: {', '.join(missing_fields)}")
            return
        
        # Проверяем тип места
        try:
            place_type = PlaceType(venue_data["type"])
        except ValueError:
            valid_types = [t.value for t in PlaceType]
            await message.answer(f"❌ Неверный тип заведения. Допустимые типы: {', '.join(valid_types)}")
            return
        
        # Сохраняем данные в состоянии
        await state.update_data(venue_data=venue_data)
        
        # Отправляем подтверждение
        confirmation_text = (
            f"📋 Проверьте данные заведения:\n\n"
            f"🏢 Название: {venue_data['name']}\n"
            f"🔖 Тип: {place_type.value}\n"
            f"🏙 Город: {venue_data['city']}\n"
        )
        
        if "url" in venue_data:
            confirmation_text += f"🔗 URL: {venue_data['url']}\n"
        if "address" in venue_data:
            confirmation_text += f"📍 Адрес: {venue_data['address']}\n"
        if "description" in venue_data:
            confirmation_text += f"📝 Описание: {venue_data['description']}\n"
        if "admin_message" in venue_data:
            confirmation_text += f"ℹ️ Сообщение от администратора: {venue_data['admin_message']}\n"
        
        # Создаем клавиатуру для подтверждения
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Подтвердить", callback_data="admin:venue:confirm_add"),
            InlineKeyboardButton("❌ Отмена", callback_data="admin:venue:cancel")
        )
        
        await message.answer(confirmation_text, reply_markup=kb)
        await AdminVenueStates.confirm_add.set()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке данных заведения: {e}")
        await message.answer("❌ Произошла ошибка при обработке данных. Пожалуйста, попробуйте снова.")

# Обработчик подтверждения добавления заведения
async def confirm_add_venue(call: types.CallbackQuery, state: FSMContext):
    """Обрабатывает подтверждение добавления заведения"""
    await call.answer()
    
    # Получаем данные из состояния
    data = await state.get_data()
    venue_data = data.get("venue_data", {})
    
    if not venue_data:
        await call.message.answer("❌ Данные о заведении не найдены. Попробуйте снова.")
        await state.finish()
        return
    
    # Добавляем заведение в базу данных
    try:
        async for session in get_session():
            place_type = PlaceType(venue_data["type"])
            
            result = await VenueService.add_venue(
                session=session,
                name=venue_data["name"],
                place_type=place_type,
                city=venue_data["city"],
                url=venue_data.get("url"),
                description=venue_data.get("description"),
                address=venue_data.get("address"),
                admin_message=venue_data.get("admin_message"),
                is_active=True
            )
            
            if result:
                await call.message.edit_text(
                    f"✅ Заведение успешно добавлено!\n\n"
                    f"🏢 {result.name}\n"
                    f"🏙 {result.city}\n"
                    f"🆔 ID: {result.id}"
                )
            else:
                await call.message.edit_text("❌ Не удалось добавить заведение. Попробуйте снова позже.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении заведения в БД: {e}")
        await call.message.edit_text("❌ Произошла ошибка при сохранении данных. Пожалуйста, попробуйте снова позже.")
    
    await state.finish()

# Обработчик отмены добавления заведения
async def cancel_venue_action(call: types.CallbackQuery, state: FSMContext):
    """Обрабатывает отмену действия с заведением"""
    await call.answer()
    await call.message.edit_text("❌ Действие отменено.")
    await state.finish()

# Функция для проверки прав администратора
async def check_admin_rights(telegram_id):
    """Проверяет, является ли пользователь администратором"""
    # Здесь должна быть ваша логика проверки прав администратора
    # Например, проверка ID в списке админов или запрос к БД
    # Для демонстрации возвращаем True
    return True

def register_admin_venue_handlers(dp: Dispatcher):
    """Регистрирует обработчики для админки заведений"""
    # Команда для добавления нового заведения
    dp.register_message_handler(cmd_admin_add_venue, commands=["add_venue"], state="*")
    
    # Обработчик для получения данных о заведении
    dp.register_message_handler(process_venue_data, state=AdminVenueStates.waiting_for_venue_data)
    
    # Обработчики подтверждения действий
    dp.register_callback_query_handler(
        confirm_add_venue, 
        lambda c: c.data == "admin:venue:confirm_add", 
        state=AdminVenueStates.confirm_add
    )
    
    # Обработчик отмены
    dp.register_callback_query_handler(
        cancel_venue_action, 
        lambda c: c.data == "admin:venue:cancel", 
        state="*"
    )
