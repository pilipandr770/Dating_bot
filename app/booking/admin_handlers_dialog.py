# app/booking/admin_handlers_dialog.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from sqlalchemy import select

from app.database import get_session
from app.booking.models import PlaceType, Place
from app.booking.services_db import VenueService

# Настройка логирования
logger = logging.getLogger(__name__)

# Состояния для пошагового добавления заведения
class AdminVenueDialog(StatesGroup):
    waiting_for_city = State()
    waiting_for_place_type = State()
    waiting_for_name = State()
    waiting_for_url = State()
    # waiting_for_address = State()  # Убрано, т.к. поле не существует в БД
    waiting_for_description = State()
    waiting_for_admin_message = State()
    confirm_add = State()
    
# Состояния для редактирования заведения
class AdminVenueEditDialog(StatesGroup):
    waiting_for_city = State()
    waiting_for_place_type = State()
    selecting_venue = State()
    editing_field = State()
    waiting_for_new_value = State()
    confirm_edit = State()

# Команда для запуска пошагового добавления заведения
async def cmd_add_venue(message: types.Message, state: FSMContext):
    """Запускает диалог добавления нового заведения"""
    # Проверка прав администратора
    is_admin = await check_admin_rights(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await state.finish()
    
    # Запрашиваем город
    await message.answer(
        "🏙 Шаг 1/6: Введите название города, для которого добавляется заведение:"
    )
    await AdminVenueDialog.waiting_for_city.set()

# Обработчик ввода города
async def process_venue_city(message: types.Message, state: FSMContext):
    """Обработка ввода города"""
    city = message.text.strip()
    
    if not city:
        await message.answer("❌ Название города не может быть пустым. Пожалуйста, введите название города:")
        return
    
    # Сохраняем город в состоянии
    await state.update_data(city=city)
    
    # Предлагаем выбрать тип заведения
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    for place_type in PlaceType:
        markup.insert(KeyboardButton(place_type.value))
    
    await message.answer(
        f"🔖 Шаг 2/6: Выберите тип заведения для города {city}:",
        reply_markup=markup
    )
    await AdminVenueDialog.waiting_for_place_type.set()

# Обработчик выбора типа заведения
async def process_venue_type(message: types.Message, state: FSMContext):
    """Обработка выбора типа заведения"""
    place_type = message.text.strip().lower()
    
    # Проверяем, является ли выбранный тип допустимым
    valid_types = [t.value for t in PlaceType]
    
    if place_type not in valid_types:
        types_list = ", ".join(valid_types)
        await message.answer(f"❌ Неверный тип заведения. Выберите один из предложенных вариантов: {types_list}")
        return
    
    # Сохраняем тип в состоянии
    await state.update_data(place_type=place_type)
    
    # Запрашиваем название заведения
    await message.answer(
        "🏢 Шаг 3/7: Введите название заведения:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await AdminVenueDialog.waiting_for_name.set()

# Обработчик ввода названия заведения
async def process_venue_name(message: types.Message, state: FSMContext):
    """Обработка ввода названия заведения"""
    name = message.text.strip()
    
    if not name:
        await message.answer("❌ Название заведения не может быть пустым. Пожалуйста, введите название:")
        return
    
    # Сохраняем название в состоянии
    await state.update_data(name=name)
    
    # Запрашиваем URL заведения
    await message.answer(
        "🔗 Шаг 4/7: Введите URL сайта заведения (или '-' если нет):"
    )
    await AdminVenueDialog.waiting_for_url.set()

# Обработчик ввода URL
async def process_venue_url(message: types.Message, state: FSMContext):
    """Обработка ввода URL заведения"""
    url = message.text.strip()
    
    # Если пользователь отправил "-", считаем что URL нет
    if url == "-":
        url = None
    
    # Сохраняем URL в состоянии
    await state.update_data(url=url)
    
    # Запрашиваем описание заведения (пропускаем шаг с адресом, так как его нет в БД)
    await message.answer(
        "� Шаг 5/7: Введите описание заведения (или '-' если хотите пропустить):"
    )
    await AdminVenueDialog.waiting_for_description.set()

# Обработчик ввода адреса - оставляем для совместимости, но не используем
async def process_venue_address(message: types.Message, state: FSMContext):
    """Обработка ввода адреса заведения - этот метод не используется"""
    pass

# Обработчик ввода описания
async def process_venue_description(message: types.Message, state: FSMContext):
    """Обработка ввода описания заведения"""
    description = message.text.strip()
    
    # Если пользователь отправил "-", считаем что описания нет
    if description == "-":
        description = None
    
    # Сохраняем описание в состоянии
    await state.update_data(description=description)
    
    # Запрашиваем сообщение от администратора
    await message.answer(
        "ℹ️ Шаг 6/7: Введите сообщение от администратора (акции, скидки и т.д.) или '-' если нет:"
    )
    await AdminVenueDialog.waiting_for_admin_message.set()

# Обработчик ввода админского сообщения
async def process_venue_admin_message(message: types.Message, state: FSMContext):
    """Обработка ввода сообщения от администратора"""
    admin_message = message.text.strip()
    
    # Если пользователь отправил "-", считаем что сообщения нет
    if admin_message == "-":
        admin_message = None
    
    # Сохраняем сообщение в состоянии
    await state.update_data(admin_message=admin_message)
    
    # Получаем все данные и показываем для подтверждения
    data = await state.get_data()
    
    confirmation_text = (
        f"📋 Проверьте данные заведения:\n\n"
        f"🏙 Город: {data['city']}\n"
        f"🔖 Тип: {data['place_type']}\n"
        f"🏢 Название: {data['name']}\n"
    )
    
    if data.get('url'):
        confirmation_text += f"🔗 URL: {data['url']}\n"
    if data.get('description'):
        confirmation_text += f"� Описание: {data['description']}\n"
    if data.get('admin_message'):
        confirmation_text += f"ℹ️ Сообщение от администратора: {data['admin_message']}\n"
        confirmation_text += f"✅ Сообщение будет сохранено в базе данных для всех заведений этого типа в выбранном городе\n"
    
    # Клавиатура для подтверждения
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data="admin:venue:confirm_add"),
        InlineKeyboardButton("❌ Отменить", callback_data="admin:venue:cancel")
    )
    
    await message.answer(confirmation_text, reply_markup=markup)
    await AdminVenueDialog.confirm_add.set()

# Обработчик подтверждения добавления заведения
async def confirm_add_venue(call: types.CallbackQuery, state: FSMContext):
    """Обработка подтверждения добавления заведения"""
    await call.answer()
    
    # Получаем все данные из состояния
    data = await state.get_data()
    
    try:
        # Добавляем заведение в базу данных
        async for session in get_session():
            # Отладка: запрашиваем структуру таблицы перед добавлением
            await VenueService.debug_db_schema(session, "dating_bot.places")
            
            # Используем строковый тип, а не Enum
            place_type = data['place_type']
            
            # Преобразуем URL в link
            url = data.get('url')
            
            # Координаты пока не заполняем (можно добавить их запрос в будущем)
            coordinates = None
            
            result = await VenueService.add_venue(
                session=session,
                name=data['name'],
                place_type=place_type,
                city=data['city'],
                url=url,
                description=data.get('description'),
                admin_message=data.get('admin_message'),  # Будет сохранено в логах
                coordinates=coordinates
            )
            
            if result:
                success_message = (
                    f"✅ Заведение успешно добавлено!\n\n"
                    f"🏢 {result.name}\n"
                    f"🏙 {result.city}\n"
                    f"🔖 Тип: {result.type}\n"
                )
                
                # Добавляем ссылку, если она есть
                if hasattr(result, 'link') and result.link:
                    success_message += f"🔗 Ссылка: {result.link}\n"
                
                success_message += f"🆔 ID: {result.id}"
                
                # Если было админское сообщение, сообщаем что оно сохранено в базе данных
                if data.get('admin_message'):
                    success_message += f"\n\n📝 Администраторское сообщение сохранено в базе данных."
                
                await call.message.edit_text(success_message)
            else:
                await call.message.edit_text("❌ Не удалось добавить заведение. Попробуйте снова позже.")
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении заведения: {e}")
        await call.message.edit_text(f"❌ Произошла ошибка при сохранении данных: {str(e)}")
    
    await state.finish()

# Команда для редактирования заведения
async def cmd_edit_venue(message: types.Message, state: FSMContext):
    """Запускает диалог редактирования заведения"""
    # Проверка прав администратора
    is_admin = await check_admin_rights(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await state.finish()
    
    # Запрашиваем город для фильтрации заведений
    await message.answer("🏙 Введите название города для поиска заведений:")
    await AdminVenueEditDialog.waiting_for_city.set()

# Команда для просмотра заведений в городе
async def cmd_list_venues(message: types.Message):
    """Показывает список заведений в городе"""
    # Проверка прав администратора
    is_admin = await check_admin_rights(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    # Получаем аргументы команды
    command_args = message.get_args()
    
    if not command_args:
        await message.answer(
            "ℹ️ Укажите название города для поиска заведений.\n"
            "Пример: /list_venues Франкфурт"
        )
        return
    
    city = command_args.strip()
    
    try:
        async for session in get_session():
            # Запрашиваем структуру таблицы для отладки
            await VenueService.debug_db_schema(session, "dating_bot.places")
            
            # Создаем запрос на получение всех заведений в указанном городе
            query = select(Place).where(Place.city.ilike(f"%{city}%"))
            result = await session.execute(query)
            places = result.scalars().all()
            
            if not places:
                await message.answer(f"🔍 Заведения в городе '{city}' не найдены.")
                return
            
            # Формируем список заведений
            response = f"📍 Найдено заведений в городе '{city}': {len(places)}\n\n"
            
            for place in places:
                response += f"🏢 {place.name}\n"
                response += f"🔖 Тип: {place.type}\n"
                
                if place.link:
                    response += f"🔗 Ссылка: {place.link}\n"
                
                if place.latitude and place.longitude:
                    response += f"📍 Координаты: {place.latitude}, {place.longitude}\n"
                
                response += f"🆔 ID: {place.id}\n\n"
                
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка при получении списка заведений: {e}")
        await message.answer(f"❌ Произошла ошибка при получении списка заведений: {str(e)}")

# Обработчик отмены действия
async def cancel_venue_action(call: types.CallbackQuery, state: FSMContext):
    """Обрабатывает отмену действия с заведением"""
    await call.answer()
    await call.message.edit_text("❌ Действие отменено.")
    await state.finish()

# Функция для проверки прав администратора
async def check_admin_rights(telegram_id):
    """Проверяет, является ли пользователь администратором"""
    # В реальном приложении здесь должна быть проверка в базе данных
    # Для демонстрации возвращаем True для всех пользователей
    return True

def register_admin_venue_dialog_handlers(dp: Dispatcher):
    """Регистрирует обработчики для пошагового диалога управления заведениями"""
    # Команды для управления заведениями
    dp.register_message_handler(cmd_add_venue, commands=["add_venue"], state="*")
    dp.register_message_handler(cmd_edit_venue, commands=["edit_venue"], state="*")
    dp.register_message_handler(cmd_list_venues, commands=["list_venues"], state="*")
    
    # Обработчики шагов добавления заведения
    dp.register_message_handler(process_venue_city, state=AdminVenueDialog.waiting_for_city)
    dp.register_message_handler(process_venue_type, state=AdminVenueDialog.waiting_for_place_type)
    dp.register_message_handler(process_venue_name, state=AdminVenueDialog.waiting_for_name)
    dp.register_message_handler(process_venue_url, state=AdminVenueDialog.waiting_for_url)
    # dp.register_message_handler(process_venue_address, state=AdminVenueDialog.waiting_for_address)  # Убрано
    dp.register_message_handler(process_venue_description, state=AdminVenueDialog.waiting_for_description)
    dp.register_message_handler(process_venue_admin_message, state=AdminVenueDialog.waiting_for_admin_message)
    
    # Обработчики подтверждения действий
    dp.register_callback_query_handler(
        confirm_add_venue, 
        lambda c: c.data == "admin:venue:confirm_add", 
        state=AdminVenueDialog.confirm_add
    )
    
    # Обработчик отмены
    dp.register_callback_query_handler(
        cancel_venue_action, 
        lambda c: c.data == "admin:venue:cancel", 
        state="*"
    )
