# файл: app/webhook/stripe_webhook.py

import os
import stripe
from fastapi import APIRouter, Request, Header, HTTPException
from sqlalchemy import select
from app.database import get_session
from app.models.payments import Payment, PaymentStatus
from app.models.user import User
from app.config import STRIPE_WEBHOOK_SECRET

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None)
):
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid payload or signature")

    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        metadata = session_data.get("metadata", {})
        user_id = metadata.get("user_id")

        if not user_id:
            raise HTTPException(status_code=400, detail="No user_id in metadata")

        async for session in get_session():
            user = await session.scalar(select(User).where(User.id == int(user_id)))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            payment = await session.scalar(
                select(Payment)
                .where(Payment.user_id == user.id)
                .where(Payment.status == PaymentStatus.pending)
                .order_by(Payment.timestamp.desc())
            )
            if payment:
                payment.status = PaymentStatus.confirmed
                if payment.type.name == "token_purchase":
                    user.token_balance += int(payment.amount)
                elif payment.type.name == "stripe":
                    user.is_premium = True
                await session.commit()

    return {"status": "success"}
