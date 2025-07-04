import asyncio
import sys
import logging
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, User as TelegramUser

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append('.')
from app.booking.handlers import process_city, BookingStates, show_places_for_booking, process_place_type
from app.booking.services import BookingService

# Create mock objects
class MockState:
    def __init__(self):
        self.data = {}
    
    async def update_data(self, **kwargs):
        self.data.update(kwargs)
    
    async def get_data(self):
        return self.data
    
    async def set_state(self, state):
        self.current_state = state

class MockMessage:
    def __init__(self, text, user_id=123):
        self.text = text
        self.from_user = MockUser(user_id)
        self.responses = []
    
    async def answer(self, text, reply_markup=None, parse_mode=None):
        self.responses.append({
            'text': text,
            'markup': reply_markup,
            'parse_mode': parse_mode
        })
        logger.info(f"Message response: {text[:50]}... with markup: {reply_markup is not None}")
        return True

class MockUser:
    def __init__(self, user_id):
        self.id = user_id

class MockCallbackQuery:
    def __init__(self, data, user_id=123):
        self.data = data
        self.from_user = MockUser(user_id)
        self.message = MockMessage("Callback message", user_id)
    
    async def answer(self, text=None, show_alert=False):
        logger.info(f"Callback answered: {text if text else 'No text'}")
        return True

async def test_booking_flow():
    logger.info("Starting test of booking flow for Frankfurt")
    
    # Test process_city with Frankfurt
    state = MockState()
    await state.set_state(BookingStates.choosing_city)
    
    # User enters "Frankfurt"
    message = MockMessage("Frankfurt")
    await process_city(message, state)
    
    # Check state after process_city
    state_data = await state.get_data()
    logger.info(f"State after process_city: {state_data}")
    
    # Test process_place_type with 'restaurant'
    callback = MockCallbackQuery("booking:place_type:restaurant")
    await process_place_type(callback, state)
    
    # Check state after process_place_type
    state_data = await state.get_data()
    logger.info(f"State after process_place_type: {state_data}")
    
    # TODO: Mock date selection and test show_places_for_booking
    # This would need more sophisticated mocking

if __name__ == "__main__":
    asyncio.run(test_booking_flow())
