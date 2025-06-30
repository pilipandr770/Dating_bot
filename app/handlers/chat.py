from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select, or_
from app.models.matches import Match
from app.models.user import User
from app.models.messages import Message
from app.database import get_session

class ChatState(StatesGroup):
    in_chat = State()

# Команда /chat або "Мої матчі"
async def choose_match(message: types.Message, state: FSMContext):
    tg_id = str(message.from_user.id)

    async for session in get_session():
        me = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not me:
            return await message.answer("⚠️ Ти ще не зареєстрований.")

        stmt = select(Match).where(or_(
            Match.user_1_id == me.id,
            Match.user_2_id == me.id
        ))
        matches = await session.scalars(stmt)
        matches = matches.all()

        if not matches:
            return await message.answer("😔 У тебе ще немає матчів.")

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for m in matches:
            other_id = m.user_2_id if m.user_1_id == me.id else m.user_1_id
            other = await session.scalar(select(User).where(User.id == other_id))
            if other:
                kb.add(KeyboardButton(f"💬 {other.first_name} ({m.thread_id})"))

        await message.answer("Оберіть, з ким хочеш поспілкуватися:", reply_markup=kb)
        await ChatState.in_chat.set()

from aiogram.dispatcher.filters import Text

# Прийом повідомлення під час активного чату
# файл: app/handlers/chat.py

from app.services.assistant import analyze_message

async def in_chat_handler(message: types.Message, state: FSMContext):
    text = message.text
    tg_id = str(message.from_user.id)

    async for session in get_session():
        me = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not me:
            return await message.answer("⚠️ Помилка доступу.")

        current = await state.get_state()
        if current != ChatState.in_chat.state:
            return

        # Витягаємо активний thread_id
        data = await state.get_data()
        thread_id = data.get("thread_id")

        if not thread_id:
            # Вперше обрано співрозмовника
            if "(" in text and ")" in text:
                thread_id = text.split("(")[-1].strip(")")
                await state.update_data(thread_id=thread_id)
                return await message.answer("🔸 Напиши повідомлення — я передам його твоєму метчу.")
            else:
                return await message.answer("❌ Не знайдено thread_id")

        # Зберігаємо повідомлення в БД
        msg = Message(
            thread_id=thread_id,
            sender_id=me.id,
            message_text=text
        )
        session.add(msg)

        # Знаходимо одержувача
        match = await session.scalar(select(Match).where(Match.thread_id == thread_id))
        receiver_id = match.user_2_id if match.user_1_id == me.id else match.user_1_id
        receiver = await session.scalar(select(User).where(User.id == receiver_id))

        # Надсилаємо повідомлення одержувачу
        if receiver:
            try:
                await message.bot.send_message(
                    chat_id=int(receiver.telegram_id),
                    text=f"💬 Повідомлення від {me.first_name}:\n\n{text}"
                )
            except Exception as e:
                await message.answer(f"⚠️ Не вдалося доставити повідомлення: {e}")

        # 🔍 AI-аналітика
        ai_result = await analyze_message(text, me.id, thread_id)
        if ai_result:
            await message.answer(f"🤖 AI-аналіз: {ai_result}")
# Позначити користувача як підозрілого
            me.is_flagged = True
            await session.commit()

            await session.commit()
            await message.answer("✅ Повідомлення надіслано.")

# Вихід із чату
async def exit_chat(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("📤 Ти вийшов(-ла) з чату.")

ADMIN_ID = 7444992311  # заміни на свій Telegram ID

async def handle_report(callback_query: types.CallbackQuery):
    data = callback_query.data
    reporter_id = str(callback_query.from_user.id)

    if data.startswith("report_"):
        reported_id = int(data.split("_")[1])
        await callback_query.answer("🚨 Скарга відправлена модератору.")

        text = f"⚠️ Користувач {reporter_id} поскаржився на {reported_id}."

        try:
            await callback_query.bot.send_message(chat_id=ADMIN_ID, text=text)
        except:
            await callback_query.message.answer("❌ Не вдалося надіслати скаргу адміну.")



def register_chat_handlers(dp: Dispatcher):
    dp.register_message_handler(choose_match, commands=["chat"])
    dp.register_message_handler(choose_match, lambda m: "Мої матчі" in m.text)
    dp.register_message_handler(exit_chat, Text(equals="Вийти з чату", ignore_case=True), state=ChatState.in_chat)
    dp.register_message_handler(in_chat_handler, state=ChatState.in_chat)

def register_swipe_handlers(dp: Dispatcher):
    dp.register_message_handler(show_next_profile, lambda m: "Знайти пару" in m.text)
    dp.register_callback_query_handler(handle_swipe, lambda c: c.data.startswith(("like_", "dislike_")))
    dp.register_callback_query_handler(handle_report, lambda c: c.data.startswith("report_"))
