# файл: app/keyboards/main_menu.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu(lang: str):
    texts = {
        "ua": {
            "start": "🚀 Почати",
            "profile": "📝 Анкета",
            "swipes": "👥 Знайомитись",
            "matches": "❤️ Мої матчі",
            "settings": "⚙️ Налаштування пошуку",
            "privacy": "🛡 Datenschutz",
            "agb": "📜 AGB",
            "impressum": "ℹ️ Impressum"
        },
        "ru": {
            "start": "🚀 Начать",
            "profile": "📝 Анкета",
            "swipes": "👥 Знакомиться",
            "matches": "❤️ Мои матчи",
            "settings": "⚙️ Настройки поиска",
            "privacy": "🛡 Datenschutz",
            "agb": "📜 AGB",
            "impressum": "ℹ️ Impressum"
        },
        "en": {
            "start": "🚀 Start",
            "profile": "📝 Profile",
            "swipes": "👥 Meet people",
            "matches": "❤️ My matches",
            "settings": "⚙️ Search settings",
            "privacy": "🛡 Privacy Policy",
            "agb": "📜 Terms of Use",
            "impressum": "ℹ️ Imprint"
        },
        "de": {
            "start": "🚀 Starten",
            "profile": "📝 Profil",
            "swipes": "👥 Leute kennenlernen",
            "matches": "❤️ Meine Matches",
            "settings": "⚙️ Sucheinstellungen",
            "privacy": "🛡 Datenschutz",
            "agb": "📜 AGB",
            "impressum": "ℹ️ Impressum"
        },
    }

    t = texts.get(lang, texts["en"])

    # Настраиваем параметры клавиатуры:
    # resize_keyboard=True - компактная клавиатура
    # one_time_keyboard=False - клавиатура остается видимой после нажатия
    # is_persistent=True - сохраняет клавиатуру между перезапусками
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True, 
        one_time_keyboard=False,
        input_field_placeholder="Виберіть дію"
    )
    kb.row(KeyboardButton(t["swipes"]), KeyboardButton(t["matches"]))
    kb.row(KeyboardButton(t["profile"]), KeyboardButton(t["settings"]))
    kb.row(KeyboardButton(t["privacy"]), KeyboardButton(t["agb"]), KeyboardButton(t["impressum"]))
    return kb
