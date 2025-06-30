# файл: app/models/questions.py

from sqlalchemy import Column, Integer, String, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class QuestionType(str, enum.Enum):
    single_choice = "single_choice"
    text = "text"

class Question(Base):
    __tablename__ = "questions"
    __table_args__ = {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    type = Column(Enum(QuestionType), nullable=False)
    options = Column(JSON)  # для типу single_choice
