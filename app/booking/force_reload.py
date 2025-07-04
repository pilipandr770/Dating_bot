# app/booking/force_reload.py

import os
import sys
import importlib
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("FORCE_RELOAD")

def reload_all_modules():
    """Force reload all booking modules to clear any module caching issues"""
    booking_modules = [
        'app.booking.new_handlers',
        'app.booking.services_db',
        'app.booking.services_admin_message',
        'app.booking.models',
        'app.booking.keyboards',
        'app.booking.__init__',
        'app.booking.admin_message_handlers',
        'app.booking.admin_handlers_dialog',
        'app.booking.admin_venue_list'
    ]
    
    logger.info("🔄 Starting forced reload of booking modules...")
    
    for module_name in booking_modules:
        try:
            # First try to import the module
            try:
                module = importlib.import_module(module_name)
                logger.info(f"✓ Successfully imported {module_name}")
            except ImportError as e:
                logger.warning(f"⚠️ Could not import {module_name}: {e}")
                continue
                
            # Now reload it
            try:
                importlib.reload(module)
                logger.info(f"🔄 Successfully reloaded {module_name}")
            except Exception as e:
                logger.error(f"❌ Failed to reload {module_name}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error with {module_name}: {e}")
    
    logger.info("✅ Module reload completed")

if __name__ == "__main__":
    reload_all_modules()
    
    logger.info("""
    🚀 NEXT STEPS:
    1. Run 'python -m app.booking.verify_setup' to verify the setup
    2. Then run the bot with 'python -m app.main' or 'python app/main.py'
    3. Test the booking functionality in Telegram
    """)
