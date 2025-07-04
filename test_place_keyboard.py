#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for creating place keyboards with both dictionary and model inputs
"""

import asyncio
import logging
import sys
from aiogram.types import InlineKeyboardMarkup
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("place_keyboard_test.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("place_keyboard_test")

# Import keyboard function and venue service
from app.booking.keyboards import create_place_keyboard
from app.booking.services_db import VenueService
from app.database import get_session

async def test_keyboard_with_dict():
    """Test place keyboard creation with dictionary venues"""
    logger.info("Testing with dictionary venues")
    
    # Create sample venue dictionaries
    sample_venues = [
        {"id": 1, "name": "Test Restaurant 1", "url": "http://example.com/1"},
        {"id": 2, "name": "Test Restaurant 2", "url": "http://example.com/2"},
        {"id": 3, "name": "Test Restaurant 3", "url": "http://example.com/3"}
    ]
    
    logger.info(f"Creating keyboard with {len(sample_venues)} sample venues")
    
    try:
        keyboard = await create_place_keyboard(sample_venues)
        
        if isinstance(keyboard, InlineKeyboardMarkup):
            logger.info(f"✅ Successfully created keyboard with {len(keyboard.inline_keyboard)} rows")
            
            # Print keyboard layout
            for i, row in enumerate(keyboard.inline_keyboard):
                button_texts = [btn.text for btn in row]
                button_callbacks = [btn.callback_data for btn in row]
                logger.info(f"Row {i+1}: Buttons = {button_texts}, Callbacks = {button_callbacks}")
            
            return True
        else:
            logger.error(f"❌ Failed to create keyboard - got {type(keyboard)} instead of InlineKeyboardMarkup")
            return False
    except Exception as e:
        logger.error(f"❌ Error creating keyboard with dictionaries: {e}")
        logger.error(traceback.format_exc())
        return False

async def test_keyboard_with_db_models():
    """Test place keyboard creation with database models"""
    logger.info("Testing with database venue models")
    
    try:
        # Get venues from database
        venues = []
        async for session in get_session():
            try:
                # Get some venues from the database
                venues = await VenueService.get_venues_by_type_and_city(session, "restaurant", None)
                # If none found, try another type
                if not venues:
                    venues = await VenueService.get_venues_by_type_and_city(session, "cafe", None)
                # If still none found, try without filters
                if not venues:
                    # Use raw SQL query as a last resort
                    from sqlalchemy import text
                    result = await session.execute(text("SELECT * FROM dating_bot.places LIMIT 3"))
                    rows = result.fetchall()
                    if rows:
                        venues = rows
            except Exception as e:
                logger.error(f"Error retrieving venues from database: {e}")
                logger.error(traceback.format_exc())
        
        if not venues:
            logger.warning("No venues found in database, skipping this test")
            return True
        
        logger.info(f"Creating keyboard with {len(venues)} database venues")
        logger.info(f"First venue type: {type(venues[0])}")
        
        keyboard = await create_place_keyboard(venues)
        
        if isinstance(keyboard, InlineKeyboardMarkup):
            logger.info(f"✅ Successfully created keyboard with {len(keyboard.inline_keyboard)} rows")
            
            # Print keyboard layout
            for i, row in enumerate(keyboard.inline_keyboard):
                button_texts = [btn.text for btn in row]
                button_callbacks = [btn.callback_data for btn in row]
                logger.info(f"Row {i+1}: Buttons = {button_texts}, Callbacks = {button_callbacks}")
            
            return True
        else:
            logger.error(f"❌ Failed to create keyboard - got {type(keyboard)} instead of InlineKeyboardMarkup")
            return False
    except Exception as e:
        logger.error(f"❌ Error creating keyboard with database models: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    try:
        logger.info("Starting place keyboard tests")
        
        # Test with dictionaries
        dict_result = asyncio.run(test_keyboard_with_dict())
        
        # Test with database models
        db_result = asyncio.run(test_keyboard_with_db_models())
        
        if dict_result and db_result:
            logger.info("✅ All keyboard tests successful!")
            print("\n✅ All keyboard tests successful! The place buttons should now work correctly.")
        else:
            if not dict_result:
                logger.error("❌ Dictionary venue keyboard test failed!")
            if not db_result:
                logger.error("❌ Database venue keyboard test failed!")
            print("\n❌ Some keyboard tests failed. Check place_keyboard_test.log for details.")
    except Exception as e:
        logger.error(f"Error running keyboard tests: {e}")
        logger.error(traceback.format_exc())
        print(f"\n❌ Error running keyboard tests: {e}")
