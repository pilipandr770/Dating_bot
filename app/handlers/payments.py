from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from sqlalchemy import select
from datetime import datetime

from app.database import get_session
from app.models.user import User
from app.models.payments import Payment, PaymentType, PaymentStatus
from app.services.stripe import create_checkout_session

ADMIN_TELEGRAM_ID = 123456789  # 🔁 Заміни на свій Telegram ID

# 💳 /pay — меню оплати
async def payments_menu(message: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💎 Premium (1 міс)", callback_data="buy_subscription_premium"),
        types.InlineKeyboardButton("🚀 Pro (3 міс)", callback_data="buy_subscription_pro"),
        types.InlineKeyboardButton("👑 VIP (12 міс)", callback_data="buy_subscription_vip"),
        types.InlineKeyboardButton("🪙 Купити токени (10€)", callback_data="buy_tokens")
    )
    await message.answer("💳 Оберіть варіант оплати:", reply_markup=kb)


# 🔘 Callback
async def handle_payment_callback(call: types.CallbackQuery):
    await call.answer()
    user_id = str(call.from_user.id)
    action = call.data

    if action.startswith("buy_subscription_"):
        plan = action.replace("buy_subscription_", "")
        session_url = await create_checkout_session(user_id, plan_type=plan)
        if session_url:
            await call.message.answer(f"🔗 Перейдіть до оплати:\n{session_url}")
    elif action == "buy_tokens":
        session_url = await create_checkout_session(user_id, token_pack=True)
        if session_url:
            await call.message.answer(f"💰 Купівля токенів (10€):\n{session_url}")
    else:
        await call.message.answer("⚠️ Невідома дія.")


# 🔄 /confirm — тимчасове підтвердження
async def confirm_payment(message: types.Message):
    tg_id = str(message.from_user.id)

    async for session in get_session():
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not user:
            return await message.answer("⚠️ Спершу зареєструйся.")

        user.is_premium = True

        payment = Payment(
            user_id=user.id,
            amount=10.0,
            currency="eur",
            status=PaymentStatus.confirmed,
            timestamp=datetime.utcnow()
        )
        session.add(payment)
        await session.commit()

        await message.answer("🎉 Платіж підтверджено. Ти Premium!", parse_mode="Markdown")


# 💰 /balance
async def check_token_balance(message: types.Message):
    tg_id = str(message.from_user.id)

    async for session in get_session():
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not user:
            return await message.answer("⚠️ Тебе не знайдено.")
        await message.answer(f"🔐 Твій баланс токенів: {user.token_balance or 0}")


# 🔁 /transfer 5 987654321
async def transfer_tokens(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) != 3:
        return await message.answer("❗ Приклад: /transfer 5 987654321")

    amount = int(parts[1])
    recipient_tg_id = parts[2]
    sender_tg_id = str(message.from_user.id)

    if amount <= 0:
        return await message.answer("❌ Неправильна сума.")

    async for session in get_session():
        sender = await session.scalar(select(User).where(User.telegram_id == sender_tg_id))
        recipient = await session.scalar(select(User).where(User.telegram_id == recipient_tg_id))

        if not sender or not recipient:
            return await message.answer("❗ Користувача не знайдено.")

        if sender.token_balance < amount:
            return await message.answer("🚫 Недостатньо токенів.")

        # Комісія 1%
        fee = max(1, amount // 100)
        net_amount = amount - fee

        sender.token_balance -= amount
        recipient.token_balance += net_amount

        session.add(Payment(
            user_id=sender.id,
            type=PaymentType.transfer,
            amount=amount,
            status=PaymentStatus.confirmed,
            recipient_id=recipient.id,
            currency="tokens",
            timestamp=datetime.utcnow()
        ))
        await session.commit()

        await message.answer(f"✅ Ти надіслав {net_amount} токенів. Комісія: {fee} токенів.")
        try:
            await message.bot.send_message(int(recipient.telegram_id), f"📥 Отримано {net_amount} токенів від {sender.first_name}!")
        except:
            pass


# 🔄 /sell 20 — запит на продаж токенів
async def sell_tokens(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        return await message.answer("❗ Приклад: /sell 20")

    amount = int(parts[1])
    tg_id = str(message.from_user.id)

    async for session in get_session():
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not user or not user.is_verified:
            return await message.answer("🚫 Тільки верифіковані користувачі можуть продавати токени.")

        if user.token_balance < amount:
            return await message.answer("🚫 Недостатньо токенів.")

        euro = amount * 0.9

        # Відправити повідомлення адміну
        try:
            await message.bot.send_message(
                ADMIN_TELEGRAM_ID,
                f"💸 Запит на продаж токенів від {user.first_name} (@{message.from_user.username})\n"
                f"Сума: {amount} токенів = {euro:.2f}€\nTelegram ID: {tg_id}"
            )
        except:
            pass

        await message.answer("📤 Запит на продаж надіслано адміну. Очікуй підтвердження.")


# 🔌 Реєстрація
def register_payment_handlers(dp: Dispatcher):
    dp.register_message_handler(payments_menu, commands=["pay"])
    dp.register_message_handler(confirm_payment, commands=["confirm"])
    dp.register_message_handler(check_token_balance, commands=["balance"])
    dp.register_message_handler(transfer_tokens, commands=["transfer"])
    dp.register_message_handler(sell_tokens, commands=["sell"])
    dp.register_callback_query_handler(handle_payment_callback, Text(startswith="buy_"))

