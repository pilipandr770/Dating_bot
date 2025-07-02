# файл: app/models/wallet.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class Wallet(Base):
    """Модель кошелька пользователя"""
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    balance = Column(Float, default=0.0, nullable=False)  # Баланс в условных единицах
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Связь с пользователем
    user = relationship("User", backref="wallet", uselist=False)

    # Связь с транзакциями
    transactions = relationship("Transaction", back_populates="wallet")


class Transaction(Base):
    """Модель для хранения транзакций пользователей"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # deposit, withdrawal, transfer_in, transfer_out, purchase
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    reference_id = Column(String(100), nullable=True)  # ID платежа во внешней системе или ID транзакции для перевода
    status = Column(String(20), default="completed")  # pending, completed, failed, cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Связь с кошельком
    wallet = relationship("Wallet", back_populates="transactions")
