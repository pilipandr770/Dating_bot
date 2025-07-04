#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to verify the FSM state transition in the booking flow
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
        logging.FileHandler("state_transition_test.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("state_transition_test")

# Import necessary modules
from app.booking.unified_handler import process_place_type, BookingState
from aiogram import types
from aiogram.dispatcher import FSMContext

class MockMessage:
    """Mock message for testing"""
    def __init__(self):
        self.text = "Test message"
    
    async def edit_text(self, *args, **kwargs):
        logger.info(f"Message.edit_text called with {kwargs}")
        return True
    
    async def answer(self, *args, **kwargs):
        logger.info(f"Message.answer called with {args}")
        return True

class MockCallbackQuery:
    """Mock callback query for testing"""
    def __init__(self, data="place_type:restaurant"):
        self.data = data
        self.message = MockMessage()
    
    async def answer(self, *args, **kwargs):
        logger.info(f"CallbackQuery.answer called with {args}")
        return True

class MockState:
    """Mock state for testing FSM transitions"""
    def __init__(self):
        self.state = BookingState.waiting_for_place_type
        self.data = {"city": "Test City"}
        logger.info(f"State initialized to {self.state}")
    
    async def get_data(self):
        return self.data
    
    async def update_data(self, **kwargs):
        self.data.update(kwargs)
        logger.info(f"State data updated: {kwargs}")
    
    async def get_state(self):
        return self.state.state
    
    async def set_state(self, state):
        old_state = self.state
        self.state = state
        logger.info(f"⭐ State changed from {old_state.state} to {state.state}")
        return True

    # For State.finish() support
    async def finish(self):
        logger.info("State finished (reset)")
        self.state = None
        
    # For completeness - other methods that might be called
    def __getattr__(self, name):
        async def wrapper(*args, **kwargs):
            logger.info(f"Called {name} with {args}, {kwargs}")
            return True
        return wrapper

async def test_state_transition():
    """Test that process_place_type transitions state to waiting_for_place"""
    logger.info("Starting FSM state transition test")
    
    # Setup mocks
    callback_query = MockCallbackQuery(data="place_type:restaurant")
    state = MockState()
    
    logger.info("Initial state: waiting_for_place_type")
    
    # Call the handler
    try:
        logger.info("Calling process_place_type handler")
        await process_place_type(callback_query, state)
        logger.info("Handler completed")
        
        # Check the final state
        if state.state == BookingState.waiting_for_place:
            logger.info("✅ State successfully transitioned to waiting_for_place")
            return True
        else:
            logger.error(f"❌ State did not transition correctly, current state: {state.state}")
            return False
    except Exception as e:
        logger.error(f"❌ Error during handler execution: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    try:
        logger.info("Starting state transition test")
        result = asyncio.run(test_state_transition())
        
        if result:
            print("\n✅ State transition test passed! The FSM now correctly transitions to waiting_for_place state.")
            print("This means users can now click on specific venues after selecting a venue type.")
        else:
            print("\n❌ State transition test failed. Check state_transition_test.log for details.")
    except Exception as e:
        logger.error(f"Error running test: {e}")
        logger.error(traceback.format_exc())
        print(f"\n❌ Error running test: {e}")
