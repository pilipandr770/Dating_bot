# файл: app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, Enum, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr
import enum

# Import the shared Base
from app.models.base import Base

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
    
    @declared_attr
    def __table_args__(cls):
        return {'schema': 'dating_bot'}

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
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
