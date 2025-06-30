# файл: app/models/user_answers.py

from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserAnswer(Base):
    __tablename__ = "user_answers"
    __table_args__ = {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    question_id = Column(Integer, ForeignKey("dating_bot.questions.id"))
    answer = Column(String)
