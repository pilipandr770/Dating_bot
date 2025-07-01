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
    first_name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)  # Text field in DB, not enum
    orientation = Column(String)  # Text field in DB, not enum
    city = Column(String)
    language = Column(String)  # Text field in DB, not enum
    bio = Column(String)
    is_verified = Column(Boolean, default=False)
    token_balance = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
