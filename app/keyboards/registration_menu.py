# файл: app/keyboards/registration_menu.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_registration_menu(lang: str):
    texts = {
        "ua": {
            "name":     "✏️ Ввести ім'я",
            "gender":   "👤 Стать",
            "orientation": "🏳️ Ориєнтація",
            "age":      "🎂 Вік",
            "city":     "📍 Місто",
            "photos":   "📷 Фото",
            "bio":      "📝 Біо",
            "done":     "✅ Готово"
        },
        "ru": {
            "name":     "✏️ Ввести имя",
            "gender":   "👤 Пол",
            "orientation": "🏳️ Ориентация",
            "age":      "🎂 Возраст",
            "city":     "📍 Город",
            "photos":   "📷 Фото",
            "bio":      "📝 Био",
            "done":     "✅ Готово"
        },
        "en": {
            "name":     "✏️ Enter name",
            "gender":   "👤 Gender",
            "orientation": "🏳️ Orientation",
            "age":      "🎂 Age",
            "city":     "📍 City",
            "photos":   "📷 Photos",
            "bio":      "📝 Bio",
            "done":     "✅ Done"
        },
        "de": {
            "name":     "✏️ Name eingeben",
            "gender":   "👤 Geschlecht",
            "orientation": "🏳️ Orientierung",
            "age":      "🎂 Alter",
            "city":     "📍 Stadt",
            "photos":   "📷 Fotos",
            "bio":      "📝 Bio",
            "done":     "✅ Fertig"
        }
    }
    t = texts.get(lang, texts["ua"])
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(t["name"]), KeyboardButton(t["gender"]))
    kb.add(KeyboardButton(t["orientation"]), KeyboardButton(t["age"]))
    kb.add(KeyboardButton(t["city"]), KeyboardButton(t["photos"]))
    kb.add(KeyboardButton(t["bio"]))
    kb.add(KeyboardButton(t["done"]))
    return kb
