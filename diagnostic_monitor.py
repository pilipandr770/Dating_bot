"""
Diagnostic Monitor for Soul Link Bot

This script monitors log files and database state to help diagnose issues.
Run this in a separate terminal while the bot is running.
"""

import os
import sys
import time
import asyncio
import logging
import traceback
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("monitor")

# Track the last position in each log file
file_positions = {}

class LogFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            file_path = event.src_path
            if file_path.endswith('.log'):
                display_new_log_entries(file_path)

def display_new_log_entries(file_path):
    """Display new log entries from a log file"""
    try:
        if not os.path.exists(file_path):
            return
            
        with open(file_path, 'r', encoding='utf-8') as file:
            # Get last position or start at beginning
            position = file_positions.get(file_path, 0)
            file.seek(position)
            
            # Read new content
            new_content = file.read()
            if new_content:
                print(f"\n--- New entries in {os.path.basename(file_path)} ---")
                print(new_content, end='')
                
            # Update position
            file_positions[file_path] = file.tell()
    except Exception as e:
        logger.error(f"Error reading log file {file_path}: {e}")

async def monitor_database():
    """Check database connection and tables"""
    try:
        logger.info("Checking database connection...")
        
        # Import modules
        from app.database import get_session
        from sqlalchemy import text
        
        async for session in get_session():
            # Check admin_messages table
            try:
                query = text("SELECT COUNT(*) FROM dating_bot.admin_messages")
                result = await session.execute(query)
                count = result.scalar()
                logger.info(f"Admin messages in database: {count}")
                
                # Check sample messages
                if count > 0:
                    query = text("SELECT city, place_type, message FROM dating_bot.admin_messages LIMIT 3")
                    result = await session.execute(query)
                    rows = result.fetchall()
                    logger.info("Sample admin messages:")
                    for row in rows:
                        logger.info(f"  - City: {row[0]}, Type: {row[1]}, Message: {row[2][:30]}...")
            except Exception as e:
                logger.error(f"Error checking admin_messages table: {e}")
                
            # Check place_types table
            try:
                query = text("SELECT COUNT(*) FROM dating_bot.place_types")
                result = await session.execute(query)
                count = result.scalar()
                logger.info(f"Place types in database: {count}")
                
                if count > 0:
                    query = text("SELECT id, name FROM dating_bot.place_types LIMIT 5")
                    result = await session.execute(query)
                    rows = result.fetchall()
                    logger.info("Available place types:")
                    for row in rows:
                        logger.info(f"  - ID: {row[0]}, Name: {row[1]}")
            except Exception as e:
                logger.error(f"Error checking place_types table: {e}")
                
            # Check places table
            try:
                query = text("SELECT COUNT(*) FROM dating_bot.places")
                result = await session.execute(query)
                count = result.scalar()
                logger.info(f"Places in database: {count}")
                
                if count > 0:
                    query = text("SELECT id, name, city, place_type FROM dating_bot.places LIMIT 3")
                    result = await session.execute(query)
                    rows = result.fetchall()
                    logger.info("Sample places:")
                    for row in rows:
                        logger.info(f"  - ID: {row[0]}, Name: {row[1]}, City: {row[2]}, Type: {row[3]}")
            except Exception as e:
                logger.error(f"Error checking places table: {e}")
            
    except Exception as e:
        logger.error(f"Error monitoring database: {e}")
        logger.error(traceback.format_exc())

async def test_admin_message_retrieval():
    """Test the admin message retrieval directly"""
    try:
        logger.info("Testing admin message retrieval...")
        
        from app.database import get_session
        from app.booking.services_admin_message import AdminMessageService
        
        # Test cases - different combinations of city and place type
        test_cases = [
            ("Moscow", "Restaurant"),
            ("Moscow", "Cafe"),
            ("New York", "Bar"),
            ("Франкфурт", "restaurant"),  # Match existing data
            ("FRANKFURT", "RESTAURANT"),  # Test case insensitivity
        ]
        
        for city, place_type in test_cases:
            logger.info(f"Testing retrieval for city='{city}', type='{place_type}'")
            
            async for session in get_session():
                # Try flexible method if available
                if hasattr(AdminMessageService, 'get_admin_message_flexible'):
                    try:
                        message = await AdminMessageService.get_admin_message_flexible(session, city, place_type)
                        logger.info(f"Flexible method result: {message}")
                    except Exception as e:
                        logger.error(f"Error using flexible method: {e}")
                
                # Try standard method
                try:
                    message = await AdminMessageService.get_admin_message(session, city, place_type)
                    logger.info(f"Standard method result: {message}")
                except Exception as e:
                    logger.error(f"Error using standard method: {e}")
    except Exception as e:
        logger.error(f"Error testing admin message retrieval: {e}")
        logger.error(traceback.format_exc())

async def main():
    try:
        # Display current time
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n===== Diagnostic Monitor Started at {now} =====\n")
        
        # Define log files to monitor
        log_files = [
            "unified_handler.log",
            "keyboards.log",
            "verification.log",
            "app.log"
        ]
        
        # Read initial content
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n===== Current content of {log_file} =====")
                with open(log_file, 'r', encoding='utf-8') as file:
                    content = file.read()
                    print(content)
                    file_positions[log_file] = file.tell()
        
        # Test database connectivity and check admin messages
        await monitor_database()
        
        # Test admin message retrieval directly
        await test_admin_message_retrieval()
        
        # Set up file watching
        event_handler = LogFileHandler()
        observer = Observer()
        observer.schedule(event_handler, path='.', recursive=False)
        observer.start()
        
        print("\n===== Now monitoring log files for changes =====")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        
        observer.join()
        
    except Exception as e:
        logger.error(f"Error in diagnostic monitor: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDiagnostic monitor stopped.")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
