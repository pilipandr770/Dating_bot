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

def main():
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Now let's test with handlers_fixed.py logger
    from app.booking.handlers_fixed import logger as handlers_logger
    
    handlers_logger.debug("Debug from handlers_fixed")
    handlers_logger.info("Info from handlers_fixed")
    handlers_logger.warning("Warning from handlers_fixed")
    handlers_logger.error("Error from handlers_fixed")
    
    # Test service imports
    try:
        from app.booking.services_admin_message import AdminMessageService
        print("Successfully imported AdminMessageService")
    except Exception as e:
        print(f"Error importing AdminMessageService: {e}")

if __name__ == "__main__":
    main()
