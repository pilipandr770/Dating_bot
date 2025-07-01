# файл: app/keyboards/main_menu.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu(lang: str):
    texts = {
        "ua": {
            "start": "🚀 Почати",
            "profile": "📝 Анкета",
            "privacy": "🛡 Datenschutz",
            "agb": "📜 AGB",
            "impressum": "ℹ️ Impressum"
        },
        "ru": {
            "start": "🚀 Начать",
            "profile": "📝 Анкета",
            "privacy": "🛡 Datenschutz",
            "agb": "📜 AGB",
            "impressum": "ℹ️ Impressum"
        },
        "en": {
            "start": "🚀 Start",
            "profile": "📝 Profile",
            "privacy": "🛡 Privacy Policy",
            "agb": "📜 Terms of Use",
            "impressum": "ℹ️ Imprint"
        },
        "de": {
            "start": "🚀 Starten",
            "profile": "📝 Profil",
            "privacy": "🛡 Datenschutz",
            "agb": "📜 AGB",
            "impressum": "ℹ️ Impressum"
        },
    }

    t = texts.get(lang, texts["en"])

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton(t["start"]), KeyboardButton(t["profile"]))
    kb.row(KeyboardButton(t["privacy"]), KeyboardButton(t["agb"]), KeyboardButton(t["impressum"]))
    return kb
