#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Diagnostic script to check place type keyboard creation
"""

import asyncio
import logging
import sys
from aiogram.types import InlineKeyboardMarkup

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("keyboard_test.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("keyboard_test")

# Import keyboard function
from app.booking.keyboards import create_place_type_keyboard

async def test_keyboard():
    logger.info("Testing place type keyboard creation")
    
    # Test with default place types
    default_place_types = ['restaurant', 'cafe', 'bar', 'cinema', 'event', 'park']
    logger.info(f"Creating keyboard with default types: {default_place_types}")
    
    keyboard = await create_place_type_keyboard(default_place_types)
    
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

if __name__ == "__main__":
    try:
        logger.info("Starting keyboard test")
        result = asyncio.run(test_keyboard())
        if result:
            logger.info("✅ Keyboard test successful!")
            print("\n✅ Keyboard test successful! The place type buttons should now work correctly.")
        else:
            logger.error("❌ Keyboard test failed!")
            print("\n❌ Keyboard test failed. Check keyboard_test.log for details.")
    except Exception as e:
        logger.error(f"Error running keyboard test: {e}")
        print(f"\n❌ Error running keyboard test: {e}")
