# файл: app/models/consents.py

from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class ConsentType(str, enum.Enum):
    privacy = "privacy"
    agb = "agb"
    impressum = "impressum"
    ai_training = "ai_training"
    refund_policy = "refund_policy"

class UserConsent(Base):
    __tablename__ = "user_consents"
    __table_args__ = {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    type = Column(Enum(ConsentType), nullable=False)
    accepted_at = Column(DateTime(timezone=True), server_default=func.now())
