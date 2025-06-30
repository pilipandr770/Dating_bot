# файл: Dockerfile

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо залежності
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копіюємо код
COPY . .

# Вхідна точка (зміниться пізніше на Gunicorn/CMD)
CMD ["python", "app/bot.py"]
