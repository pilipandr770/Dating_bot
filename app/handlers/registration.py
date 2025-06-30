# файл: app/handlers/registration.py

from aiogram import types
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.keyboards.registration import gender_keyboard, orientation_keyboard

# Стан машини для анкети
class Registration(StatesGroup):
    name = State()
    gender = State()
    orientation = State()
    age = State()
    city = State()
    language = State()
    photo = State()
    bio = State()
    confirm = State()

# Старт анкети (після "🚀 Почати")
async def start_registration(message: types.Message, state: FSMContext):
    await state.finish()  # якщо юзер натисне "почати" вдруге
    await message.answer("Як тебе звати?")
    await Registration.name.set()


# файл: app/keyboards/registration.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def gender_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("👨 Чоловік"), KeyboardButton("👩 Жінка"), KeyboardButton("⚧ Інше"))
    return kb

def orientation_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(
        KeyboardButton("💞 Гетеро"),
        KeyboardButton("🌈 Гомо"),
        KeyboardButton("🔁 Бі"),
        KeyboardButton("❔ Інше")
    )
    return kb


# Продовження анкети — Ім’я
async def on_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Окей! Тепер обери свою стать:", reply_markup=gender_keyboard())
    await Registration.gender.set()

# Стать
async def on_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Тепер обери орієнтацію:", reply_markup=orientation_keyboard())
    await Registration.orientation.set()

# Орієнтація
async def on_orientation(message: types.Message, state: FSMContext):
    await state.update_data(orientation=message.text)
    await message.answer("Скільки тобі років?")
    await Registration.age.set()

# Вік
async def on_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        if age < 18:
            return await message.answer("❌ Цей бот лише для користувачів 18+.")
        await state.update_data(age=age)
        await message.answer("З якого ти міста?")
        await Registration.city.set()
    except ValueError:
        await message.answer("Вкажи вік числом 🙏")

# Місто
async def on_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await message.answer("Додай своє фото (можна одне або кілька, до 5):")
    await Registration.photo.set()


# Фото — максимум 5
async def on_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])

    if message.photo:
        file_id = message.photo[-1].file_id
        photos.append(file_id)

        if len(photos) >= 5:
            await state.update_data(photos=photos)
            await message.answer("Максимум 5 фото збережено. Напиши коротко про себе (до 300 символів):")
            await Registration.bio.set()
        else:
            await state.update_data(photos=photos)
            await message.answer(f"Фото {len(photos)}/5 прийнято. Можеш надіслати ще або /done щоб перейти до біо.")
    else:
        await message.answer("❌ Надішли саме фото.")

# Команда /done — якщо не хоче більше фото
async def finish_photos(message: types.Message, state: FSMContext):
    await message.answer("Добре! Напиши коротке біо (до 300 символів):")
    await Registration.bio.set()

# Біо
async def on_bio(message: types.Message, state: FSMContext):
    bio = message.text.strip()[:300]
    await state.update_data(bio=bio)

    data = await state.get_data()
    preview = f"🔍 Перевір анкету:\n\n👤 Ім’я: {data.get('name')}\n🧬 Стать: {data.get('gender')}\n"\
              f"💘 Орієнтація: {data.get('orientation')}\n🎂 Вік: {data.get('age')}\n"\
              f"🏙 Місто: {data.get('city')}\n📝 Біо: {bio}\n\nЗберегти?"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("✅ Зберегти"), KeyboardButton("❌ Скасувати"))

    await message.answer(preview, reply_markup=kb)
    await Registration.confirm.set()

# Збереження анкети
from app.services.user_service import create_user_from_registration

async def on_confirm(message: types.Message, state: FSMContext):
    if "зберегти" in message.text.lower():
        data = await state.get_data()
        telegram_id = str(message.from_user.id)

        try:
            await create_user_from_registration(data, telegram_id)
            await message.answer("✅ Твоя анкета збережена! Тепер можна знайомитися ❤️")
        except Exception as e:
            await message.answer(f"❌ Виникла помилка при збереженні анкети: {e}")
        finally:
            await state.finish()
    else:
        await message.answer("❌ Анкету скасовано.")
        await state.finish()


# ... всі async def вище ...

def register_registration_handlers(dp: Dispatcher):
    dp.register_message_handler(start_registration, lambda m: "Почати" in m.text, state="*")
    dp.register_message_handler(on_name, state=Registration.name)
    dp.register_message_handler(on_gender, state=Registration.gender)
    dp.register_message_handler(on_orientation, state=Registration.orientation)
    dp.register_message_handler(on_age, state=Registration.age)
    dp.register_message_handler(on_city, state=Registration.city)
    dp.register_message_handler(on_photo, content_types=types.ContentType.PHOTO, state=Registration.photo)
    dp.register_message_handler(finish_photos, commands="done", state=Registration.photo)
    dp.register_message_handler(on_bio, state=Registration.bio)
    dp.register_message_handler(on_confirm, state=Registration.confirm)

