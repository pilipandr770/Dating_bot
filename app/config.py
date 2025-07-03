# файл: app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
POSTGRES_URL = os.getenv("POSTGRES_URL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_CHAT_ID = os.getenv("OPENAI_ASSISTANT_ID_CHAT")
ASSISTANT_ANALYSIS_ID = os.getenv("OPENAI_ASSISTANT_ID_ANALYSIS")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRODUCT_URL = os.getenv("STRIPE_PRODUCT_URL")
STRIPE_SUBSCRIPTION_URL = os.getenv("STRIPE_SUBSCRIPTION_URL")

# Ключи для сервисов бронирования
OPENTABLE_API_KEY = os.getenv("OPENTABLE_API_KEY", "")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN", "")

def get_config(key, default=None):
    """Получение значения из переменных среды с возможностью указать значение по умолчанию"""
    return os.getenv(key, default)
