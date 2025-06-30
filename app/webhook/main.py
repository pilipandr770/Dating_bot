# файл: app/webhook/main.py

from fastapi import FastAPI
from app.webhook.stripe_webhook import router as stripe_router

app = FastAPI()

# Інтегруємо Stripe Webhook
app.include_router(stripe_router)

# Якщо хочеш додаткові маршрути (наприклад, healthcheck або admin)
@app.get("/")
async def root():
    return {"status": "ok"}
