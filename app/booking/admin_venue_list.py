# app/booking/admin_venue_list.py

from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

from app.database import get_session
from app.services.user_service import get_user_language
from app.booking.services_db import VenueService

# Настройка логирования
logger = logging.getLogger(__name__)

async def cmd_list_venues(message: types.Message):
    """Команда для просмотра всех заведений в базе данных (для админа)"""
    telegram_id = str(message.from_user.id)
    
    # Проверяем права администратора (можно доработать)
    is_admin = True  # TODO: добавить проверку прав администратора
    
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    try:
        # Получаем все заведения из базы данных
        async for session in get_session():
            # Отладка: запрашиваем структуру таблицы
            await VenueService.debug_db_schema(session, "dating_bot.places")
            
            # Запрашиваем все заведения из БД
            result = await session.execute("SELECT id, name, type, city, link FROM dating_bot.places")
            venues = result.fetchall()
            
            if not venues:
                await message.answer("📊 В базе данных нет заведений.")
                return
            
            # Выводим информацию по всем заведениям
            response = "📊 Список всех заведений в базе данных:\n\n"
            
            for venue in venues:
                venue_id, name, venue_type, city, link = venue
                response += f"🆔 {venue_id} | 🏢 {name}\n"
                response += f"🏙 Город: {city or 'Не указан'}\n"
                response += f"🔖 Тип: {venue_type or 'Не указан'}\n"
                if link:
                    response += f"🔗 Ссылка: {link}\n"
                response += "---------------------\n\n"
            
            # Отправляем сообщение
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка при получении списка заведений: {e}")
        await message.answer(f"❌ Ошибка при получении списка заведений: {str(e)}")

def register_admin_venue_list_handlers(dp: Dispatcher):
    """Регистрирует обработчики для списка заведений"""
    dp.register_message_handler(cmd_list_venues, commands=["list_venues"])
