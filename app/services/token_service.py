# файл: app/services/token_service.py

from app.database import get_session
from app.models.user import User
from app.models.payments import Payment
from app.models.token_withdrawals import TokenWithdrawal
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_user_balance(telegram_id: str) -> int:
    """
    Получить текущий баланс токенов пользователя по Telegram ID
    """
    async for session in get_session():
        try:
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            return user.token_balance if user else 0
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {str(e)}")
            return 0

async def update_user_balance(telegram_id: str, amount: int) -> bool:
    """
    Обновить баланс токенов пользователя (добавить/вычесть)
    Положительное значение - пополнение, отрицательное - списание
    """
    async for session in get_session():
        try:
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            if not user:
                return False
                
            # Проверяем, достаточно ли средств при списании
            if amount < 0 and user.token_balance + amount < 0:
                return False
                
            # Обновляем баланс
            user.token_balance += amount
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при обновлении баланса: {str(e)}")
            return False

async def transfer_tokens(sender_telegram_id: str, receiver_telegram_id: str, amount: int) -> bool:
    """
    Перевести токены от одного пользователя к другому
    """
    if amount <= 0:
        return False
        
    # Проверяем, не пытается ли пользователь перевести токены самому себе
    if sender_telegram_id == receiver_telegram_id:
        return False
        
    async for session in get_session():
        try:
            # Получаем отправителя
            sender = await session.scalar(
                select(User).where(User.telegram_id == sender_telegram_id)
            )
            if not sender or sender.token_balance < amount:
                return False
                
            # Получаем получателя
            receiver = await session.scalar(
                select(User).where(User.telegram_id == receiver_telegram_id)
            )
            if not receiver:
                return False
                
            # Списываем токены у отправителя
            sender.token_balance -= amount
            
            # Зачисляем токены получателю
            receiver.token_balance += amount
            
            # Записываем транзакцию
            payment = Payment(
                user_id=sender.id,
                type="token_transfer",
                amount=0,  # Денежная сумма = 0
                token_amount=amount,
                status="confirmed"
            )
            session.add(payment)
            
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при переводе токенов: {str(e)}")
            return False

async def request_withdrawal(telegram_id: str, amount: int) -> bool:
    """
    Создать запрос на вывод токенов
    """
    if amount <= 0:
        return False
        
    async for session in get_session():
        try:
            # Получаем пользователя
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            if not user or user.token_balance < amount:
                return False
                
            # Создаем запрос на вывод
            withdrawal = TokenWithdrawal(
                user_id=user.id,
                token_amount=amount,
                status="pending"
            )
            session.add(withdrawal)
            
            # Временно блокируем сумму вывода (вычитаем из баланса)
            user.token_balance -= amount
            
            await session.commit()
            
            # Уведомляем администраторов о новой заявке
            from app.services.notification_service import notify_admins_about_withdrawal
            await notify_admins_about_withdrawal(withdrawal.id)
            
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при создании запроса на вывод: {str(e)}")
            return False

async def approve_withdrawal(withdrawal_id: int) -> bool:
    """
    Подтвердить запрос на вывод токенов (только для администратора)
    """
    async for session in get_session():
        try:
            withdrawal = await session.scalar(
                select(TokenWithdrawal).where(TokenWithdrawal.id == withdrawal_id)
            )
            if not withdrawal or withdrawal.status != "pending":
                return False
                
            withdrawal.status = "approved"
            
            # Токены уже списаны при создании запроса
            
            await session.commit()
            
            # Уведомляем пользователя об одобрении заявки
            from app.services.notification_service import notify_withdrawal_status
            await notify_withdrawal_status(withdrawal_id, "approved")
            
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при подтверждении вывода: {str(e)}")
            return False

async def reject_withdrawal(withdrawal_id: int) -> bool:
    """
    Отклонить запрос на вывод токенов (только для администратора)
    """
    async for session in get_session():
        try:
            withdrawal = await session.scalar(
                select(TokenWithdrawal).where(TokenWithdrawal.id == withdrawal_id)
            )
            if not withdrawal or withdrawal.status != "pending":
                return False
                
            # Меняем статус
            withdrawal.status = "rejected"
            
            # Возвращаем токены пользователю
            user = await session.scalar(
                select(User).where(User.id == withdrawal.user_id)
            )
            if user:
                user.token_balance += withdrawal.token_amount
            
            await session.commit()
            
            # Уведомляем пользователя об отклонении заявки
            from app.services.notification_service import notify_withdrawal_status
            await notify_withdrawal_status(withdrawal_id, "rejected")
            
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при отклонении вывода: {str(e)}")
            return False

async def get_token_history(telegram_id: str, limit: int = 10) -> list:
    """
    Получить историю операций с токенами для пользователя
    """
    async for session in get_session():
        try:
            # Получаем ID пользователя
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            if not user:
                return []
                
            # Получаем платежи пользователя (пополнения и переводы)
            payments = await session.scalars(
                select(Payment)
                .where(Payment.user_id == user.id)
                .where(Payment.token_amount.isnot(None))  # Фильтруем только операции с токенами
                .order_by(Payment.timestamp.desc())
                .limit(limit)
            )
            
            # Получаем заявки на вывод
            withdrawals = await session.scalars(
                select(TokenWithdrawal)
                .where(TokenWithdrawal.user_id == user.id)
                .order_by(TokenWithdrawal.timestamp.desc())
                .limit(limit)
            )
            
            # Объединяем результаты
            result = []
            
            for payment in payments:
                operation_type = ""
                if payment.type == "token_purchase":
                    operation_type = "purchase"
                elif payment.type == "token_transfer":
                    operation_type = "transfer"
                    
                result.append({
                    "type": operation_type,
                    "amount": payment.token_amount,
                    "timestamp": payment.timestamp,
                    "status": payment.status
                })
                
            for withdrawal in withdrawals:
                result.append({
                    "type": "withdrawal",
                    "amount": -withdrawal.token_amount,  # Отрицательное значение для вывода
                    "timestamp": withdrawal.timestamp,
                    "status": withdrawal.status
                })
                
            # Сортируем по времени
            result.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Ограничиваем результат
            return result[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории токенов: {str(e)}")
            return []
