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

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # для переказів

    type = Column(Enum(PaymentType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="eur")
    token_amount = Column(Float, nullable=True)  # якщо токени
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)

    tariff = Column(Enum(TariffPlan), nullable=True)  # для підписки
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

class TokenBalance(Base):
    __tablename__ = "token_balances"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    balance = Column(Float, default=0.0)

    user = relationship("User", back_populates="token_balance")

# У models/user.py потрібно додати:
# from sqlalchemy.orm import relationship
# ...
# token_balance = relationship("TokenBalance", back_populates="user", uselist=False)
