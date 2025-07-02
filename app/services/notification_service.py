# файл: app/services/notification_service.py

from app.database import get_session
from app.models.user import User
from sqlalchemy import select
from aiogram import Bot
import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка API токена бота
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

async def notify_user(telegram_id: str, message: str):
    """
    Отправить уведомление пользователю по его Telegram ID
    """
    try:
        await bot.send_message(chat_id=telegram_id, text=message)
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления пользователю {telegram_id}: {str(e)}")
        return False

async def notify_withdrawal_status(withdrawal_id: int, status: str):
    """
    Отправить уведомление о статусе заявки на вывод токенов
    """
    async for session in get_session():
        try:
            # Получаем данные о заявке и пользователе
            from app.models.token_withdrawals import TokenWithdrawal
            
            # Получаем заявку
            withdrawal = await session.scalar(
                select(TokenWithdrawal).where(TokenWithdrawal.id == withdrawal_id)
            )
            if not withdrawal:
                logger.error(f"Заявка на вывод с ID {withdrawal_id} не найдена")
                return False
                
            # Получаем пользователя
            user = await session.scalar(
                select(User).where(User.id == withdrawal.user_id)
            )
            if not user or not user.telegram_id:
                logger.error(f"Пользователь не найден для заявки {withdrawal_id}")
                return False
            
            # Получаем язык пользователя
            lang = user.language or "en"
            
            # Формируем сообщение в зависимости от статуса и языка
            messages = {
                "approved": {
                    "ua": f"✅ Ваша заявка на виведення {withdrawal.token_amount} токенів була схвалена! Кошти будуть перераховані на вашу платіжну карту протягом 1-3 робочих днів.",
                    "ru": f"✅ Ваша заявка на вывод {withdrawal.token_amount} токенов одобрена! Средства будут перечислены на вашу платежную карту в течение 1-3 рабочих дней.",
                    "en": f"✅ Your request to withdraw {withdrawal.token_amount} tokens has been approved! Funds will be transferred to your payment card within 1-3 business days.",
                    "de": f"✅ Ihr Antrag auf Abhebung von {withdrawal.token_amount} Token wurde genehmigt! Die Gelder werden innerhalb von 1-3 Werktagen auf Ihre Zahlungskarte überwiesen."
                },
                "rejected": {
                    "ua": f"❌ На жаль, ваша заявка на виведення {withdrawal.token_amount} токенів була відхилена. Токени повернуто на ваш баланс. Для отримання детальної інформації зверніться в службу підтримки.",
                    "ru": f"❌ К сожалению, ваша заявка на вывод {withdrawal.token_amount} токенов отклонена. Токены возвращены на ваш баланс. Для получения подробной информации обратитесь в службу поддержки.",
                    "en": f"❌ Unfortunately, your request to withdraw {withdrawal.token_amount} tokens has been rejected. Tokens have been returned to your balance. For detailed information, please contact support.",
                    "de": f"❌ Leider wurde Ihr Antrag auf Abhebung von {withdrawal.token_amount} Token abgelehnt. Die Token wurden Ihrem Guthaben gutgeschrieben. Für detaillierte Informationen wenden Sie sich bitte an den Support."
                }
            }
            
            # Отправляем уведомление
            message = messages.get(status, {}).get(lang, messages[status]["en"])
            return await notify_user(user.telegram_id, message)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления о статусе заявки: {str(e)}")
            return False

async def notify_admins_about_withdrawal(withdrawal_id: int):
    """
    Уведомить администраторов о новой заявке на вывод токенов
    """
    async for session in get_session():
        try:
            # Получаем данные о заявке и пользователе
            from app.models.token_withdrawals import TokenWithdrawal
            
            # Список ID телеграм администраторов
            admin_ids = os.getenv("ADMIN_IDS", "").split(",")
            if not admin_ids:
                return False
                
            # Получаем заявку
            withdrawal = await session.scalar(
                select(TokenWithdrawal).where(TokenWithdrawal.id == withdrawal_id)
            )
            if not withdrawal:
                return False
                
            # Получаем пользователя
            user = await session.scalar(
                select(User).where(User.id == withdrawal.user_id)
            )
            if not user:
                return False
                
            # Формируем сообщение для админа
            message = f"🔔 Новая заявка на вывод токенов!\n\nID заявки: {withdrawal.id}\nПользователь: {user.telegram_id} (ID: {user.id})\nСумма: {withdrawal.token_amount} токенов\nДата: {withdrawal.timestamp}\n\nДля обработки используйте команду /admin_withdrawal {withdrawal.id} [approve/reject]"
            
            # Отправляем сообщение всем администраторам
            for admin_id in admin_ids:
                await notify_user(admin_id, message)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при уведомлении администраторов о заявке: {str(e)}")
            return False
