import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from app.database import get_session
from app.booking.services_admin_message import AdminMessageService
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("admin_message_debug.log"), logging.StreamHandler()]
)
logger = logging.getLogger("admin_message_debug")

# Default test data for comparison
TEST_CITY = "Kyiv"
TEST_PLACE_TYPE = "restaurant"

async def test_db_connection():
    """Test database connection"""
    logger.info("Testing database connection...")
    try:
        async for session in get_session():
            result = await session.execute(text("SELECT 1"))
            logger.info(f"Database connection successful: {result.scalar()}")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def list_all_admin_messages():
    """List all admin messages in the database"""
    logger.info("Listing all admin messages...")
    try:
        async for session in get_session():
            # First check if the table exists
            check_table = await session.execute(
                text("SELECT EXISTS(SELECT FROM information_schema.tables "
                     "WHERE table_schema = 'dating_bot' AND table_name = 'admin_messages')")
            )
            if not check_table.scalar():
                logger.error("admin_messages table does not exist!")
                return []
            
            # List all admin messages
            query = text("SELECT id, city, place_type, message FROM dating_bot.admin_messages")
            result = await session.execute(query)
            messages = result.fetchall()
            
            logger.info(f"Found {len(messages)} admin messages in database")
            for msg in messages:
                logger.info(f"ID: {msg[0]}, City: {msg[1]}, Place Type: {msg[2]}, Message: {msg[3][:30]}...")
            
            return messages
    except Exception as e:
        logger.error(f"Error listing admin messages: {e}")
        return []

async def test_get_admin_message(city, place_type):
    """Test getting admin message using service method"""
    logger.info(f"Testing get_admin_message with city='{city}', place_type='{place_type}'")
    try:
        async for session in get_session():
            # Try the regular service method
            message = await AdminMessageService.get_admin_message(session, city, place_type)
            logger.info(f"Regular method result: {message}")
            
            # Try flexible version if it exists
            if hasattr(AdminMessageService, 'get_admin_message_flexible'):
                flexible_message = await AdminMessageService.get_admin_message_flexible(session, city, place_type)
                logger.info(f"Flexible method result: {flexible_message}")
            
            # Try direct SQL with different variations
            # Case 1: Exact match
            query1 = text("SELECT message FROM dating_bot.admin_messages WHERE LOWER(city) = LOWER(:city) AND LOWER(place_type) = LOWER(:place_type)")
            result1 = await session.execute(query1.bindparams(city=city, place_type=place_type))
            message1 = result1.scalar()
            logger.info(f"Direct SQL (exact match): {message1}")
            
            # Case 2: City contains match
            query2 = text("SELECT message FROM dating_bot.admin_messages WHERE LOWER(city) LIKE LOWER(:city) AND LOWER(place_type) = LOWER(:place_type)")
            result2 = await session.execute(query2.bindparams(city=f"%{city}%", place_type=place_type))
            message2 = result2.scalar()
            logger.info(f"Direct SQL (city contains): {message2}")
            
            # Case 3: Place type only
            query3 = text("SELECT message FROM dating_bot.admin_messages WHERE LOWER(place_type) = LOWER(:place_type) LIMIT 1")
            result3 = await session.execute(query3.bindparams(place_type=place_type))
            message3 = result3.scalar()
            logger.info(f"Direct SQL (place type only): {message3}")
            
            # Case 4: Any message (fallback)
            query4 = text("SELECT message FROM dating_bot.admin_messages LIMIT 1")
            result4 = await session.execute(query4)
            message4 = result4.scalar()
            logger.info(f"Direct SQL (any message): {message4}")
            
            return {
                "service_method": message,
                "direct_exact": message1,
                "direct_contains": message2,
                "direct_type_only": message3,
                "direct_any": message4
            }
    except Exception as e:
        logger.error(f"Error testing get_admin_message: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

async def check_process_place_type_implementation():
    """Check the implementation of process_place_type in all handler files"""
    logger.info("Checking process_place_type implementation in handler files...")
    
    # Path to the different handler files
    handler_files = [
        "app/booking/handlers_fixed.py",
        "app/booking/handlers.py",
        "app/booking/new_handlers.py"
    ]
    
    import os
    import re
    
    for file_path in handler_files:
        if not os.path.exists(file_path):
            logger.info(f"File {file_path} does not exist")
            continue
            
        logger.info(f"Checking {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Check if process_place_type exists
            if "async def process_place_type" in content:
                logger.info(f"process_place_type found in {file_path}")
                
                # Check admin message related code
                if "admin_message" in content and "AdminMessageService" in content:
                    logger.info(f"Admin message logic found in {file_path}")
                    
                    # Extract the admin message part
                    pattern = r"(# Пробуем получить сообщение администратора.*?admin_message.*?logger\.info.*?)\n\s*#"
                    matches = re.findall(pattern, content, re.DOTALL)
                    if matches:
                        logger.info(f"Admin message retrieval code in {file_path}:")
                        for match in matches:
                            logger.info(f"Code snippet: {match[:200]}...")
                    else:
                        logger.info(f"No specific admin message retrieval code found in {file_path}")
                else:
                    logger.info(f"No admin message logic found in {file_path}")
            else:
                logger.info(f"process_place_type NOT found in {file_path}")

async def check_imports():
    """Check which handler file is being imported in __init__.py"""
    logger.info("Checking imports in __init__.py...")
    
    import os
    if os.path.exists("app/booking/__init__.py"):
        with open("app/booking/__init__.py", 'r', encoding='utf-8') as file:
            content = file.read()
            logger.info(f"Content of __init__.py:\n{content}")
            
            # Check which handlers file is imported
            if "from app.booking.handlers_fixed import" in content:
                logger.info("handlers_fixed.py is being imported")
            if "from app.booking.handlers import" in content:
                logger.info("handlers.py is being imported")
            if "from app.booking.new_handlers import" in content:
                logger.info("new_handlers.py is being imported")
    else:
        logger.info("__init__.py file not found")

async def inject_admin_message_directly():
    """Inject admin message directly into the database"""
    logger.info("Injecting test admin message directly into database...")
    try:
        async for session in get_session():
            # Check if message already exists
            check_query = text(
                "SELECT COUNT(*) FROM dating_bot.admin_messages "
                "WHERE LOWER(city) = LOWER(:city) AND LOWER(place_type) = LOWER(:place_type)"
            )
            count = await session.execute(check_query.bindparams(city=TEST_CITY, place_type=TEST_PLACE_TYPE))
            
            if count.scalar() > 0:
                logger.info(f"Admin message for {TEST_CITY}/{TEST_PLACE_TYPE} already exists")
            else:
                # Insert new message
                insert_query = text(
                    "INSERT INTO dating_bot.admin_messages(city, place_type, message) "
                    "VALUES(:city, :place_type, :message)"
                )
                await session.execute(insert_query.bindparams(
                    city=TEST_CITY,
                    place_type=TEST_PLACE_TYPE,
                    message="DEBUG TEST ADMIN MESSAGE - PLEASE DISPLAY ME!"
                ))
                await session.commit()
                logger.info(f"Test admin message inserted for {TEST_CITY}/{TEST_PLACE_TYPE}")
            
            return True
    except Exception as e:
        logger.error(f"Error injecting test admin message: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    logger.info("Starting admin message debug")
    
    # Test database connection
    if not await test_db_connection():
        logger.error("Database connection failed, aborting further tests")
        return
    
    # Check imports
    await check_imports()
    
    # Check implementation
    await check_process_place_type_implementation()
    
    # List all admin messages
    messages = await list_all_admin_messages()
    
    if not messages:
        logger.warning("No admin messages found in database, injecting test message")
        await inject_admin_message_directly()
        # List again after injection
        messages = await list_all_admin_messages()
    
    # Test getting admin message
    if messages:
        # Test with existing data
        sample_city = messages[0][1]
        sample_type = messages[0][2]
        logger.info(f"Testing with existing data: city='{sample_city}', type='{sample_type}'")
        await test_get_admin_message(sample_city, sample_type)
    
    # Test with standard test data
    logger.info(f"Testing with standard test data: city='{TEST_CITY}', type='{TEST_PLACE_TYPE}'")
    await test_get_admin_message(TEST_CITY, TEST_PLACE_TYPE)
    
    logger.info("Admin message debug completed")

if __name__ == "__main__":
    asyncio.run(main())
