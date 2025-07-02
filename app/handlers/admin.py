# файл: app/handlers/admin.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.services.token_service import approve_withdrawal, reject_withdrawal
from app.models.token_withdrawals import TokenWithdrawal
from app.database import get_session
from sqlalchemy import select, and_
import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка ID администраторов
load_dotenv()
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

# Состояния для админских операций
class AdminStates(StatesGroup):
    waiting_for_withdrawal_action = State()  # Ожидание действия с заявкой

# Проверка, является ли пользователь администратором
def is_admin(telegram_id: str) -> bool:
    return telegram_id in ADMIN_IDS

# Обработчик команды /admin - показать админское меню
async def cmd_admin(message: types.Message):
    telegram_id = str(message.from_user.id)
    
    if not is_admin(telegram_id):
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📊 Статистика пользователей", callback_data="admin_stats"),
        InlineKeyboardButton("💸 Заявки на вывод", callback_data="admin_withdrawals"),
        InlineKeyboardButton("🔄 Обновить бота", callback_data="admin_update_bot")
    )
    
    await message.answer("👨‍💻 Панель администратора", reply_markup=markup)

# Обработчик для просмотра заявок на вывод
async def on_admin_withdrawals(callback_query: types.CallbackQuery):
    telegram_id = str(callback_query.from_user.id)
    
    if not is_admin(telegram_id):
        await callback_query.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    # Получаем все ожидающие заявки
    async for session in get_session():
        try:
            withdrawals = await session.scalars(
                select(TokenWithdrawal)
                .where(TokenWithdrawal.status == "pending")
                .order_by(TokenWithdrawal.timestamp)
            )
            
            withdrawals_list = list(withdrawals)
            
            if not withdrawals_list:
                await callback_query.message.edit_text("✅ Нет ожидающих заявок на вывод.")
                await callback_query.answer()
                return
            
            # Получаем информацию о пользователях
            from app.models.user import User
            
            response = "📝 Заявки на вывод токенов:\n\n"
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup(row_width=2)
            
            for withdrawal in withdrawals_list:
                user = await session.scalar(select(User).where(User.id == withdrawal.user_id))
                username = user.username if user and user.username else "Unknown"
                
                response += f"ID: {withdrawal.id}\n"
                response += f"User: {username} (ID: {withdrawal.user_id})\n"
                response += f"Amount: {withdrawal.token_amount} tokens\n"
                response += f"Date: {withdrawal.timestamp}\n\n"
                
                markup.add(
                    InlineKeyboardButton(f"✅ Approve #{withdrawal.id}", callback_data=f"admin_approve_{withdrawal.id}"),
                    InlineKeyboardButton(f"❌ Reject #{withdrawal.id}", callback_data=f"admin_reject_{withdrawal.id}")
                )
            
            markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin_back"))
            
            await callback_query.message.edit_text(response, reply_markup=markup)
            await callback_query.answer()
        
        except Exception as e:
            logger.error(f"Ошибка при получении заявок на вывод: {str(e)}")
            await callback_query.message.edit_text("❌ Ошибка при получении заявок на вывод.")
            await callback_query.answer()

# Обработчик для одобрения заявки на вывод
async def on_admin_approve_withdrawal(callback_query: types.CallbackQuery):
    telegram_id = str(callback_query.from_user.id)
    
    if not is_admin(telegram_id):
        await callback_query.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    withdrawal_id = int(callback_query.data.split('_')[2])
    
    success = await approve_withdrawal(withdrawal_id)
    
    if success:
        await callback_query.message.edit_text(f"✅ Заявка #{withdrawal_id} успешно одобрена.")
    else:
        await callback_query.message.edit_text(f"❌ Ошибка при одобрении заявки #{withdrawal_id}.")
    
    await callback_query.answer()

# Обработчик для отклонения заявки на вывод
async def on_admin_reject_withdrawal(callback_query: types.CallbackQuery):
    telegram_id = str(callback_query.from_user.id)
    
    if not is_admin(telegram_id):
        await callback_query.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    withdrawal_id = int(callback_query.data.split('_')[2])
    
    success = await reject_withdrawal(withdrawal_id)
    
    if success:
        await callback_query.message.edit_text(f"✅ Заявка #{withdrawal_id} отклонена. Токены возвращены пользователю.")
    else:
        await callback_query.message.edit_text(f"❌ Ошибка при отклонении заявки #{withdrawal_id}.")
    
    await callback_query.answer()

# Обработчик для возврата к админскому меню
async def on_admin_back(callback_query: types.CallbackQuery):
    telegram_id = str(callback_query.from_user.id)
    
    if not is_admin(telegram_id):
        await callback_query.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📊 Статистика пользователей", callback_data="admin_stats"),
        InlineKeyboardButton("💸 Заявки на вывод", callback_data="admin_withdrawals"),
        InlineKeyboardButton("🔄 Обновить бота", callback_data="admin_update_bot")
    )
    
    await callback_query.message.edit_text("👨‍💻 Панель администратора", reply_markup=markup)
    await callback_query.answer()

# Обработчик команды для быстрой обработки заявки
async def cmd_admin_withdrawal(message: types.Message):
    telegram_id = str(message.from_user.id)
    
    if not is_admin(telegram_id):
        return
    
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("❌ Неверный формат команды. Используйте: /admin_withdrawal <id> <approve/reject>")
        return
    
    try:
        withdrawal_id = int(parts[1])
        action = parts[2].lower()
        
        if action == "approve":
            success = await approve_withdrawal(withdrawal_id)
            if success:
                await message.answer(f"✅ Заявка #{withdrawal_id} успешно одобрена.")
            else:
                await message.answer(f"❌ Ошибка при одобрении заявки #{withdrawal_id}.")
        elif action == "reject":
            success = await reject_withdrawal(withdrawal_id)
            if success:
                await message.answer(f"✅ Заявка #{withdrawal_id} отклонена. Токены возвращены пользователю.")
            else:
                await message.answer(f"❌ Ошибка при отклонении заявки #{withdrawal_id}.")
        else:
            await message.answer("❌ Неверное действие. Используйте 'approve' или 'reject'.")
    except ValueError:
        await message.answer("❌ ID заявки должен быть числом.")
    except Exception as e:
        logger.error(f"Ошибка при обработке заявки: {str(e)}")
        await message.answer(f"❌ Ошибка при обработке заявки: {str(e)}")

# Регистрация обработчиков
def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands="admin", state="*")
    dp.register_message_handler(cmd_admin_withdrawal, commands="admin_withdrawal", state="*")
    
    dp.register_callback_query_handler(on_admin_withdrawals, lambda c: c.data == "admin_withdrawals", state="*")
    dp.register_callback_query_handler(on_admin_approve_withdrawal, lambda c: c.data.startswith("admin_approve_"), state="*")
    dp.register_callback_query_handler(on_admin_reject_withdrawal, lambda c: c.data.startswith("admin_reject_"), state="*")
    dp.register_callback_query_handler(on_admin_back, lambda c: c.data == "admin_back", state="*")
