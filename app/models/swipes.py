# файл: app/models/swipes.py

from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

# Import a shared Base to avoid multiple base classes
from app.models.base import Base

class Swipe(Base):
    __tablename__ = "swipes"
    
    @declared_attr
    def __table_args__(cls):
        return {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    swiper_id = Column(Integer, ForeignKey("dating_bot.users.id", ondelete="CASCADE"))
    swiped_id = Column(Integer, ForeignKey("dating_bot.users.id", ondelete="CASCADE"))
    is_like = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
