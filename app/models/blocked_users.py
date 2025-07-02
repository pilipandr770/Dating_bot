# файл: app/models/blocked_users.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base

class BlockedUser(Base):
    __tablename__ = "blocked_users"
    __table_args__ = (
        UniqueConstraint('blocker_id', 'blocked_id', name='uq_blocker_blocked'),
        {'schema': 'dating_bot'}
    )

    id = Column(Integer, primary_key=True)
    blocker_id = Column(Integer, ForeignKey("dating_bot.users.id", ondelete="CASCADE"), nullable=False)
    blocked_id = Column(Integer, ForeignKey("dating_bot.users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
