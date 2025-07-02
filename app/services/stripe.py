# файл: app/services/stripe.py

import stripe
import os
from dotenv import load_dotenv
from app.models.payments import Payment, PaymentType, PaymentStatus, TariffPlan
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Price IDs із .env
STRIPE_PRICE_BASE = os.getenv("STRIPE_PRICE_BASE")
STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM")
STRIPE_PRICE_VIP = os.getenv("STRIPE_PRICE_VIP")
STRIPE_PRICE_TOKENS = os.getenv("STRIPE_PRICE_TOKENS")

STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL")
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL")


async def create_checkout_session(user_id: int, product_type: str, session: AsyncSession) -> str:
    """
    Створити Stripe Checkout Session:
    - product_type = 'tokens', 'base', 'premium', 'vip'
    """

    price_id = None
    mode = "payment"
    payment_type = None
    tariff = None
    token_amount = None

    if product_type == "tokens":
        price_id = STRIPE_PRICE_TOKENS
        payment_type = "token_purchase"  # Используем строку вместо Enum
        amount = 10.0
        token_amount = 100  # За 10 EUR пользователь получает 100 токенов
    elif product_type == "base":
        price_id = STRIPE_PRICE_BASE
        payment_type = "stripe"
        tariff = "base"
        mode = "subscription"
        amount = 5.0  # Базовая подписка 5 EUR
    elif product_type == "premium":
        price_id = STRIPE_PRICE_PREMIUM
        payment_type = "stripe"
        tariff = "premium"
        mode = "subscription"
        amount = 15.0
    elif product_type == "vip":
        price_id = STRIPE_PRICE_VIP
        payment_type = "stripe"
        tariff = "vip"
        mode = "subscription"
        amount = 30.0
    else:
        raise ValueError("❌ Невідомий тип продукту")

    checkout = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": 1,
        }],
        mode=mode,
        success_url=f"{STRIPE_SUCCESS_URL}?success=true",
        cancel_url=f"{STRIPE_CANCEL_URL}?canceled=true",
        metadata={
            "user_id": str(user_id),
            "product_type": product_type
        }
    )

    payment = Payment(
        user_id=user_id,
        type=payment_type,
        amount=amount,
        currency="eur",
        token_amount=token_amount,
        status="pending",
        tariff=tariff,
        stripe_session_id=checkout.id
    )
    session.add(payment)
    await session.commit()

    return checkout.url


async def confirm_payment(session_id: str, session: AsyncSession) -> bool:
    """
    Підтвердження платежу через Stripe Session ID
    """
    stripe_session = stripe.checkout.Session.retrieve(session_id)
    user_id = int(stripe_session.metadata["user_id"])

    stmt = select(Payment).where(Payment.stripe_session_id == session_id)
    payment = await session.scalar(stmt)

    if not payment:
        # Если платёж не найден по session_id, ищем по user_id и статусу
        stmt = select(Payment).where(Payment.user_id == user_id, Payment.status == "pending")
        payment = await session.scalar(stmt)
    
    if payment:
        payment.status = "confirmed"
        
        # Если это покупка токенов, начисляем их пользователю
        if payment.type == "token_purchase" and payment.token_amount:
            user = await session.scalar(select(User).where(User.id == user_id))
            if user:
                user.token_balance += payment.token_amount
                
        # Если это покупка подписки, устанавливаем premium статус
        if payment.type == "stripe" and payment.tariff in ["premium", "vip"]:
            user = await session.scalar(select(User).where(User.id == user_id))
            if user:
                user.is_premium = True
        
        await session.commit()
        return True
    
    return False
    return False
