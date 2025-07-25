﻿from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, MediaGroup
from sqlalchemy import select, not_, exists
from app.database import get_session
from app.models.user import User
from app.models.swipes import Swipe
from app.models.reports import Report
from app.services.user_service import get_user_language, get_user_photos
from app.keyboards.main_menu import get_main_menu
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функція для початку свайпів
async def cmd_start_swipes(message: types.Message):
    # Отримуємо мову користувача для клавіатури
    user_id = message.from_user.id
    lang = await get_user_language(str(user_id))
    
    # Показуємо перший профіль без зайвих повідомлень, 
    # адже головне меню вже показано після збереження анкети
    await show_next_profile(message)

async def show_next_profile(message: types.Message):
    current_user_id = str(message.from_user.id)

    async for session in get_session():
        # Отримуємо поточного користувача
        me = await session.scalar(select(User).where(User.telegram_id == current_user_id))
        if not me:
            return await message.answer("⚠️ Твоя анкета ще не створена. Спочатку зареєструйся.")

        # Import BlockedUser model
        from app.models.blocked_users import BlockedUser
        
        # Пошук відповідного партнера на основі статі та орієнтації
        stmt = (
            select(User)
            .where(User.id != me.id)
            .where(
                not_(
                    exists().where(Swipe.swiper_id == me.id).where(Swipe.swiped_id == User.id)
                )
            )
            # Исключаем пользователей, которые заблокировали текущего пользователя
            .where(
                not_(
                    exists().where(BlockedUser.blocker_id == User.id).where(BlockedUser.blocked_id == me.id)
                )
            )
            # Исключаем пользователей, которых заблокировал текущий пользователь
            .where(
                not_(
                    exists().where(BlockedUser.blocker_id == me.id).where(BlockedUser.blocked_id == User.id)
                )
            )
        )
        
        # Получаем пользовательские настройки поиска
        from app.services.search_settings_service import get_search_settings_by_telegram_id
        settings = await get_search_settings_by_telegram_id(current_user_id)
        
        # Если настроек нет, используем стандартные фильтры, иначе применяем пользовательские
        if not settings:
            # Додаємо фільтрацію за статтю та орієнтацією
            # Спочатку визначаємо, хто може подобатися поточному користувачеві
            if me.orientation == "гетеро":
                # Гетеро людям подобається протилежна стать
                if me.gender == "чоловік":
                    stmt = stmt.where(User.gender == "жінка")
                elif me.gender == "жінка":
                    stmt = stmt.where(User.gender == "чоловік")
            elif me.orientation == "гомо":
                # Гомо людям подобається та ж стать
                stmt = stmt.where(User.gender == me.gender)
            elif me.orientation == "бі":
                # Бі людям можуть подобатися всі, тому додаткової фільтрації не потрібно
                pass
            
            # Тепер фільтруємо за орієнтацією потенційних партнерів
            # Нам потрібно показувати тільки тих, кому теоретично може сподобатися поточний користувач
            if me.gender == "чоловік":
                # Поточний користувач - чоловік, тому показуємо:
                # - гетеро жінок
                # - гомо чоловіків
                # - бі обох статей
                stmt = stmt.where(
                    (User.orientation == "бі") |
                    ((User.gender == "жінка") & (User.orientation == "гетеро")) |
                    ((User.gender == "чоловік") & (User.orientation == "гомо"))
                )
            elif me.gender == "жінка":
                # Поточний користувач - жінка, тому показуємо:
                # - гетеро чоловіків
                # - гомо жінок
                # - бі обох статей
                stmt = stmt.where(
                    (User.orientation == "бі") |
                    ((User.gender == "чоловік") & (User.orientation == "гетеро")) |
                    ((User.gender == "жінка") & (User.orientation == "гомо"))
                )
            
            # Додаємо фільтрацію за віком (стандартний діапазон ±5 років)
            # За замовчуванням показуємо людей у віковому діапазоні ±5 років від поточного користувача
            if me.age:
                min_age = max(18, me.age - 5)  # Мінімум 18 років
                max_age = me.age + 5
                stmt = stmt.where(User.age >= min_age)
                stmt = stmt.where(User.age <= max_age)
        else:
            # Применяем пользовательские настройки поиска
            
            # Фильтрация по возрасту
            stmt = stmt.where(User.age >= settings.min_age)
            stmt = stmt.where(User.age <= settings.max_age)
            
            # Фильтрация по полу (если указан конкретный пол)
            if settings.preferred_gender:
                stmt = stmt.where(User.gender == settings.preferred_gender)
            
            # Проверяем, нужно ли фильтровать по городу
            if settings.city_filter and me.city:
                stmt = stmt.where(User.city == me.city)
            
            # Здесь можно добавить фильтрацию по расстоянию,
            # если в базе данных есть координаты пользователей
            # Для этого нужно использовать функции геолокации из app.services.geo
        
        # Обмежуємо результат одним користувачем
        stmt = stmt.limit(1)
        candidate = await session.scalar(stmt)

        if candidate:
            # Removed is_flagged check since this field no longer exists
            flag_note = ""

            # Побудова клавіатури свайпу
            kb = InlineKeyboardMarkup(row_width=3)  # Changed row_width to accommodate the new button
            kb.add(
                InlineKeyboardButton("❤️", callback_data=f"like_{candidate.id}"),
                InlineKeyboardButton("❌", callback_data=f"dislike_{candidate.id}"),
                InlineKeyboardButton("🚫", callback_data=f"block_{candidate.id}")  # Added block button
            )

            # Отримуємо фотографії кандидата
            from app.services.user_service import get_user_photos
            photo_file_ids = await get_user_photos(candidate.id)
            
            # Логируем для отладки
            print(f"📸 Для профиля ID={candidate.id} ({candidate.first_name}) найдено {len(photo_file_ids) if photo_file_ids else 0} фотографий")
            
            # Створюємо текст анкети
            profile_text = f"{flag_note}👤 {candidate.first_name}, {candidate.age}\n" \
                          f"🏙 {candidate.city}\n📝 {candidate.bio or '—'}"
            
            # Якщо є фото - відправляємо медіа групою
            if photo_file_ids and len(photo_file_ids) > 0:
                # Якщо є тільки одне фото - відправляємо його з підписом і клавіатурою
                if len(photo_file_ids) == 1:
                    await message.answer_photo(
                        photo=photo_file_ids[0],
                        caption=profile_text,
                        reply_markup=kb
                    )
                else:
                    # Якщо багато фото - відправляємо медіа групою
                    media_group = []
                    for i, file_id in enumerate(photo_file_ids):
                        # До першого фото додаємо підпис з даними анкети
                        if i == 0:
                            media_group.append(types.InputMediaPhoto(
                                media=file_id,
                                caption=profile_text
                            ))
                        else:
                            media_group.append(types.InputMediaPhoto(media=file_id))
                            
                    # Відправляємо медіа групу
                    await message.answer_media_group(media_group)
                    # Відправляємо клавіатуру окремим повідомленням
                    await message.answer("Оцініть цю анкету:", reply_markup=kb)
            else:
                # Якщо немає фото - просто відправляємо текст
                await message.answer(profile_text, reply_markup=kb)
        else:
            await message.answer("😔 На жаль, більше анкет поки що немає.")

from app.models.swipes import Swipe
from app.models.match import Match
import uuid

# Обробка свайпу
async def handle_swipe(callback_query: types.CallbackQuery):
    data = callback_query.data
    telegram_id = str(callback_query.from_user.id)

    action, target_id_str = data.split("_")
    target_id = int(target_id_str)

    async for session in get_session():
        me = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if not me:
            return await callback_query.message.answer("⚠️ Твоя анкета ще не створена.")

        # Зберігаємо свайп
        swipe = Swipe(
            swiper_id=me.id,
            swiped_id=target_id,
            is_like=(action == "like")
        )
        session.add(swipe)
        await session.flush()

        # Якщо це лайк — перевіряємо на взаємність
        if action == "like":
            mutual = await session.scalar(
                select(Swipe).where(
                    Swipe.swiper_id == target_id,
                    Swipe.swiped_id == me.id,
                    Swipe.is_like == True
                )
            )
            if mutual:
                # Створюємо match
                thread = str(uuid.uuid4())
                match = Match(
                    user_1_id=me.id,
                    user_2_id=target_id,
                    thread_id=thread
                )
                session.add(match)
                await callback_query.message.answer("🎉 У вас взаємний лайк! Можна починати чат ❤️")

        await session.commit()

    await callback_query.message.delete()
    await callback_query.answer()
    # Показываем следующую анкету автоматически
    await show_next_profile(callback_query.message)

ADMIN_ID = 7444992311  # Замінити на свій Telegram ID

async def handle_report(callback_query: types.CallbackQuery):
    data = callback_query.data
    reporter_id = str(callback_query.from_user.id)

    if data.startswith("report_"):
        reported_id = int(data.split("_")[1])
        await callback_query.answer("🚨 Скарга відправлена модератору.")
        
        # Save report to database
        async for session in get_session():
            # Get user ID from database
            reporter = await session.scalar(select(User).where(User.telegram_id == reporter_id))
            
            if reporter:
                from app.models.reports import Report
                report = Report(
                    reporter_id=reporter.id,
                    reported_id=reported_id,
                    reason="User reported through swipes"
                )
                session.add(report)
                await session.commit()

        # Also notify admin
        text = f"⚠️ Нове повідомлення про скаргу\n" \
               f"Від користувача: {reporter_id}\n" \
               f"На користувача: {reported_id}"

        try:
            await callback_query.bot.send_message(chat_id=ADMIN_ID, text=text)
        except:
            await callback_query.message.answer("❌ Не вдалося надіслати скаргу адміну.")

async def handle_block(callback_query: types.CallbackQuery):
    data = callback_query.data
    telegram_id = str(callback_query.from_user.id)

    if not data.startswith("block_"):
        return
    target_id = int(data.split("_")[1])

    async for session in get_session():
        me = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if not me:
            return await callback_query.message.answer("⚠️ Твоя анкета ще не створена.")

        # Проверяем, не заблокирован ли уже
        from app.models.blocked_users import BlockedUser
        exists_block = await session.scalar(
            select(BlockedUser).where(
                BlockedUser.blocker_id == me.id,
                BlockedUser.blocked_id == target_id
            )
        )
        if not exists_block:
            block = BlockedUser(blocker_id=me.id, blocked_id=target_id)
            session.add(block)
            await session.commit()
            await callback_query.message.answer("🚫 Користувача заблоковано. Наступна анкета:")
        else:
            await callback_query.message.answer("🚫 Користувач вже заблокований. Наступна анкета:")

    await callback_query.message.delete()
    await callback_query.answer()
    # Показываем наступну анкету
    await show_next_profile(callback_query.message)

def register_swipe_handlers(dp: Dispatcher):
    # Регистрация обработчика для кнопки "Знайомитись" на кількох мовах
    dp.register_message_handler(cmd_start_swipes, lambda m: "Знайомитись" in m.text or "Знакомиться" in m.text or "Meet people" in m.text or "Leute kennenlernen" in m.text)
    dp.register_callback_query_handler(handle_swipe, lambda c: c.data.startswith(("like_", "dislike_")))
    dp.register_callback_query_handler(handle_block, lambda c: c.data.startswith("block_"))
    dp.register_callback_query_handler(handle_report, lambda c: c.data.startswith("report_"))
