# app/booking/verify_setup.py

import asyncio
import logging
import traceback
import sys
import os
from sqlalchemy import text

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("VERIFY_SETUP")

# Try to import necessary modules to verify they're working
try:
    # Import core modules
    from app.database import get_session, init_db
    logger.info("✅ Core database modules imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import core modules: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

async def verify_imports():
    """Check that all necessary modules can be imported"""
    try:
        # Import booking handlers and services
        from app.booking.new_handlers import register_booking_handlers, process_place_type
        logger.info("✅ Successfully imported register_booking_handlers from new_handlers.py")
        
        # Check if handlers_fixed.py is also loaded
        try:
            from app.booking.handlers_fixed import register_booking_handlers as old_register_handlers
            logger.warning("⚠️ handlers_fixed.py is still loadable (this is OK if it's just for reference)")
        except ImportError:
            logger.info("✅ handlers_fixed.py is not loaded (as expected)")
        
        # Check if handlers.py.bak exists but is not loaded
        if os.path.exists(os.path.join(os.path.dirname(__file__), "handlers.py.bak")):
            logger.info("✅ handlers.py.bak exists (renamed file)")
        
        # Check if handlers.py still exists (should be renamed to .bak)
        if os.path.exists(os.path.join(os.path.dirname(__file__), "handlers.py")):
            logger.warning("⚠️ handlers.py still exists! This could cause conflicts")
        else:
            logger.info("✅ handlers.py does not exist (as expected)")
        
        # Import admin message service
        from app.booking.services_admin_message import AdminMessageService
        logger.info("✅ Successfully imported AdminMessageService")
        
        # Import venue service
        from app.booking.services_db import VenueService
        logger.info("✅ Successfully imported VenueService")
        
    except Exception as e:
        logger.error(f"❌ Import verification failed: {e}")
        logger.error(traceback.format_exc())
        return False
    
    return True

async def verify_database():
    """Check that the database is accessible and contains expected tables/data"""
    try:
        # Initialize the database
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Check if required tables exist
        async for session in get_session():
            # Check places table
            places_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'dating_bot' AND table_name = 'places'
                );
            """)
            places_result = await session.execute(places_query)
            places_exists = places_result.scalar()
            
            if places_exists:
                logger.info("✅ Table 'places' exists in the database")
                
                # Count places
                count_query = text("SELECT COUNT(*) FROM dating_bot.places")
                count_result = await session.execute(count_query)
                places_count = count_result.scalar()
                logger.info(f"ℹ️ Number of places in the database: {places_count}")
                
                # List sample places
                if places_count > 0:
                    sample_query = text("SELECT id, name, city, type FROM dating_bot.places LIMIT 5")
                    sample_result = await session.execute(sample_query)
                    sample_places = sample_result.fetchall()
                    logger.info(f"ℹ️ Sample places:")
                    for place in sample_places:
                        logger.info(f"  - ID: {place.id}, Name: {place.name}, City: {place.city}, Type: {place.type}")
            else:
                logger.error("❌ Table 'places' does NOT exist in the database!")
            
            # Check admin_messages table
            admin_msg_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'dating_bot' AND table_name = 'admin_messages'
                );
            """)
            admin_msg_result = await session.execute(admin_msg_query)
            admin_msg_exists = admin_msg_result.scalar()
            
            if admin_msg_exists:
                logger.info("✅ Table 'admin_messages' exists in the database")
                
                # Count admin messages
                count_query = text("SELECT COUNT(*) FROM dating_bot.admin_messages")
                count_result = await session.execute(count_query)
                admin_msg_count = count_result.scalar()
                logger.info(f"ℹ️ Number of admin messages in the database: {admin_msg_count}")
                
                # List all admin messages
                if admin_msg_count > 0:
                    admin_msg_query = text("SELECT id, city, place_type, message FROM dating_bot.admin_messages")
                    admin_msg_result = await session.execute(admin_msg_query)
                    admin_messages = admin_msg_result.fetchall()
                    logger.info(f"ℹ️ All admin messages:")
                    for msg in admin_messages:
                        logger.info(f"  - ID: {msg.id}, City: {msg.city}, Type: {msg.place_type}")
                        logger.info(f"    Message: {msg.message[:50]}{'...' if len(msg.message) > 50 else ''}")
                
                # Test retrieving a specific message
                if admin_msg_count > 0:
                    from app.booking.services_admin_message import AdminMessageService
                    first_msg = admin_messages[0]
                    
                    # Test exact match
                    message = await AdminMessageService.get_admin_message(
                        session, city=first_msg.city, place_type=first_msg.place_type
                    )
                    if message:
                        logger.info(f"✅ Successfully retrieved admin message with exact match")
                    else:
                        logger.warning(f"⚠️ Failed to retrieve admin message with exact match")
                    
                    # Test case-insensitive match
                    if first_msg.city:
                        message = await AdminMessageService.get_admin_message(
                            session, city=first_msg.city.upper(), place_type=first_msg.place_type
                        )
                        if message:
                            logger.info(f"✅ Successfully retrieved admin message with case-insensitive match")
                        else:
                            logger.warning(f"⚠️ Failed to retrieve admin message with case-insensitive match")
            else:
                logger.error("❌ Table 'admin_messages' does NOT exist in the database!")
    
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        logger.error(traceback.format_exc())
        return False
    
    return True

async def simulate_callback_handler():
    """Simulate the callback handler to see if it would process correctly"""
    try:
        from app.booking.new_handlers import process_place_type
        from aiogram.types import CallbackQuery, User, Message, Chat
        from aiogram.dispatcher import FSMContext
        
        # This is just a skeleton to check if imports work - not actual simulation
        logger.info("✅ process_place_type handler can be imported successfully")
        logger.info("ℹ️ To fully test the handler, run the bot and test with the actual Telegram interface")
        
        # Print out the callback pattern that would trigger this handler
        logger.info("ℹ️ This handler processes callbacks matching: 'booking:type:*'")
        logger.info("ℹ️ Example: 'booking:type:restaurant', 'booking:type:cafe', etc.")
        
    except Exception as e:
        logger.error(f"❌ Handler simulation failed: {e}")
        logger.error(traceback.format_exc())
        return False
    
    return True

async def main():
    """Run all verifications"""
    logger.info("🔍 Starting verification of the bot setup...")
    
    import_success = await verify_imports()
    db_success = await verify_database()
    handler_success = await simulate_callback_handler()
    
    if import_success and db_success and handler_success:
        logger.info("✅ All verification checks passed!")
        logger.info("""
        🚀 NEXT STEPS:
        1. Run the bot with 'python -m app.main' or 'python app/main.py'
        2. In Telegram, use the booking menu and select a place type
        3. Check the logs for [NEW] prefixed messages to confirm new_handlers.py is being used
        4. Verify that admin messages are displayed in the Telegram UI
        """)
    else:
        logger.error("❌ Some verification checks failed!")
        
        if not import_success:
            logger.error("""
            📌 IMPORT ISSUES:
            - Make sure handlers.py is renamed to handlers.py.bak
            - Verify that new_handlers.py exists and has the correct register_booking_handlers function
            - Check that __init__.py imports from new_handlers.py
            """)
        
        if not db_success:
            logger.error("""
            📌 DATABASE ISSUES:
            - Verify that the database is running and accessible
            - Check that the tables 'places' and 'admin_messages' exist
            - Ensure there are admin messages in the database
            """)
        
        if not handler_success:
            logger.error("""
            📌 HANDLER ISSUES:
            - Check that the process_place_type function in new_handlers.py is correctly defined
            - Verify that the handler is registered with the correct callback pattern
            """)

if __name__ == "__main__":
    asyncio.run(main())
