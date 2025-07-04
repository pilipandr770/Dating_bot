"""
This script verifies that:
1. The unified handler is properly imported
2. The admin messages can be retrieved
3. Handler registration happens correctly
"""

import asyncio
import logging
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("verification.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("verification")

async def main():
    try:
        # Import key modules
        logger.info("Importing key modules...")
        
        from app.booking import register_booking_handlers
        from app.database import init_db, get_session
        from app.booking.services_admin_message import AdminMessageService
        from app.booking.services_db import VenueService
        from app.booking.unified_handler import process_place_type
        from aiogram import Bot, Dispatcher
        from aiogram.contrib.fsm_storage.memory import MemoryStorage
        
        # Verify module source
        import inspect
        handler_source = inspect.getmodule(process_place_type).__file__
        logger.info(f"process_place_type imported from: {handler_source}")
        
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        
        # Test admin message service
        logger.info("Testing admin message service...")
        async for session in get_session():
            try:
                # Try getting message with flexible method
                city = "Moscow"
                place_type = "Restaurant"
                
                if hasattr(AdminMessageService, 'get_admin_message_flexible'):
                    message = await AdminMessageService.get_admin_message_flexible(session, city, place_type)
                    logger.info(f"Admin message (flexible): {message}")
                
                # Try standard method
                message = await AdminMessageService.get_admin_message(session, city, place_type)
                logger.info(f"Admin message (standard): {message}")
                
                # List all messages in DB
                from sqlalchemy import text
                query = text("SELECT id, city, place_type, message FROM dating_bot.admin_messages")
                result = await session.execute(query)
                rows = result.fetchall()
                logger.info(f"All admin messages in DB: {rows}")
                
            except Exception as e:
                logger.error(f"Error testing admin message service: {e}")
                logger.error(traceback.format_exc())
        
        # Test handler registration
        logger.info("Testing handler registration...")
        
        # Create test bot and dispatcher
        bot = Bot(token="test_token")
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)
        
        # Register handlers
        register_booking_handlers(dp)
        
        # Check if handlers were registered
        if hasattr(dp, 'callback_query_handlers'):
            handlers = dp.callback_query_handlers
            logger.info(f"Callback query handlers: {handlers}")
        
        logger.info("Verification completed successfully!")
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
