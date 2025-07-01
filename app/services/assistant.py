# файл: app/services/assistant.py

import os
from dotenv import load_dotenv
from app.database import get_session
from app.models.messages import Message
from app.models.user import User
from app.models.match import Match
from sqlalchemy import select

load_dotenv()

# Initialize the OpenAI client with proper error handling
client = None
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if client.api_key is None or client.api_key == "":
        print("⚠️ OpenAI API key is not set in environment variables, AI analysis will be disabled")
        client = None
    else:
        print("✅ OpenAI client initialized successfully")
except ImportError:
    print("⚠️ OpenAI package not installed or incompatible, AI analysis will be disabled")
except Exception as e:
    print(f"⚠️ Error initializing OpenAI client: {e}, AI analysis will be disabled")

ASSISTANT_ANALYSIS_ID = os.getenv("OPENAI_ASSISTANT_ID_ANALYSIS")

async def analyze_chat(thread_id: str, user_id: int = None):
    """
    Analyze the entire chat thread when explicitly requested.
    Returns advice based on the chat history.
    """
    # Skip analysis if OpenAI client is not initialized
    if client is None:
        return "⚠️ AI аналіз недоступний (API ключ не налаштовано)"
    
    # Retrieve the chat history from the database
    chat_history = []
    user_info = {}
    
    async for session in get_session():
        # Get messages from this thread
        messages = await session.scalars(
            select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
        )
        messages = messages.all()
        
        if not messages:
            return "Історія повідомлень порожня. Немає що аналізувати."
        
        # Get user information for context
        match = await session.scalar(select(Match).where(Match.thread_id == thread_id))
        if match:
            user1 = await session.scalar(select(User).where(User.id == match.user_1_id))
            user2 = await session.scalar(select(User).where(User.id == match.user_2_id))
            if user1:
                user_info[user1.id] = {"name": user1.first_name, "gender": user1.gender, "age": user1.age}
            if user2:
                user_info[user2.id] = {"name": user2.first_name, "gender": user2.gender, "age": user2.age}
        
        # Format the chat history
        for msg in messages:
            sender = user_info.get(msg.sender_id, {"name": "Користувач"})
            chat_history.append(f"{sender['name']}: {msg.message_text}")
    
    # Create the prompt with the chat history
    chat_text = "\n".join(chat_history[-20:])  # Get the last 20 messages to avoid token limits
    
    prompt = f"""
    Проаналізуй наступну розмову між двома людьми у чаті знайомств та надай дружню пораду:
    
    {chat_text}
    
    Будь ласка, дай такі поради:
    1. Як можна покращити спілкування?
    2. Які спільні інтереси ти помічаєш?
    3. Чи є якісь ознаки несумісності або обережності?
    4. Запропонуй 2-3 теми для продовження розмови.
    
    Відповідь має бути дружньою, ввічливою та корисною для обох учасників.
    """
    
    try:
        # Using the new OpenAI API format (v1.0.0+)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти дружній помічник для побачень і знайомств. Ти аналізуєш розмови та надаєш корисні поради для покращення спілкування."},
                {"role": "user", "content": prompt}
            ]
        )
        
        result = response.choices[0].message.content
        print(f"🔍 AI-аналіз чату: {result}")
        
        # Log the analysis
        try:
            # Use the user_id as the sender instead of 0 to avoid foreign key issues
            if user_id:
                async for session in get_session():
                    # Save as a message from the user who requested it (but mark it as AI)
                    msg = Message(
                        thread_id=thread_id,
                        sender_id=user_id,  # Use the user who requested the analysis
                        message_text=f"🤖 AI АНАЛІЗ:\n\n{result}"
                    )
                    session.add(msg)
                    await session.commit()
        except Exception as log_err:
            print(f"❌ Помилка логування AI аналізу: {log_err}")
            # Don't fail the whole function just because logging failed

        return f"🤖 AI АНАЛІЗ:\n\n{result}"

    except Exception as e:
        print(f"❌ Помилка аналізу AI: {e}")
        return f"❌ Помилка аналізу чату: {str(e)}"


async def analyze_message(text: str, sender_id: int, thread_id: str):
    """
    Legacy function kept for backward compatibility.
    Now simply returns None to avoid automatic analysis of each message.
    """
    return None

