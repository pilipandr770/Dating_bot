# файл: app/handlers/registration.py

from aiogram import types
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from app.keyboards.registration import gender_keyboard, orientation_keyboard
from app.keyboards.registration_menu import get_registration_menu
from app.keyboards.main_menu import get_main_menu
from app.services.user_service import create_or_get_user, update_user_field, get_user_language, save_user_photos, get_user_photos
from sqlalchemy import select
from app.models.user import User
from app.database import get_session

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

# Новий стан для меню анкети
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_orientation = State()
    waiting_for_age = State()
    waiting_for_city = State()
    waiting_for_photos = State()
    waiting_for_bio = State()

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
            # Создаем пользователя, если еще не существует
            user = await create_or_get_user(telegram_id)
            
            # Сохраняем анкету
            user_id = await create_user_from_registration(data, telegram_id)
            
            if not user_id:
                await message.answer("❌ Ошибка при сохранении анкеты. Попробуйте еще раз.")
                await state.finish()
                return
            
            # Получаем язык пользователя сначала из данных состояния, затем из базы если в состоянии нет
            lang = data.get("language") or await get_user_language(telegram_id) or "ua"
            
            # Тексты для разных языков
            texts = {
                "ua": {
                    "success": "✅ Твоя анкета збережена! Тепер можна знайомитися ❤️",
                    "hint": "👇 Натисніть кнопку \"Знайомитись\" для пошуку нових профілів"
                },
                "ru": {
                    "success": "✅ Твоя анкета сохранена! Теперь можно знакомиться ❤️",
                    "hint": "👇 Нажмите кнопку \"Знакомиться\" для поиска новых профилей"
                },
                "en": {
                    "success": "✅ Your profile has been saved! Now you can start meeting people ❤️",
                    "hint": "👇 Press the \"Meet people\" button to find new profiles"
                },
                "de": {
                    "success": "✅ Dein Profil wurde gespeichert! Jetzt kannst du Leute kennenlernen ❤️",
                    "hint": "👇 Drücke den \"Leute kennenlernen\" Button, um neue Profile zu finden"
                }
            }
            
            t = texts.get(lang, texts["en"])
            
            # Создаем клавиатуру явным образом
            main_menu = get_main_menu(lang)
            
            # Радикальный способ: отправляем пользователю команду для отображения главного меню
            # Сначала удаляем клавиатуру
            await message.answer("⌛ Сохраняем анкету...", reply_markup=ReplyKeyboardRemove())
            
            # Затем отправляем новое сообщение с главным меню
            await message.answer(
                f"{t['success']}\n\n{t['hint']}",
                reply_markup=main_menu
            )
            
            # Завершаем состояние
            await state.finish()
        except Exception as e:
            await message.answer(f"❌ Виникла помилка при збереженні анкети: {e}")
            await state.finish()
    else:
        # Получаем данные из состояния
        data = await state.get_data()
        telegram_id = str(message.from_user.id)
        
        # Получаем язык пользователя сначала из данных состояния, затем из базы если в состоянии нет
        lang = data.get("language") or await get_user_language(telegram_id) or "ua"
        
        # Тексты для разных языков
        cancel_texts = {
            "ua": "❌ Анкету скасовано.",
            "ru": "❌ Анкета отменена.",
            "en": "❌ Profile creation canceled.",
            "de": "❌ Profilerstellung abgebrochen."
        }
        
        text = cancel_texts.get(lang, cancel_texts["en"])
        
        # Сначала удаляем текущую клавиатуру
        await message.answer("⌛ Отменяем...", reply_markup=ReplyKeyboardRemove())
        
        # Создаем главное меню явно
        main_menu = get_main_menu(lang)
        
        # Затем показываем сообщение с новой клавиатурой
        await message.answer(text, reply_markup=main_menu)
        await state.finish()


# Профіль / анкета
async def cmd_profile(message: types.Message, state: FSMContext):
    # Отримуємо мову користувача
    user_id = message.from_user.id
    lang = await get_user_language(str(user_id))
    
    # Сначала показываем текущую анкету, если есть данные
    async for session in get_session():
        user = await session.scalar(select(User).where(User.telegram_id == str(user_id)))
        if user:
            # Отображаем информацию о пользователе
            profile_text = f"👤 {user.first_name}, {user.age or '?'}\n"
            if user.gender:
                profile_text += f"🧬 {user.gender}\n"
            if user.orientation:
                profile_text += f"💘 {user.orientation}\n"
            if user.city:
                profile_text += f"🏙 {user.city}\n"
            if user.bio:
                profile_text += f"📝 {user.bio}\n"
                
            # Получаем и отображаем фотографии
            photo_file_ids = await get_user_photos(user.id)
            
            if photo_file_ids and len(photo_file_ids) > 0:
                # Отправляем первое фото с подписью
                await message.answer_photo(
                    photo=photo_file_ids[0],
                    caption=f"📸 Ваш текущий профиль:\n\n{profile_text}"
                )
                
                # Если есть еще фото - отправляем их
                if len(photo_file_ids) > 1:
                    media_group = []
                    for file_id in photo_file_ids[1:]:
                        media_group.append(types.InputMediaPhoto(media=file_id))
                    
                    if media_group:
                        await message.answer_media_group(media_group)
            else:
                # Если нет фото - просто текст
                await message.answer(f"📸 Ваш текущий профиль:\n\n{profile_text}")
    
    # Удаляем клавиатуру
    await message.answer("📝 Открываем редактор анкеты...", reply_markup=ReplyKeyboardRemove())
    
    # Получаем клавиатуру редактирования анкеты
    reg_menu = get_registration_menu(lang)
    
    # Показываем новое меню
    await message.answer("📝 Розділ «Анкета». Оберіть, що заповнити:", 
                         reply_markup=reg_menu)
    await state.finish()  # якщо була якась попередня сесія

# Обробники для кожного поля в анкеті

async def process_name_button(message: types.Message, state: FSMContext):
    await message.answer("✏️ Введіть ваше ім'я:")
    await RegistrationStates.waiting_for_name.set()

async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Ім'я повинно містити щонайменше 2 символи. Спробуйте знову:")
        return
    
    await update_user_field(str(message.from_user.id), "first_name", name)
    await message.answer(f"✅ Ім'я {name} збережено.")
    await cmd_profile(message, state)  # повернутися в меню анкети

async def process_gender_button(message: types.Message, state: FSMContext):
    await message.answer("👤 Оберіть вашу стать:", reply_markup=gender_keyboard())
    await RegistrationStates.waiting_for_gender.set()

async def process_gender(message: types.Message, state: FSMContext):
    gender = message.text
    await update_user_field(str(message.from_user.id), "gender", gender)
    await message.answer(f"✅ Стать {gender} збережено.")
    await cmd_profile(message, state)

async def process_orientation_button(message: types.Message, state: FSMContext):
    await message.answer("🏳️ Оберіть вашу орієнтацію:", reply_markup=orientation_keyboard())
    await RegistrationStates.waiting_for_orientation.set()

async def process_orientation(message: types.Message, state: FSMContext):
    orientation = message.text
    await update_user_field(str(message.from_user.id), "orientation", orientation)
    await message.answer(f"✅ Орієнтацію {orientation} збережено.")
    await cmd_profile(message, state)

async def process_age_button(message: types.Message, state: FSMContext):
    await message.answer("🎂 Введіть ваш вік (лише число, наприклад: 25):")
    await RegistrationStates.waiting_for_age.set()

async def process_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if age < 18 or age > 100:
            await message.answer("❌ Вік повинен бути від 18 до 100 років. Спробуйте знову:")
            return
            
        await update_user_field(str(message.from_user.id), "age", age)
        await message.answer(f"✅ Вік {age} збережено.")
        await cmd_profile(message, state)
    except ValueError:
        await message.answer("❌ Будь ласка, введіть дійсний вік (лише число):")

async def process_city_button(message: types.Message, state: FSMContext):
    await message.answer("📍 Введіть ваше місто:")
    await RegistrationStates.waiting_for_city.set()

async def process_city(message: types.Message, state: FSMContext):
    city = message.text.strip()
    if len(city) < 2:
        await message.answer("❌ Назва міста повинна містити щонайменше 2 символи. Спробуйте знову:")
        return
        
    await update_user_field(str(message.from_user.id), "city", city)
    await message.answer(f"✅ Місто {city} збережено.")
    await cmd_profile(message, state)

async def process_photos_button(message: types.Message, state: FSMContext):
    await message.answer(
        "📷 Надішліть ваше фото (до 5 фото).\n"
        "Після завершення надішліть текст 'Готово'"
    )
    await state.update_data(photos=[])
    await RegistrationStates.waiting_for_photos.set()

async def process_photos(message: types.Message, state: FSMContext):
    if message.text and message.text.lower() == "готово":
        data = await state.get_data()
        photos = data.get("photos", [])
        
        if not photos:
            await message.answer("❌ Ви не додали жодного фото. Спробуйте знову або натисніть 'Готово':")
            return
            
        # Сначала создаем пользователя, если его еще нет
        telegram_id = str(message.from_user.id)
        user = await create_or_get_user(telegram_id)
        
        # Затем сохраняем фото
        success = await save_user_photos(telegram_id, photos)
        
        if success:
            await message.answer(f"✅ Збережено {len(photos)} фото.")
        else:
            await message.answer("❌ Виникла проблема при збереженні фото. Спробуйте пізніше.")
        
        await cmd_profile(message, state)
    elif message.photo:
        data = await state.get_data()
        photos = data.get("photos", [])
        
        if len(photos) >= 5:
            await message.answer("❌ Ви вже додали максимальну кількість фото (5). Натисніть 'Готово':")
            return
            
        file_id = message.photo[-1].file_id
        photos.append(file_id)
        
        await state.update_data(photos=photos)
        await message.answer(f"✅ Фото {len(photos)}/5 додано. Додайте ще або напишіть 'Готово'")
    else:
        await message.answer("❌ Будь ласка, надішліть фото або напишіть 'Готово':")

async def process_bio_button(message: types.Message, state: FSMContext):
    await message.answer(
        "📝 Розкажіть про себе (до 300 символів).\n"
        "Це допоможе іншим користувачам краще вас зрозуміти."
    )
    await RegistrationStates.waiting_for_bio.set()

async def process_bio(message: types.Message, state: FSMContext):
    bio = message.text.strip()
    if len(bio) > 300:
        await message.answer("❌ Біо занадто довге (максимум 300 символів). Спробуйте знову:")
        return
        
    await update_user_field(str(message.from_user.id), "bio", bio)
    await message.answer(f"✅ Біо збережено.")
    await cmd_profile(message, state)

async def process_done_button(message: types.Message, state: FSMContext):
    # Получаем данные из состояния
    telegram_id = str(message.from_user.id)
    lang = await get_user_language(telegram_id) or "ua"
    
    # Сначала удаляем текущую клавиатуру
    await message.answer("⌛ Завершаем настройку профиля...", reply_markup=ReplyKeyboardRemove())
    
    # Создаем главное меню
    main_menu = get_main_menu(lang)
    
    # Показываем сообщение с новой клавиатурой
    await message.answer(
        "✅ Анкета заповнена! Тепер ви можете починати знайомства.",
        reply_markup=main_menu
    )
    
    # Завершаем состояние
    await state.finish()

# Розширена реєстрація обробників
def register_registration_handlers(dp: Dispatcher):
    # Старі обробники для процесу реєстрації
    dp.register_message_handler(start_registration, lambda m: "Почати" in m.text or "Начать" in m.text or "Start" in m.text or "Starten" in m.text, state="*")
    dp.register_message_handler(on_name, state=Registration.name)
    dp.register_message_handler(on_gender, state=Registration.gender)
    dp.register_message_handler(on_orientation, state=Registration.orientation)
    dp.register_message_handler(on_age, state=Registration.age)
    dp.register_message_handler(on_city, state=Registration.city)
    dp.register_message_handler(on_photo, content_types=types.ContentType.PHOTO, state=Registration.photo)
    
    # Обробник для кнопки "Анкета" в головному меню
    dp.register_message_handler(cmd_profile, lambda m: "📝" in m.text and ("Анкета" in m.text or "Profile" in m.text or "Profil" in m.text))
    
    # Кнопки меню анкети
    dp.register_message_handler(process_name_button, lambda m: "Ввести ім'я" in m.text or "Ввести имя" in m.text or "Enter name" in m.text or "Name eingeben" in m.text)
    dp.register_message_handler(process_gender_button, lambda m: "Стать" in m.text or "Пол" in m.text or "Gender" in m.text or "Geschlecht" in m.text)
    dp.register_message_handler(process_orientation_button, lambda m: "Ориєнтація" in m.text or "Ориентация" in m.text or "Orientation" in m.text or "Orientierung" in m.text)
    dp.register_message_handler(process_age_button, lambda m: "Вік" in m.text or "Возраст" in m.text or "Age" in m.text or "Alter" in m.text)
    dp.register_message_handler(process_city_button, lambda m: "Місто" in m.text or "Город" in m.text or "City" in m.text or "Stadt" in m.text)
    dp.register_message_handler(process_photos_button, lambda m: "Фото" in m.text or "Photos" in m.text or "Fotos" in m.text)
    dp.register_message_handler(process_bio_button, lambda m: "Біо" in m.text or "Био" in m.text or "Bio" in m.text)
    dp.register_message_handler(process_done_button, lambda m: "Готово" in m.text or "Done" in m.text or "Fertig" in m.text)
    
    # Обробники станів анкети
    dp.register_message_handler(process_name, state=RegistrationStates.waiting_for_name)
    dp.register_message_handler(process_gender, state=RegistrationStates.waiting_for_gender)
    dp.register_message_handler(process_orientation, state=RegistrationStates.waiting_for_orientation)
    dp.register_message_handler(process_age, state=RegistrationStates.waiting_for_age)
    dp.register_message_handler(process_city, state=RegistrationStates.waiting_for_city)
    dp.register_message_handler(process_photos, state=RegistrationStates.waiting_for_photos, content_types=['photo', 'text'])
    dp.register_message_handler(process_bio, state=RegistrationStates.waiting_for_bio)
    dp.register_message_handler(finish_photos, commands="done", state=Registration.photo)
    dp.register_message_handler(on_bio, state=Registration.bio)
    dp.register_message_handler(on_confirm, state=Registration.confirm)
    dp.register_message_handler(cmd_profile, commands="profile", state="*")
    dp.register_message_handler(process_name_button, lambda m: "ім'я" in m.text.lower(), state="*")
    dp.register_message_handler(process_name, state=RegistrationStates.waiting_for_name)
    dp.register_message_handler(process_gender_button, lambda m: "стать" in m.text.lower(), state="*")
    dp.register_message_handler(process_gender, state=RegistrationStates.waiting_for_gender)
    dp.register_message_handler(process_orientation_button, lambda m: "орієнтацію" in m.text.lower(), state="*")
    dp.register_message_handler(process_orientation, state=RegistrationStates.waiting_for_orientation)
    dp.register_message_handler(process_age_button, lambda m: "вік" in m.text.lower(), state="*")
    dp.register_message_handler(process_age, state=RegistrationStates.waiting_for_age)
    dp.register_message_handler(process_city_button, lambda m: "місто" in m.text.lower(), state="*")
    dp.register_message_handler(process_city, state=RegistrationStates.waiting_for_city)
    dp.register_message_handler(process_photos_button, lambda m: "фото" in m.text.lower(), state="*")
    dp.register_message_handler(process_photos, content_types=types.ContentType.PHOTO, state=RegistrationStates.waiting_for_photos)
    dp.register_message_handler(process_bio_button, lambda m: "біо" in m.text.lower(), state="*")
    dp.register_message_handler(process_bio, state=RegistrationStates.waiting_for_bio)
    dp.register_message_handler(process_done_button, lambda m: "готово" in m.text.lower(), state="*")

