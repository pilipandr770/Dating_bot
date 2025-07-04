import asyncio
import logging
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from app.booking.patched_handler import process_place_type
from app.booking.models import BookingState

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("test_patch.log"), logging.StreamHandler()]
)
logger = logging.getLogger("test_patch")

async def mock_state():
    """Create a mock FSMContext for testing"""
    class MockStorage:
        async def get_data(self, *args, **kwargs):
            return {"city": "Kyiv"}
        
        async def set_data(self, *args, **kwargs):
            pass
        
        async def update_data(self, *args, **kwargs):
            pass
    
    class MockFSMContext(FSMContext):
        async def get_data(self):
            return {"city": "Kyiv"}
        
        async def update_data(self, **kwargs):
            logger.info(f"Mock update_data called with {kwargs}")
            return
    
    mock_storage = MockStorage()
    return MockFSMContext(storage=mock_storage, chat=123, user=456)

async def mock_callback_query(place_type="restaurant"):
    """Create a mock callback query for testing"""
    class MockMessage:
        async def edit_text(self, text, reply_markup=None):
            logger.info(f"Mock edit_text called with text: {text[:50]}...")
            logger.info(f"Reply markup provided: {reply_markup is not None}")
            return
        
        async def answer(self, text, reply_markup=None):
            logger.info(f"Mock answer called with text: {text[:50]}...")
            logger.info(f"Reply markup provided: {reply_markup is not None}")
            return
    
    class MockCallbackQuery:
        def __init__(self, place_type):
            self.data = f"place_type:{place_type}"
            self.message = MockMessage()
        
        async def answer(self, text=None):
            logger.info(f"Mock callback answer called with text: {text}")
            return
    
    return MockCallbackQuery(place_type)

async def test_process_place_type():
    """Test the patched process_place_type handler"""
    logger.info("Testing process_place_type handler")
    
    # Create mock objects
    state = await mock_state()
    
    # Test with different place types
    place_types = ["restaurant", "bar", "cafe"]
    
    for place_type in place_types:
        logger.info(f"\n--- Testing with place_type: {place_type} ---\n")
        callback_query = await mock_callback_query(place_type)
        
        try:
            await process_place_type(callback_query, state)
            logger.info(f"process_place_type completed for {place_type} without exceptions")
        except Exception as e:
            logger.error(f"Error while testing process_place_type with {place_type}: {e}")
            import traceback
            logger.error(traceback.format_exc())

async def main():
    logger.info("Starting patch test")
    
    try:
        # Test process_place_type
        await test_process_place_type()
        logger.info("Patch test completed")
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
