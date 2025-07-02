# файл: app/keyboards/search_settings.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_search_settings_menu(language="ua"):
    """
    Клавиатура для меню настроек поиска
    """
    texts = {
        "ua": {
            "age_range": "🔢 Віковий діапазон",
            "gender": "👤 Стать",
            "distance": "🌍 Відстань пошуку",
            "city_only": "🏙️ Тільки в моєму місті",
            "back": "⬅️ Назад до меню"
        },
        "ru": {
            "age_range": "🔢 Возрастной диапазон",
            "gender": "👤 Пол",
            "distance": "🌍 Расстояние поиска",
            "city_only": "🏙️ Только в моем городе",
            "back": "⬅️ Назад в меню"
        },
        "en": {
            "age_range": "🔢 Age range",
            "gender": "👤 Gender",
            "distance": "🌍 Search distance",
            "city_only": "🏙️ Only in my city",
            "back": "⬅️ Back to menu"
        },
        "de": {
            "age_range": "🔢 Altersbereich",
            "gender": "👤 Geschlecht",
            "distance": "🌍 Suchentfernung",
            "city_only": "🏙️ Nur in meiner Stadt",
            "back": "⬅️ Zurück zum Menü"
        }
    }
    
    t = texts.get(language, texts["ua"])
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton(t["age_range"]), KeyboardButton(t["gender"]))
    kb.add(KeyboardButton(t["distance"]), KeyboardButton(t["city_only"]))
    kb.add(KeyboardButton(t["back"]))
    
    return kb

def get_gender_preference_keyboard(language="ua"):
    """
    Клавиатура для выбора предпочитаемого пола
    """
    texts = {
        "ua": {
            "male": "👨 Чоловіки",
            "female": "👩 Жінки",
            "any": "👥 Будь-який",
            "back": "⬅️ Назад"
        },
        "ru": {
            "male": "👨 Мужчины",
            "female": "👩 Женщины",
            "any": "👥 Любой",
            "back": "⬅️ Назад"
        },
        "en": {
            "male": "👨 Men",
            "female": "👩 Women",
            "any": "👥 Any",
            "back": "⬅️ Back"
        },
        "de": {
            "male": "👨 Männer",
            "female": "👩 Frauen",
            "any": "👥 Beliebig",
            "back": "⬅️ Zurück"
        }
    }
    
    t = texts.get(language, texts["ua"])
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton(t["male"]), KeyboardButton(t["female"]))
    kb.add(KeyboardButton(t["any"]))
    kb.add(KeyboardButton(t["back"]))
    
    return kb

def get_city_filter_keyboard(language="ua", is_active=False):
    """
    Клавиатура для включения/выключения фильтра города
    """
    texts = {
        "ua": {
            "enable": "✅ Включити фільтр міста",
            "disable": "❌ Вимкнути фільтр міста",
            "back": "⬅️ Назад"
        },
        "ru": {
            "enable": "✅ Включить фильтр города",
            "disable": "❌ Выключить фильтр города",
            "back": "⬅️ Назад"
        },
        "en": {
            "enable": "✅ Enable city filter",
            "disable": "❌ Disable city filter",
            "back": "⬅️ Back"
        },
        "de": {
            "enable": "✅ Stadtfilter aktivieren",
            "disable": "❌ Stadtfilter deaktivieren",
            "back": "⬅️ Zurück"
        }
    }
    
    t = texts.get(language, texts["ua"])
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add(KeyboardButton(t["disable"] if is_active else t["enable"]))
    kb.add(KeyboardButton(t["back"]))
    
    return kb
