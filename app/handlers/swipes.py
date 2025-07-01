from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, not_, exists
from app.database import get_session
from app.models.user import User
from app.models.swipes import Swipe
from app.models.reports import Report
from app.services.user_service import get_user_language
from app.keyboards.main_menu import get_main_menu

# Функция для начала свайпов
async def cmd_start_swipes(message: types.Message):
    # Получаем язык пользователя для клавиатуры
    user_id = message.from_user.id
    lang = await get_user_language(str(user_id))
    
    # Показываем первый профиль без лишних сообщений, 
    # т.к. главное меню уже показано после сохранения анкеты
    await show_next_profile(message)

async def show_next_profile(message: types.Message):
    current_user_id = str(message.from_user.id)

    async for session in get_session():
        # Отримуємо поточного користувача
        me = await session.scalar(select(User).where(User.telegram_id == current_user_id))
        if not me:
            return await message.answer("⚠️ Твоя анкета ще не створена. Спочатку зареєструйся.")

        # Пошук користувача, якого ще не свайпнули
        stmt = (
            select(User)
            .where(User.id != me.id)
            .where(
                not_(
                    exists().where(Swipe.swiper_id == me.id).where(Swipe.swiped_id == User.id)
                )
            )
            .limit(1)
        )
        candidate = await session.scalar(stmt)

        if candidate:
            # Removed is_flagged check since this field no longer exists
            flag_note = ""

            # Побудова клавіатури свайпу
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("❤️", callback_data=f"like_{candidate.id}"),
                InlineKeyboardButton("❌", callback_data=f"dislike_{candidate.id}")
            )

            # Вивід анкети
            await message.answer(
                f"{flag_note}👤 {candidate.first_name}, {candidate.age}\n"
                f"🏙 {candidate.city}\n📝 {candidate.bio or '—'}",
                reply_markup=kb
            )
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
        
        # Зберігаємо відразу, щоб уникнути проблем
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

                # Повідомляємо обох (поки лише себе)
                await callback_query.message.answer("🎉 У вас взаємний лайк! Можна починати чат ❤️")

        await session.commit()

    await callback_query.message.delete()
    await callback_query.answer()


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


def register_swipe_handlers(dp: Dispatcher):
    # Регистрация обработчика для кнопки "Знайомитись" на нескольких языках
    dp.register_message_handler(cmd_start_swipes, lambda m: "Знайомитись" in m.text or "Знакомиться" in m.text or "Meet people" in m.text or "Leute kennenlernen" in m.text)
    dp.register_callback_query_handler(handle_swipe, lambda c: c.data.startswith(("like_", "dislike_")))
    dp.register_callback_query_handler(handle_report, lambda c: c.data.startswith("report_"))
