# app/booking/test_admin_message.py

import asyncio
import logging
import traceback
import sys
from sqlalchemy import text

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("TEST_ADMIN_MESSAGE")

async def test_admin_message_retrieval():
    """Test retrieving admin messages in isolation"""
    try:
        # Import required modules
        from app.database import get_session, init_db
        from app.booking.services_admin_message import AdminMessageService
        
        logger.info("🔍 Starting admin message test...")
        
        # Initialize the database
        await init_db()
        
        # Get a list of cities and place types from the database
        cities = []
        place_types = []
        
        async for session in get_session():
            # Get cities from places table
            cities_query = text("SELECT DISTINCT city FROM dating_bot.places WHERE city IS NOT NULL")
            cities_result = await session.execute(cities_query)
            cities = [row[0] for row in cities_result.fetchall()]
            
            # Get place types from places table
            types_query = text("SELECT DISTINCT type FROM dating_bot.places WHERE type IS NOT NULL")
            types_result = await session.execute(types_query)
            place_types = [row[0] for row in types_result.fetchall()]
            
            # Add some common place types if none found
            if not place_types:
                place_types = ["restaurant", "cafe", "bar", "cinema", "event", "park", "other"]
            
            logger.info(f"Found cities: {cities}")
            logger.info(f"Found place types: {place_types}")
            
            # List all admin messages
            admin_messages_query = text("SELECT id, city, place_type, message FROM dating_bot.admin_messages")
            admin_messages_result = await session.execute(admin_messages_query)
            admin_messages = admin_messages_result.fetchall()
            
            logger.info(f"Found {len(admin_messages)} admin messages in the database:")
            for msg in admin_messages:
                logger.info(f"ID: {msg.id}, City: {msg.city}, Type: {msg.place_type}")
                logger.info(f"Message: {msg.message[:50]}{'...' if len(msg.message) > 50 else ''}")
            
            # Test each city and place type combination
            for city in cities:
                for place_type in place_types:
                    logger.info(f"Testing retrieval for city='{city}', type='{place_type}':")
                    
                    # Test direct database query
                    direct_query = text("""
                        SELECT message FROM dating_bot.admin_messages 
                        WHERE LOWER(city) LIKE LOWER(:city_pattern) 
                        AND LOWER(place_type) = LOWER(:place_type) 
                        LIMIT 1
                    """).bindparams(city_pattern=f"%{city}%", place_type=place_type)
                    
                    direct_result = await session.execute(direct_query)
                    direct_row = direct_result.fetchone()
                    
                    if direct_row:
                        logger.info(f"✅ Direct SQL: Message found: {direct_row[0][:30]}...")
                    else:
                        logger.info(f"⚠️ Direct SQL: No message found")
                    
                    # Test using the service
                    service_result = await AdminMessageService.get_admin_message(
                        session, city=city, place_type=place_type
                    )
                    
                    if service_result:
                        logger.info(f"✅ Service: Message found: {service_result[:30]}...")
                    else:
                        logger.info(f"⚠️ Service: No message found")
                    
                    # Test flexible service
                    flexible_result = await AdminMessageService.get_admin_message_flexible(
                        session, city=city, place_type=place_type
                    )
                    
                    if flexible_result:
                        logger.info(f"✅ Flexible: Message found: {flexible_result[:30]}...")
                    else:
                        logger.info(f"⚠️ Flexible: No message found")
                    
                    logger.info("---")
            
            # If no cities found, test with some default values
            if not cities:
                test_cities = ["Kyiv", "Kiev", "Київ", "Киев"]
                test_types = ["restaurant", "cafe", "bar"]
                
                logger.info("No cities found in database, testing with default values:")
                for city in test_cities:
                    for place_type in test_types:
                        logger.info(f"Testing with city='{city}', type='{place_type}'")
                        message = await AdminMessageService.get_admin_message(
                            session, city=city, place_type=place_type
                        )
                        
                        if message:
                            logger.info(f"✅ Message found: {message[:30]}...")
                        else:
                            logger.info(f"⚠️ No message found")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_admin_message_retrieval())
