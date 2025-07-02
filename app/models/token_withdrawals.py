# файл: app/models/token_withdrawals.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class TokenWithdrawal(Base):
    __tablename__ = "token_withdrawals"
    __table_args__ = ({'schema': 'dating_bot'})

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id", ondelete="CASCADE"), nullable=False)
    token_amount = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # "pending", "approved", "rejected"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    user = relationship("User", backref="token_withdrawals")
