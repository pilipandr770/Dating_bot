import asyncio
import logging
import os
import sys

# Add the current directory to the path so that imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging to show all logs including debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Import FSM context for our test
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from app.database import get_session
from sqlalchemy import text

class MockCallbackQuery:
    def __init__(self, data):
        self.data = data
        self.from_user = MockUser()
        self.message = MockMessage()
    
    async def answer(self):
        logger.info("Mock callback.answer() called")

class MockUser:
    def __init__(self, user_id=123456789):
        self.id = user_id

class MockMessage:
    def __init__(self):
        self.text = "Mock message text"
    
    async def edit_text(self, text, reply_markup=None, parse_mode=None):
        logger.info(f"Mock message.edit_text() called with text: {text[:50]}...")
        logger.info(f"Parse mode: {parse_mode}")
        if reply_markup:
            logger.info(f"Reply markup provided")
        return self

    async def answer(self, text, reply_markup=None, parse_mode=None):
        logger.info(f"Mock message.answer() called with text: {text[:50]}...")
        logger.info(f"Parse mode: {parse_mode}")
        if reply_markup:
            logger.info(f"Reply markup provided")
        return self

class MockFSMContext:
    def __init__(self):
        self.data = {"city": "Франкфурт"}
    
    async def get_data(self):
        return self.data
    
    async def update_data(self, **kwargs):
        self.data.update(kwargs)
    
    async def finish(self):
        logger.info("Mock FSMContext.finish() called")

async def test_process_place_type():
    logger.info("=== Starting test for process_place_type ===")
    
    # Import our handler to test
    from app.booking.handlers_fixed import process_place_type
    
    # Create mock objects
    mock_call = MockCallbackQuery(data="booking:type:restaurant")
    mock_state = MockFSMContext()
    
    # Add test admin message to the database
    async for session in get_session():
        # Check if we already have the test message
        from app.booking.services_admin_message import AdminMessageService
        
        # Add a test message if needed
        test_message = await AdminMessageService.add_admin_message(
            session=session,
            city="Франкфурт",
            place_type="restaurant",
            message="Тестовое сообщение для ресторанов в Франкфурте. Скидка 15% с промокодом TEST."
        )
        logger.info(f"Added/updated test admin message")
    
    # Call our handler
    try:
        logger.info("Calling process_place_type handler...")
        await process_place_type(mock_call, mock_state)
        logger.info("process_place_type handler completed successfully")
    except Exception as e:
        logger.error(f"Error calling process_place_type: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    await test_process_place_type()

if __name__ == "__main__":
    asyncio.run(main())
