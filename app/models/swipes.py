# файл: app/models/swipes.py

from sqlalchemy import Column, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class SwipeAction(str, enum.Enum):
    like = "like"
    dislike = "dislike"

class Swipe(Base):
    __tablename__ = "swipes"
    __table_args__ = {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    swiper_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    swiped_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    action = Column(Enum(SwipeAction), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
