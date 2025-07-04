import asyncio
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy import text
from app.database import get_session
from app.booking.services_admin_message import AdminMessageService

async def simulate_place_type_button_click():
    """
    Simulate what happens when a user clicks a place type button
    """
    print("\n===== SIMULATING PLACE TYPE BUTTON CLICK =====")
    
    # Parameters we'd have from the callback query
    city = "Франкфурт"
    place_type = "restaurant"  # or "park", etc.
    
    print(f"City: {city}")
    print(f"Place type: {place_type}")
    
    async for session in get_session():
        # This part simulates what happens in process_place_type handler
        print("\nRetrieving admin message for the selected city and place type...")
        
        # Verify both parameters are strings and properly sanitized
        logger.info(f"Parameter types: city={type(city).__name__}, place_type={type(place_type).__name__}")
        if not isinstance(city, str) or not isinstance(place_type, str):
            logger.warning("Parameters should be strings!")
            city = str(city) if city else ""
            place_type = str(place_type) if place_type else ""
        
        # First approach - using AdminMessageService
        admin_message = await AdminMessageService.get_admin_message(session, city, place_type)
        
        if admin_message:
            print(f"Found admin message via AdminMessageService: {admin_message[:50]}...")
        else:
            print("No admin message found via AdminMessageService")
            
            # Try direct SQL as a fallback (same as in handlers_fixed.py)
            direct_query = text("""
                SELECT message FROM dating_bot.admin_messages 
                WHERE LOWER(city) LIKE LOWER(:city_pattern) 
                AND LOWER(place_type) = LOWER(:place_type) 
                LIMIT 1
            """).bindparams(city_pattern=f"%{city}%", place_type=place_type)
            
            try:
                direct_result = await session.execute(direct_query)
                direct_row = direct_result.fetchone()
                if direct_row:
                    admin_message = direct_row[0]
                    print(f"Found admin message via direct SQL: {admin_message[:50]}...")
                else:
                    print("No admin message found via direct SQL either")
            except Exception as direct_query_error:
                print(f"Error in direct SQL query: {direct_query_error}")
        
        # Show how the message would be formatted
        if admin_message:
            message_text = f"✅ Вы выбрали: *{place_type}*\n\nДоступные заведения этого типа:"
            message_text += f"\n\nℹ️ {admin_message}"
            print("\nFinal message that would be shown to user:")
            print("-" * 50)
            print(message_text)
            print("-" * 50)
        else:
            print("\nNo admin message would be shown to user")
    
        # Try the other place type as well
        other_place_type = "park" if place_type == "restaurant" else "restaurant"
        print(f"\nTrying with place_type={other_place_type} for comparison...")
        
        other_admin_message = await AdminMessageService.get_admin_message(session, city, other_place_type)
        if other_admin_message:
            print(f"Found admin message for {other_place_type}: {other_admin_message[:50]}...")
        else:
            print(f"No admin message found for {other_place_type}")

asyncio.run(simulate_place_type_button_click())
