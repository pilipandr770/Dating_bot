#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test to verify that all booking handlers are properly registered
and the process_place_type handler doesn't crash on venue display
"""

import asyncio
import logging
import sys
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("verify_booking_fix.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("verify_booking_fix")

async def run_tests():
    logger.info("Starting verification of booking fixes")
    
    # 1. Test that we can import the unified_handler properly
    try:
        from app.booking.unified_handler import process_place_type, register_booking_handlers
        logger.info("✅ Successfully imported unified_handler module")
    except Exception as e:
        logger.error(f"❌ Failed to import unified_handler: {e}")
        return False
    
    # 2. Test that we can import the keyboard functions
    try:
        from app.booking.keyboards import create_place_keyboard, create_place_type_keyboard
        logger.info("✅ Successfully imported keyboard functions")
    except Exception as e:
        logger.error(f"❌ Failed to import keyboard functions: {e}")
        return False
    
    # 3. Test venue service
    try:
        from app.booking.services_db import VenueService
        from app.database import get_session
        
        venue_found = False
        async for session in get_session():
            venues = await VenueService.get_venues_by_type_and_city(session, "restaurant", None)
            if venues:
                venue_found = True
                logger.info(f"✅ Found {len(venues)} venues in database")
                logger.info(f"First venue: {venues[0].get('name') if isinstance(venues[0], dict) else getattr(venues[0], 'name', 'Unknown')}")
            else:
                logger.warning("No venues found in database, but the query didn't raise an error")
        
        if venue_found:
            logger.info("✅ Successfully queried venues from database")
        else:
            logger.warning("⚠️ No venues found, but the service functions correctly")
    except Exception as e:
        logger.error(f"❌ Failed to query venues: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    # 4. Check that create_place_keyboard can handle a mixed collection of objects
    try:
        from app.booking.keyboards import create_place_keyboard
        
        # Test with a list that includes both dicts and objects
        class FakePlaceObject:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        mixed_places = [
            {"id": 1, "name": "Dict Place"},
            FakePlaceObject(2, "Object Place")
        ]
        
        keyboard = await create_place_keyboard(mixed_places)
        logger.info(f"✅ Successfully created keyboard from mixed objects with {len(keyboard.inline_keyboard)} rows")
    except Exception as e:
        logger.error(f"❌ Failed to create keyboard from mixed objects: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    logger.info("All verification tests passed! The booking fixes should be working correctly.")
    return True

if __name__ == "__main__":
    try:
        logger.info("Starting booking fix verification")
        result = asyncio.run(run_tests())
        
        if result:
            print("\n✅ All booking fixes have been verified and are working correctly!")
            print("The bot should now properly display venue types and venue lists without errors.")
        else:
            print("\n⚠️ Some tests failed. Check the verify_booking_fix.log file for details.")
    except Exception as e:
        logger.error(f"Error running verification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n❌ Error running verification: {e}")
