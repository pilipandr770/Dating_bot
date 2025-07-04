# app/booking/final_test.py

import asyncio
import logging
import sys
import os
from sqlalchemy import text

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("FINAL_TEST")

async def final_verification():
    """Final verification of the system"""
    try:
        # Initialize the database and required modules
        from app.database import get_session, init_db
        from app.booking.services_admin_message import AdminMessageService
        
        # Verify all 3 admin messages are in the database
        async for session in get_session():
            # First, initialize the database
            await init_db()
            
            # Count admin messages
            count_query = text("SELECT COUNT(*) FROM dating_bot.admin_messages")
            count_result = await session.execute(count_query)
            admin_msg_count = count_result.scalar()
            
            logger.info(f"Found {admin_msg_count} admin messages in the database")
            
            # If we have less than 3 messages, create missing ones
            if admin_msg_count < 3:
                logger.info("Adding missing admin messages...")
                
                # Check existing message types to avoid duplicates
                existing_query = text("SELECT DISTINCT place_type FROM dating_bot.admin_messages")
                existing_result = await session.execute(existing_query)
                existing_types = [row[0] for row in existing_result.fetchall()]
                
                # Add restaurant message if missing
                if "restaurant" not in existing_types:
                    await AdminMessageService.add_admin_message(
                        session=session,
                        city="Франкфурт",
                        place_type="restaurant",
                        message="Тестовое сообщение для ресторанов в Франкфурте. Скидка 15% с промокодом TEST."
                    )
                    logger.info("Added admin message for restaurant type")
                
                # Add cafe message if missing
                if "cafe" not in existing_types:
                    await AdminMessageService.add_admin_message(
                        session=session,
                        city="Франкфурт",
                        place_type="cafe",
                        message="Тестовое сообщение для кафе во Франкфурте. Скидка 10% по промокоду CAFE10."
                    )
                    logger.info("Added admin message for cafe type")
                
                # Add park message if missing
                if "park" not in existing_types:
                    await AdminMessageService.add_admin_message(
                        session=session,
                        city="Франкфурт",
                        place_type="park",
                        message="Тестове повідомлення для парків у Франкфурті. Спеціальні події щовихідних!"
                    )
                    logger.info("Added admin message for park type")
                    
            # Verify admin_message_flexible works for all types
            test_types = ["restaurant", "cafe", "park"]
            for place_type in test_types:
                admin_message = await AdminMessageService.get_admin_message_flexible(
                    session, city="Франкфурт", place_type=place_type
                )
                
                if admin_message:
                    logger.info(f"✅ Successfully retrieved admin message for {place_type}: {admin_message[:30]}...")
                else:
                    logger.error(f"❌ Failed to retrieve admin message for {place_type}")
    
        logger.info("✅ Final verification completed!")
        logger.info("""
        🚀 NEXT STEPS:
        1. Run the bot with 'python -m app.main' or 'python app/main.py'
        2. In Telegram, use the booking menu and select a place type
        3. Confirm that:
           - The admin message appears below the venue list
           - The logs show "[NEW]" prefixed messages (indicating new_handlers.py is used)
           - No errors appear in the logs
        """)
                    
    except Exception as e:
        logger.error(f"Error during final verification: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(final_verification())
