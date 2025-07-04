import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from app.config import TELEGRAM_BOT_TOKEN
from app.database import get_session
from app.booking.services_admin_message import AdminMessageService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

async def test_get_admin_message():
    """Test retrieving admin messages from database"""
    logger.info("Testing admin message retrieval...")
    
    test_cities = ["Frankfurt", "Kyiv", "Berlin", "Paris"]
    test_types = ["restaurant", "cafe", "park", "museum", "theater"]
    
    async for session in get_session():
        logger.info("Database session opened")
        
        # Test all combinations
        for city in test_cities:
            for place_type in test_types:
                logger.info(f"Testing city={city}, place_type={place_type}")
                
                # Try flexible method
                message = await AdminMessageService.get_admin_message_flexible(session, city, place_type)
                logger.info(f"Flexible method result: city={city}, type={place_type}, message={message}")

async def test_send_message():
    """Test sending a message with admin message content"""
    logger.info("Testing message sending...")
    
    # Replace with your test chat ID (your Telegram user ID)
    TEST_CHAT_ID = 123456789  # Replace with your actual Telegram user ID
    
    async for session in get_session():
        # Get a sample admin message
        message = await AdminMessageService.get_admin_message_flexible(session, "Frankfurt", "restaurant")
        
        if not message:
            logger.error("No admin message found for testing!")
            return
            
        try:
            # Create message content
            message_content = f"ℹ️ {message}\n\n"
            message_content += "🏙️ Here are restaurants in Frankfurt:"
            
            # Send a test message
            logger.info(f"Sending test message: {message_content}")
            sent_msg = await bot.send_message(TEST_CHAT_ID, message_content)
            logger.info(f"Message sent successfully. Message ID: {sent_msg.message_id}")
            
        except Exception as e:
            logger.error(f"Error sending test message: {e}")

async def main():
    logger.info("Starting test script...")
    
    # Test retrieving messages
    await test_get_admin_message()
    
    # Test sending messages
    # await test_send_message()  # Uncomment and set your Telegram ID to test sending
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main())
