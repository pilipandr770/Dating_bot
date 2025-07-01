from aiogram import types, Dispatcher
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select, or_
from app.models.match import Match
from app.models.user import User
from app.models.messages import Message
from app.models.reports import Report
from app.database import get_session
from app.services.assistant import analyze_message, analyze_chat
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatState(StatesGroup):
    in_chat = State()
    waiting_for_analysis = State()

# Визначаємо ai_advice_handler на початку файлу
async def ai_advice_handler(message: types.Message, state: FSMContext):
    """Handler for AI advice requests in chats"""
    logger.info(f"AI порада запитана користувачем {message.from_user.id}")
    tg_id = str(message.from_user.id)
    
    await message.answer("⏳ Аналізую ваше спілкування...")
    await ChatState.waiting_for_analysis.set()
    
    try:
        # Get current thread_id from state
        data = await state.get_data()
        thread_id = data.get("thread_id")
        
        if not thread_id:
            await message.answer("❌ Помилка: не вдалося визначити активний чат.")
            await ChatState.in_chat.set()
            return
            
        # Get user ID for context
        async for session in get_session():
            user = await session.scalar(select(User).where(User.telegram_id == tg_id))
            if not user:
                await message.answer("⚠️ Помилка доступу.")
                await ChatState.in_chat.set()
                return
                
            # Get AI analysis
            logger.info(f"Запит на аналіз для thread_id={thread_id}, user_id={user.id}")
            analysis = await analyze_chat(thread_id, user.id)
            
            # Create keyboard with back option
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("⬅️ Вийти з чату"))
            
            # Send the analysis to the user
            await message.answer(analysis, reply_markup=kb)
            
            # Return to chat state
            await ChatState.in_chat.set()
            
    except Exception as e:
        logger.error(f"Помилка AI поради: {str(e)}")
        await message.answer(f"❌ Помилка при отриманні поради: {str(e)}")
        await ChatState.in_chat.set()

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
            # Import the main menu keyboard
            from app.keyboards.main_menu import get_main_menu
            lang = getattr(me, 'language', 'ua')  # Default to 'ua' if not set
            main_menu = get_main_menu(lang)
            return await message.answer("😔 У тебе ще немає матчів.", reply_markup=main_menu)

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for m in matches:
            other_id = m.user_2_id if m.user_1_id == me.id else m.user_1_id
            other = await session.scalar(select(User).where(User.id == other_id))
            if other:
                kb.add(KeyboardButton(f"💬 {other.first_name} ({m.thread_id})"))
        
        # Add exit button in user's language
        kb.add(KeyboardButton("⬅️ Вийти з чату"))

        await message.answer("Оберіть, з ким хочеш поспілкуватися:", reply_markup=kb)
        await ChatState.in_chat.set()
        
        # Clear any previous chat state data
        await state.update_data(thread_id=None)

from aiogram.dispatcher.filters import Text

# Прийом повідомлення під час активного чату
# файл: app/handlers/chat.py

async def in_chat_handler(message: types.Message, state: FSMContext):
    text = message.text
    tg_id = str(message.from_user.id)

    # Exit early for special commands
    if "Вийти з чату" in text or "⬅️" in text:
        return
        
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
                # Add a back button
                kb = ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(KeyboardButton("⬅️ Вийти з чату"))
                return await message.answer("🔸 Напиши повідомлення — я передам його твоєму метчу.", reply_markup=kb)
            else:
                # Return to match selection if message format is invalid
                return await message.answer("❌ Не знайдено thread_id, спробуйте знову обрати співрозмовника.")

        try:
            # Зберігаємо повідомлення в БД
            msg = Message(
                thread_id=thread_id,
                sender_id=me.id,
                message_text=text
            )
            session.add(msg)
            await session.flush()  # Make sure message is saved before proceeding
            
            # Знаходимо одержувача
            match = await session.scalar(select(Match).where(Match.thread_id == thread_id))
            if not match:
                await message.answer("❌ Помилка: чат не знайдено. Спробуйте знову.")
                await state.finish()
                from app.keyboards.main_menu import get_main_menu
                return await message.answer("Повертаємось до головного меню", 
                                           reply_markup=get_main_menu(getattr(me, 'language', 'ua')))
                
            receiver_id = match.user_2_id if match.user_1_id == me.id else match.user_1_id
            receiver = await session.scalar(select(User).where(User.id == receiver_id))
    
            # Надсилаємо повідомлення одержувачу
            if receiver:
                try:
                    # Create keyboard for the receiver to reply with an AI assistant button
                    receiver_kb = ReplyKeyboardMarkup(resize_keyboard=True)
                    receiver_kb.add(KeyboardButton(f"💬 {me.first_name} ({thread_id})"))
                    receiver_kb.add(KeyboardButton("🤖 AI Порада"), KeyboardButton("⬅️ Вийти з чату"))
                    
                    # Важливо! Встановлюємо стан отримувача вручну, щоб він міг відповідати
                    from aiogram import Bot
                    from aiogram.dispatcher import FSMContext
                    from aiogram.dispatcher import Dispatcher
                    
                    # Отримуємо dispatcher з бота
                    dp = Dispatcher.get_current()
                    if dp:
                        # Створюємо state для отримувача
                        receiver_state = FSMContext(dp.storage, receiver.telegram_id, receiver.telegram_id)
                        
                        # Встановлюємо стан і thread_id для отримувача
                        await receiver_state.set_state(ChatState.in_chat.state)
                        await receiver_state.update_data(thread_id=thread_id)
                        print(f"✅ Встановлено стан для отримувача {receiver.telegram_id}")
                    
                    # Надсилаємо повідомлення
                    sent_msg = await message.bot.send_message(
                        chat_id=int(receiver.telegram_id),
                        text=f"💬 Повідомлення від {me.first_name}:\n\n{text}",
                        reply_markup=receiver_kb
                    )
                    
                    # Додаємо додаткову інструкцію для отримувача
                    await message.bot.send_message(
                        chat_id=int(receiver.telegram_id),
                        text=f"🔹 Для відповіді {me.first_name} просто напишіть текст у цьому чаті"
                    )
                    
                    # Update sender's keyboard to include AI advice button
                    kb = ReplyKeyboardMarkup(resize_keyboard=True)
                    kb.add(KeyboardButton("🤖 AI Порада"), KeyboardButton("⬅️ Вийти з чату"))
                    await message.answer("✅ Повідомлення надіслано", reply_markup=kb)
                except Exception as e:
                    print(f"Помилка при відправці повідомлення: {e}")
                    await message.answer(f"⚠️ Не вдалося доставити повідомлення: {e}")
            else:
                await message.answer("⚠️ Користувач не знайдений")
        except Exception as e:
            await message.answer(f"❌ Помилка при обробці повідомлення: {str(e)}")

        # Commit all changes to database
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            await message.answer(f"⚠️ Помилка при збереженні повідомлення: {str(e)}")

# Вихід із чату
async def exit_chat(message: types.Message, state: FSMContext):
    # Get user language for main menu
    tg_id = str(message.from_user.id)
    lang = 'ua'  # Default language
    
    async for session in get_session():
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if user and user.language:
            lang = user.language
    
    # Import and show the main menu keyboard
    from app.keyboards.main_menu import get_main_menu
    main_menu = get_main_menu(lang)
    
    # Clear the state and return to main menu
    await state.finish()
    await message.answer("📤 Ти вийшов(-ла) з чату.", reply_markup=main_menu)

# Функцію ai_advice_handler перенесено на початок файлу

ADMIN_ID = 7444992311  # заміни на свій Telegram ID

async def handle_report(callback_query: types.CallbackQuery):
    data = callback_query.data
    reporter_id = str(callback_query.from_user.id)

    if data.startswith("report_"):
        reported_id = int(data.split("_")[1])
        await callback_query.answer("🚨 Скарга відправлена модератору.")
        
        # Save report to database
        async for session in get_session():
            # Get user IDs from database
            reporter = await session.scalar(select(User).where(User.telegram_id == reporter_id))
            
            if reporter:
                from app.models.reports import Report
                report = Report(
                    reporter_id=reporter.id,
                    reported_id=reported_id,  # This is already the user ID, not telegram_id
                    reason="User reported through chat"
                )
                session.add(report)
                await session.commit()

        # Also notify admin
        text = f"⚠️ Користувач {reporter_id} поскаржився на {reported_id}."
        try:
            await callback_query.bot.send_message(chat_id=ADMIN_ID, text=text)
        except:
            await callback_query.message.answer("❌ Не вдалося надіслати скаргу адміну.")



# Спеціальний обробник для автоматичного вибору чату при натисканні кнопки зі співрозмовником
async def auto_select_chat(message: types.Message, state: FSMContext):
    """Автоматично вибирає співрозмовника при натисканні на кнопку з thread_id"""
    text = message.text
    tg_id = str(message.from_user.id)
    
    # Перевіряємо формат повідомлення (повинно містити thread_id у дужках)
    if "(" in text and ")" in text:
        thread_id = text.split("(")[-1].strip(")")
        logger.info(f"Автоматичний вибір чату з thread_id={thread_id}")
        
        # Встановлюємо thread_id у стан
        await state.update_data(thread_id=thread_id)
        await ChatState.in_chat.set()
        
        # Показуємо клавіатуру з кнопками для чату
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🤖 AI Порада"), KeyboardButton("⬅️ Вийти з чату"))
        
        await message.answer("🔸 Тепер можете написати повідомлення — я передам його співрозмовнику.", reply_markup=kb)
        return True
    
    return False

def register_chat_handlers(dp: Dispatcher):
    dp.register_message_handler(choose_match, commands=["chat"])
    
    # Підтримка кнопки "Мої матчі" для різних мов
    dp.register_message_handler(choose_match, lambda m: any(
        match_text in m.text for match_text in ["Мої матчі", "Мои матчи", "My matches", "Meine Matches"]
    ))
    
    # Support for exit button with translations
    dp.register_message_handler(exit_chat, lambda m: "Вийти з чату" in m.text or "⬅️" in m.text, state=ChatState.in_chat)
    
    # Handle AI advice requests - this needs to be registered BEFORE the general message handler
    try:
        dp.register_message_handler(ai_advice_handler, lambda m: "AI Порада" in m.text or "🤖" in m.text, state=ChatState.in_chat)
        print("✅ AI порада handler зареєстрований успішно")
    except NameError:
        print("⚠️ Помилка: ai_advice_handler не знайдено. Функція AI поради не буде працювати.")
    
    # Автоматичний вибір співрозмовника при натисканні кнопки з thread_id
    dp.register_message_handler(auto_select_chat, lambda m: "💬" in m.text and "(" in m.text and ")" in m.text, state="*")
    
    # Handle regular chat messages (must be last)
    dp.register_message_handler(in_chat_handler, state=ChatState.in_chat)
