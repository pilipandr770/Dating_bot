# файл: app/services/stripe.py

import stripe
import os
from dotenv import load_dotenv
from app.models.payments import Payment, PaymentType, PaymentStatus, TariffPlan
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

    if product_type == "tokens":
        price_id = STRIPE_PRICE_TOKENS
        payment_type = PaymentType.token_purchase
        amount = 10.0
    elif product_type == "base":
        price_id = STRIPE_PRICE_BASE
        payment_type = PaymentType.stripe
        tariff = TariffPlan.base
        mode = "subscription"
        amount = 0.0
    elif product_type == "premium":
        price_id = STRIPE_PRICE_PREMIUM
        payment_type = PaymentType.stripe
        tariff = TariffPlan.premium
        mode = "subscription"
        amount = 0.0
    elif product_type == "vip":
        price_id = STRIPE_PRICE_VIP
        payment_type = PaymentType.stripe
        tariff = TariffPlan.vip
        mode = "subscription"
        amount = 0.0
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
        tariff=tariff,
        status=PaymentStatus.pending,
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

    stmt = select(Payment).where(Payment.user_id == user_id, Payment.status == PaymentStatus.pending)
    payment = await session.scalar(stmt)

    if payment:
        payment.status = PaymentStatus.confirmed
        await session.commit()
        return True
    return False
