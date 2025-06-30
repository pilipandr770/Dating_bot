# файл: app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, Enum, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class GenderEnum(str, enum.Enum):
    male = "чоловік"
    female = "жінка"
    other = "інше"

class OrientationEnum(str, enum.Enum):
    hetero = "гетеро"
    homo = "гомо"
    bi = "бі"
    other = "інше"

class LanguageEnum(str, enum.Enum):
    ua = "ua"
    ru = "ru"
    en = "en"
    de = "de"

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    age = Column(Integer, nullable=False)
    gender = Column(Enum(GenderEnum))
    orientation = Column(Enum(OrientationEnum))
    city = Column(String)
    language = Column(Enum(LanguageEnum))
    bio = Column(String(300))
    is_verified = Column(Boolean, default=False)
    consent_ai_training = Column(Boolean, default=False)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_flagged = Column(Boolean, default=False)  # ⚠️ позначено як підозрілий
