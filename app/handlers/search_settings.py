# файл: app/handlers/search_settings.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.keyboards.search_settings import get_search_settings_menu, get_gender_preference_keyboard, get_city_filter_keyboard
from app.keyboards.main_menu import get_main_menu
from app.services.search_settings_service import get_search_settings_by_telegram_id, update_search_settings
from app.services.user_service import get_user_language

# Определяем состояния FSM для настроек поиска
class SearchSettingsStates(StatesGroup):
    main_settings = State()  # Основное меню настроек
    age_min = State()        # Ввод минимального возраста
    age_max = State()        # Ввод максимального возраста
    gender_pref = State()    # Выбор предпочитаемого пола
    distance = State()       # Ввод максимального расстояния
    city_filter = State()    # Включение/выключение фильтра по городу

# Обработчик для входа в настройки поиска
async def cmd_search_settings(message: types.Message, state: FSMContext):
    # Сбрасываем предыдущее состояние
    await state.finish()
    
    # Получаем язык пользователя
    lang = await get_user_language(str(message.from_user.id))
    
    # Получаем текущие настройки пользователя
    settings = await get_search_settings_by_telegram_id(str(message.from_user.id))
    
    # Формируем текст с текущими настройками
    if settings:
        # Определяем текст в зависимости от языка
        texts = {
            "ua": {
                "title": "⚙️ Налаштування пошуку",
                "age": "🔢 Вік: {min_age}-{max_age} років",
                "gender": {
                    "чоловік": "👨 Чоловіки",
                    "жінка": "👩 Жінки",
                    None: "👥 Будь-який"
                },
                "distance": "🌍 Відстань пошуку: {distance} км",
                "city_filter": {
                    True: "🏙️ Тільки в моєму місті: Включено",
                    False: "🏙️ Тільки в моєму місті: Вимкнено"
                },
                "choose_option": "Оберіть опцію для зміни:"
            },
            "ru": {
                "title": "⚙️ Настройки поиска",
                "age": "🔢 Возраст: {min_age}-{max_age} лет",
                "gender": {
                    "чоловік": "👨 Мужчины",
                    "жінка": "👩 Женщины",
                    None: "👥 Любой"
                },
                "distance": "🌍 Расстояние поиска: {distance} км",
                "city_filter": {
                    True: "🏙️ Только в моем городе: Включено",
                    False: "🏙️ Только в моем городе: Выключено"
                },
                "choose_option": "Выберите опцию для изменения:"
            },
            "en": {
                "title": "⚙️ Search Settings",
                "age": "🔢 Age: {min_age}-{max_age} years",
                "gender": {
                    "чоловік": "👨 Men",
                    "жінка": "👩 Women",
                    None: "👥 Any"
                },
                "distance": "🌍 Search distance: {distance} km",
                "city_filter": {
                    True: "🏙️ Only in my city: Enabled",
                    False: "🏙️ Only in my city: Disabled"
                },
                "choose_option": "Choose option to change:"
            },
            "de": {
                "title": "⚙️ Sucheinstellungen",
                "age": "🔢 Alter: {min_age}-{max_age} Jahre",
                "gender": {
                    "чоловік": "👨 Männer",
                    "жінка": "👩 Frauen",
                    None: "👥 Beliebig"
                },
                "distance": "🌍 Suchentfernung: {distance} km",
                "city_filter": {
                    True: "🏙️ Nur in meiner Stadt: Aktiviert",
                    False: "🏙️ Nur in meiner Stadt: Deaktiviert"
                },
                "choose_option": "Wählen Sie eine Option zum Ändern:"
            }
        }
        
        t = texts.get(lang, texts["en"])
        
        settings_text = f"{t['title']}\n\n" \
                       f"{t['age'].format(min_age=settings.min_age, max_age=settings.max_age)}\n" \
                       f"{t['gender'].get(settings.preferred_gender, t['gender'][None])}\n" \
                       f"{t['distance'].format(distance=settings.max_distance)}\n" \
                       f"{t['city_filter'][settings.city_filter]}\n\n" \
                       f"{t['choose_option']}"
    else:
        # Если настроек нет, просто показываем меню
        settings_text = "⚙️ Налаштування пошуку"
    
    # Отправляем сообщение с клавиатурой
    await message.answer(
        settings_text,
        reply_markup=get_search_settings_menu(lang)
    )
    
    # Устанавливаем состояние
    await SearchSettingsStates.main_settings.set()

# Обработчик для возвращения в главное меню из настроек
async def back_to_main_menu(message: types.Message, state: FSMContext):
    # Сбрасываем состояние
    await state.finish()
    
    # Получаем язык пользователя
    lang = await get_user_language(str(message.from_user.id))
    
    # Отправляем сообщение с главным меню
    back_text = {
        "ua": "↩️ Повертаємось до головного меню",
        "ru": "↩️ Возвращаемся в главное меню",
        "en": "↩️ Back to main menu",
        "de": "↩️ Zurück zum Hauptmenü"
    }.get(lang, "↩️ Back to main menu")
    
    await message.answer(
        back_text,
        reply_markup=get_main_menu(lang)
    )

# Обработчик выбора опции в меню настроек
async def settings_menu_choice(message: types.Message, state: FSMContext):
    # Получаем язык пользователя
    lang = await get_user_language(str(message.from_user.id))
    
    texts = {
        "ua": {
            "age_range": "🔢 Віковий діапазон",
            "min_age": "Введіть мінімальний вік (від 18):",
            "gender": "👤 Стать",
            "distance": "🌍 Відстань пошуку",
            "enter_distance": "Введіть максимальну відстань пошуку в кілометрах (від 1 до 1000):",
            "city_only": "🏙️ Тільки в моєму місті"
        },
        "ru": {
            "age_range": "🔢 Возрастной диапазон",
            "min_age": "Введите минимальный возраст (от 18):",
            "gender": "👤 Пол",
            "distance": "🌍 Расстояние поиска",
            "enter_distance": "Введите максимальное расстояние поиска в километрах (от 1 до 1000):",
            "city_only": "🏙️ Только в моем городе"
        },
        "en": {
            "age_range": "🔢 Age range",
            "min_age": "Enter minimum age (from 18):",
            "gender": "👤 Gender",
            "distance": "🌍 Search distance",
            "enter_distance": "Enter maximum search distance in kilometers (from 1 to 1000):",
            "city_only": "🏙️ Only in my city"
        },
        "de": {
            "age_range": "🔢 Altersbereich",
            "min_age": "Geben Sie das Mindestalter ein (ab 18):",
            "gender": "👤 Geschlecht",
            "distance": "🌍 Suchentfernung",
            "enter_distance": "Geben Sie die maximale Suchentfernung in Kilometern ein (von 1 bis 1000):",
            "city_only": "🏙️ Nur in meiner Stadt"
        }
    }
    
    t = texts.get(lang, texts["en"])
    text = message.text
    
    # Определяем, какая опция была выбрана
    if t["age_range"] in text:
        await message.answer(t["min_age"])
        await SearchSettingsStates.age_min.set()
    
    elif t["gender"] in text:
        await message.answer(
            "Оберіть бажану стать для пошуку:",
            reply_markup=get_gender_preference_keyboard(lang)
        )
        await SearchSettingsStates.gender_pref.set()
    
    elif t["distance"] in text:
        await message.answer(t["enter_distance"])
        await SearchSettingsStates.distance.set()
    
    elif t["city_only"] in text:
        # Получаем текущие настройки
        settings = await get_search_settings_by_telegram_id(str(message.from_user.id))
        city_filter_active = settings.city_filter if settings else False
        
        await message.answer(
            "Фільтр пошуку тільки в твоєму місті:",
            reply_markup=get_city_filter_keyboard(lang, city_filter_active)
        )
        await SearchSettingsStates.city_filter.set()

# Обработчик для установки минимального возраста
async def set_min_age(message: types.Message, state: FSMContext):
    # Получаем язык пользователя
    lang = await get_user_language(str(message.from_user.id))
    
    texts = {
        "ua": {
            "max_age": "Тепер введіть максимальний вік:",
            "error": "❌ Вік повинен бути числом від 18 років. Спробуйте ще раз:"
        },
        "ru": {
            "max_age": "Теперь введите максимальный возраст:",
            "error": "❌ Возраст должен быть числом от 18 лет. Попробуйте еще раз:"
        },
        "en": {
            "max_age": "Now enter maximum age:",
            "error": "❌ Age must be a number from 18 years. Try again:"
        },
        "de": {
            "max_age": "Geben Sie nun das Höchstalter ein:",
            "error": "❌ Das Alter muss eine Zahl ab 18 Jahren sein. Versuchen Sie es erneut:"
        }
    }
    
    t = texts.get(lang, texts["en"])
    
    # Проверяем, что введено число >= 18
    try:
        min_age = int(message.text)
        if min_age < 18:
            raise ValueError("Age must be at least 18")
        
        # Сохраняем в состояние
        await state.update_data(min_age=min_age)
        
        # Запрашиваем максимальный возраст
        await message.answer(t["max_age"])
        await SearchSettingsStates.age_max.set()
    except ValueError:
        await message.answer(t["error"])

# Обработчик для установки максимального возраста
async def set_max_age(message: types.Message, state: FSMContext):
    # Получаем язык пользователя
    lang = await get_user_language(str(message.from_user.id))
    
    texts = {
        "ua": {
            "success": "✅ Віковий діапазон успішно оновлено",
            "error": "❌ Вік повинен бути числом і більшим за мінімальний. Спробуйте ще раз:"
        },
        "ru": {
            "success": "✅ Возрастной диапазон успешно обновлен",
            "error": "❌ Возраст должен быть числом и больше минимального. Попробуйте еще раз:"
        },
        "en": {
            "success": "✅ Age range successfully updated",
            "error": "❌ Age must be a number and greater than minimum age. Try again:"
        },
        "de": {
            "success": "✅ Altersbereich erfolgreich aktualisiert",
            "error": "❌ Das Alter muss eine Zahl und größer als das Mindestalter sein. Versuchen Sie es erneut:"
        }
    }
    
    t = texts.get(lang, texts["en"])
    
    # Получаем данные из состояния
    data = await state.get_data()
    min_age = data.get("min_age", 18)
    
    # Проверяем, что введено число и оно больше минимального возраста
    try:
        max_age = int(message.text)
        if max_age <= min_age:
            raise ValueError("Max age must be greater than min age")
        
        # Обновляем настройки пользователя
        telegram_id = str(message.from_user.id)
        await update_search_settings(
            telegram_id=telegram_id,
            settings_data={"min_age": min_age, "max_age": max_age}
        )
        
        # Возвращаемся в меню настроек
        await message.answer(t["success"])
        await cmd_search_settings(message, state)
        
    except ValueError:
        await message.answer(t["error"])

# Обработчик выбора предпочитаемого пола
async def set_gender_preference(message: types.Message, state: FSMContext):
    # Получаем язык пользователя
    lang = await get_user_language(str(message.from_user.id))
    
    # Определяем соответствие текста кнопок значениям в базе
    gender_map = {
        # Украинский
        "👨 Чоловіки": "чоловік",
        "👩 Жінки": "жінка",
        "👥 Будь-який": None,
        # Русский
        "👨 Мужчины": "чоловік",
        "👩 Женщины": "жінка",
        "👥 Любой": None,
        # Английский
        "👨 Men": "чоловік",
        "👩 Women": "жінка",
        "👥 Any": None,
        # Немецкий
        "👨 Männer": "чоловік",
        "👩 Frauen": "жінка",
        "👥 Beliebig": None
    }
    
    # Определяем значение пола на основе текста кнопки
    preferred_gender = gender_map.get(message.text)
    
    if preferred_gender is not None or "Any" in message.text or "Будь-який" in message.text or "Любой" in message.text or "Beliebig" in message.text:
        # Обновляем настройки пользователя
        telegram_id = str(message.from_user.id)
        await update_search_settings(
            telegram_id=telegram_id,
            settings_data={"preferred_gender": preferred_gender}
        )
        
        # Локализованное сообщение об успехе
        success_texts = {
            "ua": "✅ Налаштування статі успішно оновлено",
            "ru": "✅ Настройки пола успешно обновлены",
            "en": "✅ Gender settings successfully updated",
            "de": "✅ Geschlechtseinstellungen erfolgreich aktualisiert"
        }
        
        await message.answer(success_texts.get(lang, success_texts["en"]))
        # Возвращаемся в меню настроек
        await cmd_search_settings(message, state)
    
    # Если кнопка "Назад" - просто возвращаемся в меню настроек
    elif "⬅️" in message.text or "Back" in message.text or "Zurück" in message.text or "Назад" in message.text:
        await cmd_search_settings(message, state)

# Обработчик для установки максимального расстояния поиска
async def set_max_distance(message: types.Message, state: FSMContext):
    # Получаем язык пользователя
    lang = await get_user_language(str(message.from_user.id))
    
    texts = {
        "ua": {
            "success": "✅ Відстань пошуку успішно оновлена",
            "error": "❌ Відстань повинна бути числом від 1 до 1000. Спробуйте ще раз:"
        },
        "ru": {
            "success": "✅ Расстояние поиска успешно обновлено",
            "error": "❌ Расстояние должно быть числом от 1 до 1000. Попробуйте еще раз:"
        },
        "en": {
            "success": "✅ Search distance successfully updated",
            "error": "❌ Distance must be a number from 1 to 1000. Try again:"
        },
        "de": {
            "success": "✅ Suchentfernung erfolgreich aktualisiert",
            "error": "❌ Die Entfernung muss eine Zahl von 1 bis 1000 sein. Versuchen Sie es erneut:"
        }
    }
    
    t = texts.get(lang, texts["en"])
    
    # Проверяем, что введено число в допустимом диапазоне
    try:
        max_distance = int(message.text)
        if max_distance < 1 or max_distance > 1000:
            raise ValueError("Distance must be between 1 and 1000")
        
        # Обновляем настройки пользователя
        telegram_id = str(message.from_user.id)
        await update_search_settings(
            telegram_id=telegram_id,
            settings_data={"max_distance": max_distance}
        )
        
        # Возвращаемся в меню настроек
        await message.answer(t["success"])
        await cmd_search_settings(message, state)
        
    except ValueError:
        await message.answer(t["error"])

# Обработчик для включения/выключения фильтра города
async def toggle_city_filter(message: types.Message, state: FSMContext):
    # Получаем язык пользователя
    lang = await get_user_language(str(message.from_user.id))
    
    # Определяем, включаем или выключаем фильтр
    enable_filter = "✅" in message.text or "Enable" in message.text or "aktivieren" in message.text or "Включить" in message.text or "Включити" in message.text
    disable_filter = "❌" in message.text or "Disable" in message.text or "deaktivieren" in message.text or "Выключить" in message.text or "Вимкнути" in message.text
    
    # Локализованное сообщение об успехе
    success_texts = {
        "ua": {
            True: "✅ Фільтр міста увімкнено",
            False: "✅ Фільтр міста вимкнено"
        },
        "ru": {
            True: "✅ Фильтр города включен",
            False: "✅ Фильтр города выключен"
        },
        "en": {
            True: "✅ City filter enabled",
            False: "✅ City filter disabled"
        },
        "de": {
            True: "✅ Stadtfilter aktiviert",
            False: "✅ Stadtfilter deaktiviert"
        }
    }
    
    if enable_filter or disable_filter:
        # Устанавливаем значение фильтра
        city_filter = enable_filter
        
        # Обновляем настройки пользователя
        telegram_id = str(message.from_user.id)
        await update_search_settings(
            telegram_id=telegram_id,
            settings_data={"city_filter": city_filter}
        )
        
        # Отправляем сообщение об успехе
        await message.answer(success_texts.get(lang, success_texts["en"])[city_filter])
        
        # Возвращаемся в меню настроек
        await cmd_search_settings(message, state)
    
    # Если кнопка "Назад" - просто возвращаемся в меню настроек
    elif "⬅️" in message.text or "Back" in message.text or "Zurück" in message.text or "Назад" in message.text:
        await cmd_search_settings(message, state)

# Функция регистрации обработчиков
def register_search_settings_handlers(dp: Dispatcher):
    # Обработчик входа в настройки поиска
    dp.register_message_handler(
        cmd_search_settings, 
        lambda m: "⚙️" in m.text and ("Налаштування" in m.text or "Настройки" in m.text or "Settings" in m.text or "Sucheinstellungen" in m.text),
        state="*"
    )
    
    # Обработчик возвращения в главное меню
    dp.register_message_handler(
        back_to_main_menu, 
        lambda m: "⬅️" in m.text and ("Назад до меню" in m.text or "Назад в меню" in m.text or "Back to menu" in m.text or "Zurück zum Menü" in m.text),
        state=SearchSettingsStates.main_settings
    )
    
    # Обработчик выбора опции в меню настроек
    dp.register_message_handler(
        settings_menu_choice,
        state=SearchSettingsStates.main_settings
    )
    
    # Обработчики для установки возрастного диапазона
    dp.register_message_handler(
        set_min_age,
        state=SearchSettingsStates.age_min
    )
    
    dp.register_message_handler(
        set_max_age,
        state=SearchSettingsStates.age_max
    )
    
    # Обработчик для выбора предпочитаемого пола
    dp.register_message_handler(
        set_gender_preference,
        state=SearchSettingsStates.gender_pref
    )
    
    # Обработчик для установки максимального расстояния поиска
    dp.register_message_handler(
        set_max_distance,
        state=SearchSettingsStates.distance
    )
    
    # Обработчик для включения/выключения фильтра города
    dp.register_message_handler(
        toggle_city_filter,
        state=SearchSettingsStates.city_filter
    )
