# файл: app/services/assistant.py

import os
import openai
from dotenv import load_dotenv
from app.database import get_session
from app.models.messages import Message
from app.models.user import User
from app.models.matches import Match

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ANALYSIS_ID = os.getenv("OPENAI_ASSISTANT_ID_ANALYSIS")

async def analyze_message(text: str, sender_id: int, thread_id: str):
    prompt = f"""
    Аналізуй повідомлення в контексті чату знайомств. Оцініть ризики:
    - Чи є це повідомлення шахрайським?
    - Чи є агресія?
    - Чи виглядає як бот?
    Текст повідомлення:
    "{text}"
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ти аналітик безпеки. Визначай ризики в людських повідомленнях."},
                {"role": "user", "content": prompt}
            ]
        )

        result = response.choices[0].message.content
        print(f"🔍 AI-анализ: {result}")

        # (Опційно) зберігати результат в лог
        async for session in get_session():
            msg = Message(
                thread_id=thread_id,
                sender_id=sender_id,
                message_text=text + f"\n\n[AI аналіз]: {result}"
            )
            session.add(msg)
            await session.commit()

        return result

    except Exception as e:
        print(f"❌ Помилка аналізу AI: {e}")
        return None

