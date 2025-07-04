# app/booking/message_fix.py

import asyncio
import logging
from sqlalchemy import text
from app.database import get_session
from app.booking.services_admin_message import AdminMessageService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MESSAGE_FIX")

async def test_message_display_formatting():
    """
    This function tests the exact code that would be used in the Telegram handler
    to display admin messages, to verify it works correctly.
    """
    try:
        logger.info("Starting message display test...")
        
        # Test data similar to what the handler receives
        city = "Франкфурт"
        place_types = ["restaurant", "cafe", "park"]
        
        # Initialize DB
        from app.database import init_db
        await init_db()
        
        # For each place type, test how the message would be displayed
        for place_type in place_types:
            logger.info(f"Testing message display for city='{city}', type='{place_type}':")
            
            # Get admin message - same code as in handler
            admin_message = None
            try:
                async for session in get_session():
                    # Use the flexible version to get better results with fallbacks
                    admin_message = await AdminMessageService.get_admin_message_flexible(
                        session, city=city, place_type=place_type
                    )
            except Exception as e:
                logger.error(f"Error getting admin message: {e}")
            
            # Generate example message text
            message_text = f"✅ You selected: *{place_type}*\n\nAvailable venues of this type:"
            
            # Add admin message if available - same code as in handler
            if admin_message and isinstance(admin_message, str) and admin_message.strip():
                logger.info(f"Adding admin message: {admin_message[:30]}...")
                message_text += f"\n\nℹ️ {admin_message}"
                logger.info(f"Final message with admin message: {message_text[:100]}...")
            else:
                logger.info(f"Admin message missing or invalid, type: {type(admin_message).__name__}")
                logger.info(f"Admin message value: {admin_message}")
                logger.info(f"Final message without admin message: {message_text}")
    
    except Exception as e:
        logger.error(f"Test failed: {e}")

async def create_missing_admin_message():
    """Create an admin message for cafe type if it doesn't exist"""
    try:
        async for session in get_session():
            # Check if we have a message for cafe type
            query = text("SELECT * FROM dating_bot.admin_messages WHERE place_type = 'cafe'")
            result = await session.execute(query)
            existing = result.fetchone()
            
            if not existing:
                logger.info("No admin message for cafe type, creating one...")
                # Add a test message
                from app.booking.services_admin_message import AdminMessageService
                await AdminMessageService.add_admin_message(
                    session=session,
                    city="Франкфурт",
                    place_type="cafe",
                    message="Тестовое сообщение для кафе во Франкфурте. Скидка 10% по промокоду CAFE10."
                )
                logger.info("Created new admin message for cafe type")
            else:
                logger.info(f"Admin message for cafe type already exists: {existing.message[:30]}...")
    except Exception as e:
        logger.error(f"Error creating admin message: {e}")

async def main():
    """Run the tests"""
    await create_missing_admin_message()
    await test_message_display_formatting()

if __name__ == "__main__":
    asyncio.run(main())
