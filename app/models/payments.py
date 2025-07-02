# файл: app/models/payments.py

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum
from app.database import Base

class PaymentType(str, enum.Enum):
    stripe = "stripe"           # зовнішній платіж
    token_purchase = "token_purchase"   # покупка токенів
    token_transfer = "token_transfer"   # переказ між користувачами
    token_refund = "token_refund"       # продаж токенів боту

class TariffPlan(str, enum.Enum):
    base = "base"
    premium = "premium"
    vip = "vip"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = ({'schema': 'dating_bot'})

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id", ondelete="CASCADE"), nullable=False)
    
    # Поля из schema.sql
    type = Column(String, nullable=False)  # Вместо Enum для соответствия схеме
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="eur")
    token_amount = Column(Integer, nullable=True)  # Integer вместо Float
    status = Column(String, default="pending")  # Вместо Enum для соответствия схеме
    stripe_session_id = Column(String, nullable=True)  # Добавляем поле из схемы
    tariff = Column(String, nullable=True)  # Для подписки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    user = relationship("User", foreign_keys=[user_id])

# Примечание: TokenBalance класс удален, так как баланс токенов хранится 
# непосредственно в таблице users (поле token_balance)
