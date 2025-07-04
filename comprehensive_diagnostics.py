import sys
import os
import logging
import asyncio
import inspect
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

# Configure logging
log_dir = os.path.join(os.getcwd(), 'diagnostics_logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'diagnostics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('diagnostics')

# Import app modules after setting up logging
try:
    from app.config import TELEGRAM_BOT_TOKEN
    from app.database import get_session, init_db
    from app.booking import register_booking_handlers
    from app.bot import dp
    
    # Try to import different versions of the handlers
    try:
        from app.booking.patched_handler import process_place_type as patched_process_place_type
        logger.info("✅ Successfully imported patched_process_place_type from patched_handler.py")
    except ImportError:
        logger.warning("⚠️ Could not import process_place_type from patched_handler.py")
        patched_process_place_type = None
    
    try:
        from app.booking.new_handlers import process_place_type as new_process_place_type
        logger.info("✅ Successfully imported process_place_type from new_handlers.py")
    except ImportError:
        logger.warning("⚠️ Could not import process_place_type from new_handlers.py")
        new_process_place_type = None
    
    try:
        from app.booking.handlers_fixed import process_place_type as fixed_process_place_type
        logger.info("✅ Successfully imported process_place_type from handlers_fixed.py")
    except ImportError:
        logger.warning("⚠️ Could not import process_place_type from handlers_fixed.py")
        fixed_process_place_type = None

    # Import admin message service
    try:
        from app.booking.services_admin_message import AdminMessageService
        logger.info("✅ Successfully imported AdminMessageService")
    except ImportError:
        logger.warning("⚠️ Could not import AdminMessageService")
        AdminMessageService = None

    # Import venue service
    try:
        from app.booking.services_db import VenueService
        logger.info("✅ Successfully imported VenueService")
    except ImportError:
        logger.warning("⚠️ Could not import VenueService")
        VenueService = None

except Exception as e:
    logger.error(f"Error importing app modules: {e}")
    logger.error(traceback.format_exc())


async def check_handler_registrations():
    """Check which handlers are registered in the dispatcher"""
    logger.info("===== CHECKING HANDLER REGISTRATIONS =====")
    
    try:
        callback_handlers = dp._callback_query_handlers
        
        # Count patterns and handlers
        pattern_counts = {}
        for pattern_handlers in callback_handlers.values():
            for pattern, handlers in pattern_handlers.items():
                if pattern not in pattern_counts:
                    pattern_counts[pattern] = 0
                pattern_counts[pattern] += len(handlers)
                
                # Log each handler for this pattern
                logger.info(f"Pattern: {pattern}")
                for handler in handlers:
                    handler_func = handler['handler']
                    logger.info(f"  - Handler: {handler_func.__name__} from {inspect.getmodule(handler_func).__name__}")
        
        # Check for duplicates
        for pattern, count in pattern_counts.items():
            if count > 1:
                logger.warning(f"⚠️ Duplicate handlers ({count}) found for pattern: {pattern}")
            else:
                logger.info(f"✅ Single handler for pattern: {pattern}")
                
        # Check place_type: pattern specifically
        place_type_pattern = "place_type:"
        found = False
        for pattern_handlers in callback_handlers.values():
            for pattern, handlers in pattern_handlers.items():
                if place_type_pattern in str(pattern):
                    found = True
                    logger.info(f"Found place_type pattern: {pattern} with {len(handlers)} handlers")
                    for handler in handlers:
                        handler_func = handler['handler']
                        logger.info(f"  - Handler: {handler_func.__name__} from {inspect.getmodule(handler_func).__name__}")
        
        if not found:
            logger.error("❌ No handlers found for place_type: pattern!")
        
    except Exception as e:
        logger.error(f"Error checking handler registrations: {e}")
        logger.error(traceback.format_exc())


async def test_admin_message_service():
    """Test the admin message service"""
    logger.info("===== TESTING ADMIN MESSAGE SERVICE =====")
    
    if not AdminMessageService:
        logger.error("❌ AdminMessageService is not available!")
        return
    
    try:
        # Sample cities and place types for testing
        test_cases = [
            ("Moscow", "Restaurant"),
            ("Moscow", "Bar"),
            ("New York", "Restaurant"),
            ("Saint Petersburg", "Cafe"),
            # Try some variations of capitalization and spelling
            ("moscow", "restaurant"),
            ("MOSCOW", "RESTAURANT"),
            ("Moskva", "Bar"),
        ]
        
        for city, place_type in test_cases:
            logger.info(f"Testing admin message retrieval for city='{city}', place_type='{place_type}'")
            
            async for session in get_session():
                # Try with get_admin_message first
                try:
                    message = await AdminMessageService.get_admin_message(session, city, place_type)
                    logger.info(f"get_admin_message result: {message}")
                except Exception as e:
                    logger.error(f"Error in get_admin_message: {e}")
                
                # Try with get_admin_message_flexible if available
                if hasattr(AdminMessageService, 'get_admin_message_flexible'):
                    try:
                        message = await AdminMessageService.get_admin_message_flexible(session, city, place_type)
                        logger.info(f"get_admin_message_flexible result: {message}")
                    except Exception as e:
                        logger.error(f"Error in get_admin_message_flexible: {e}")
                
                # Try direct SQL query
                try:
                    from sqlalchemy import text
                    query = text("SELECT id, city, place_type, message FROM dating_bot.admin_messages WHERE LOWER(city) = LOWER(:city) AND LOWER(place_type) = LOWER(:place_type)")
                    result = await session.execute(query, {"city": city, "place_type": place_type})
                    rows = result.fetchall()
                    logger.info(f"Direct SQL query results: {rows}")
                except Exception as e:
                    logger.error(f"Error in direct SQL query: {e}")
                    
                # Get all admin messages to check what's available
                try:
                    query = text("SELECT id, city, place_type, message FROM dating_bot.admin_messages")
                    result = await session.execute(query)
                    rows = result.fetchall()
                    logger.info(f"All admin messages in DB: {rows}")
                except Exception as e:
                    logger.error(f"Error fetching all admin messages: {e}")
    
    except Exception as e:
        logger.error(f"Error testing admin message service: {e}")
        logger.error(traceback.format_exc())


async def test_venue_service():
    """Test the venue service"""
    logger.info("===== TESTING VENUE SERVICE =====")
    
    if not VenueService:
        logger.error("❌ VenueService is not available!")
        return
    
    try:
        # Sample cities and place types for testing
        test_cases = [
            ("Moscow", "Restaurant"),
            ("Moscow", "Bar"),
            ("New York", "Restaurant"),
            ("Saint Petersburg", "Cafe"),
        ]
        
        for city, place_type in test_cases:
            logger.info(f"Testing venue retrieval for city='{city}', place_type='{place_type}'")
            
            async for session in get_session():
                try:
                    venues = await VenueService.get_venues_by_type_and_city(session, place_type, city)
                    logger.info(f"Found {len(venues)} venues")
                    for venue in venues:
                        logger.info(f"Venue: {venue.name} ({venue.id})")
                except Exception as e:
                    logger.error(f"Error retrieving venues: {e}")
    
    except Exception as e:
        logger.error(f"Error testing venue service: {e}")
        logger.error(traceback.format_exc())


async def check_handler_implementation():
    """Check the implementation of the handlers"""
    logger.info("===== CHECKING HANDLER IMPLEMENTATION =====")
    
    handlers = {
        "patched_handler.py": patched_process_place_type,
        "new_handlers.py": new_process_place_type,
        "handlers_fixed.py": fixed_process_place_type
    }
    
    for name, handler in handlers.items():
        if handler:
            logger.info(f"Analyzing process_place_type from {name}:")
            try:
                source_code = inspect.getsource(handler)
                
                # Look for key components
                admin_message_check = "admin_message" in source_code
                venues_check = "venues" in source_code
                message_editing = "edit_text" in source_code
                callback_answer = "callback_query.answer" in source_code
                
                logger.info(f"  - Admin message handling: {'✅' if admin_message_check else '❌'}")
                logger.info(f"  - Venue retrieval: {'✅' if venues_check else '❌'}")
                logger.info(f"  - Message editing: {'✅' if message_editing else '❌'}")
                logger.info(f"  - Callback answering: {'✅' if callback_answer else '❌'}")
                
                # Log source module
                module = inspect.getmodule(handler)
                logger.info(f"  - Defined in module: {module.__name__}")
                logger.info(f"  - Module file: {module.__file__}")
            except Exception as e:
                logger.error(f"Error analyzing handler from {name}: {e}")
        else:
            logger.warning(f"No handler available from {name}")


async def simulate_place_type_callback():
    """Simulate a place type callback"""
    logger.info("===== SIMULATING PLACE TYPE CALLBACK =====")
    
    # Choose the available handler
    handler = None
    handler_name = ""
    
    if patched_process_place_type:
        handler = patched_process_place_type
        handler_name = "patched_handler.py"
    elif new_process_place_type:
        handler = new_process_place_type
        handler_name = "new_handlers.py"
    elif fixed_process_place_type:
        handler = fixed_process_place_type
        handler_name = "handlers_fixed.py"
    
    if not handler:
        logger.error("❌ No handler available to simulate!")
        return
    
    logger.info(f"Using process_place_type from {handler_name}")
    
    try:
        # Create a mock callback query
        class MockCallbackQuery:
            def __init__(self, data):
                self.data = data
                self.message = MockMessage()
            
            async def answer(self, text=None):
                logger.info(f"callback_query.answer() called with: {text}")
                return True
        
        class MockMessage:
            async def edit_text(self, text, reply_markup=None):
                logger.info(f"Message.edit_text() called with text: {text[:50]}... and markup: {reply_markup}")
                return True
            
            async def answer(self, text, reply_markup=None):
                logger.info(f"Message.answer() called with text: {text[:50]}... and markup: {reply_markup}")
                return True
        
        class MockState:
            def __init__(self):
                self.data = {"city": "Moscow"}
            
            async def get_data(self):
                return self.data
            
            async def update_data(self, **kwargs):
                self.data.update(kwargs)
                logger.info(f"State updated with: {kwargs}")
                return self.data
        
        # Create the mocks
        callback_query = MockCallbackQuery(data="place_type:Restaurant")
        state = MockState()
        
        # Call the handler
        logger.info("Calling process_place_type with mock callback query")
        await handler(callback_query, state)
        logger.info("Handler execution completed")
    
    except Exception as e:
        logger.error(f"Error simulating callback: {e}")
        logger.error(traceback.format_exc())


async def run_diagnostics():
    """Run all diagnostic tests"""
    logger.info("========== STARTING COMPREHENSIVE DIAGNOSTICS ==========")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        
        # Check handler registrations
        await check_handler_registrations()
        
        # Check handler implementation
        await check_handler_implementation()
        
        # Test admin message service
        await test_admin_message_service()
        
        # Test venue service
        await test_venue_service()
        
        # Simulate place type callback
        await simulate_place_type_callback()
        
        logger.info("========== DIAGNOSTICS COMPLETED ==========")
        logger.info(f"See detailed logs in: {log_file}")
        
    except Exception as e:
        logger.error(f"Error in diagnostics: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    try:
        asyncio.run(run_diagnostics())
        print(f"Diagnostics completed. See detailed logs in: {log_file}")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.critical(traceback.format_exc())
        print(f"Diagnostics failed with error: {e}")
        print(f"See detailed logs in: {log_file}")
