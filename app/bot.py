# файл: app/bot.py

import asyncio
import logging
import sys
import traceback
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import BotBlocked, Unauthorized, InvalidQueryID, TelegramAPIError
from app.config import TELEGRAM_BOT_TOKEN
from app.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Імпортуємо всі обробники
from app.handlers.start import register_start_handlers
from app.handlers.registration import register_registration_handlers
from app.handlers.swipes import register_swipe_handlers
from app.handlers.chat import register_chat_handlers
from app.handlers.search_settings import register_search_settings_handlers
from app.handlers.tokens import register_token_handlers
from app.handlers.admin import register_admin_handlers
from app.handlers.reservations import register_reservation_handlers
from app.booking import register_booking_handlers, register_admin_venue_dialog_handlers, register_admin_venue_list_handlers, register_admin_message_handlers

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Global error handler to prevent bot crashes
@dp.errors_handler()
async def errors_handler(update, exception):
    """
    Enhanced global error handler that will prevent the bot from crashing.
    Logs the error and continues execution.
    """
    try:
        # Get current exception info
        error_msg = f"Exception: {exception}"
        stack_trace = traceback.format_exc()
        
        # Log different types of errors appropriately
        if isinstance(exception, BotBlocked):
            logger.warning(f"Bot was blocked by user: {update}")
        elif isinstance(exception, Unauthorized):
            logger.warning(f"Unauthorized: {update}")
        elif isinstance(exception, InvalidQueryID):
            logger.warning(f"Invalid query ID: {update}")
        elif isinstance(exception, TelegramAPIError):
            logger.exception(f"Telegram API Error: {exception} - Update: {update}")
        else:
            # For all other exceptions
            logger.critical(f"CRITICAL BOT ERROR: {error_msg}")
            logger.critical(f"UPDATE: {update}")
            logger.critical(f"STACK TRACE: {stack_trace}")
        
        # Extract user info for better tracking
        user_id = None
        chat_id = None
        
        if update:
            if hasattr(update, 'message') and update.message:
                user_id = update.message.from_user.id if update.message.from_user else None
                chat_id = update.message.chat.id
            elif hasattr(update, 'callback_query') and update.callback_query:
                user_id = update.callback_query.from_user.id if update.callback_query.from_user else None
                chat_id = update.callback_query.message.chat.id if update.callback_query.message else None
            
            logger.info(f"Error occurred for user_id={user_id}, chat_id={chat_id}")
        
        # Try to notify the user about the error if possible
        try:
            if update and hasattr(update, 'message') and update.message:
                await update.message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз или обратитесь к администратору.")
            elif update and hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
                if update.callback_query.message:
                    await update.callback_query.message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз или обратитесь к администратору.")
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    except Exception as e:
        # Catch any exception in the error handler itself
        logger.critical(f"ERROR IN ERROR HANDLER: {e}")
        logger.critical(traceback.format_exc())
    
    # Always return True to tell aiogram that error is handled
    return True

# Головна асинхронна функція запуску
async def main():
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Ініціалізація бази
            logger.info("Initializing database...")
            try:
                await init_db()
                logger.info("Database initialized successfully")
            except Exception as db_error:
                logger.critical(f"Database initialization error: {db_error}")
                logger.critical(traceback.format_exc())
                # Wait and retry
                retry_count += 1
                await asyncio.sleep(5)
                continue

            # Реєстрація обробників (each handler registration wrapped individually)
            logger.info("Registering handlers...")
            
            handler_registrations = [
                ("start_handlers", register_start_handlers),
                ("search_settings_handlers", register_search_settings_handlers),
                ("registration_handlers", register_registration_handlers),
                ("swipe_handlers", register_swipe_handlers),
                ("chat_handlers", register_chat_handlers),
                ("token_handlers", register_token_handlers),
                ("admin_handlers", register_admin_handlers),
                ("reservation_handlers", register_reservation_handlers),
                ("booking_handlers", register_booking_handlers),
                ("admin_venue_dialog_handlers", register_admin_venue_dialog_handlers),
                ("admin_venue_list_handlers", register_admin_venue_list_handlers),
                ("admin_message_handlers", register_admin_message_handlers)
            ]
            
            for handler_name, handler_func in handler_registrations:
                try:
                    handler_func(dp)
                    logger.info(f"✅ {handler_name} registered successfully")
                except Exception as handler_error:
                    logger.error(f"❌ Error registering {handler_name}: {handler_error}")
                    logger.error(traceback.format_exc())
            
            logger.info("Handler registration completed")

            # Log the start of the bot
            logger.info("Starting bot with error recovery settings...")
            
            # Запуск бота с параметрами для автоматического восстановления после ошибок
            # Версія aiogram 2.25.1 
            await dp.start_polling(
                reset_webhook=True, 
                timeout=30,      # Timeout for long polling
                relax=0.1,       # Time between requests
                fast=True,       # Skip old updates
                allowed_updates=types.AllowedUpdates.all()  # Process all update types
            )
            
            # If we got here, the bot exited normally
            logger.info("Bot stopped normally")
            break
            
        except Exception as e:
            logger.critical(f"Critical error in main function (attempt {retry_count+1}/{max_retries}): {e}")
            logger.critical(traceback.format_exc())
            
            retry_count += 1
            if retry_count < max_retries:
                # Try to restart if there's a critical error
                logger.info(f"Attempting to restart after critical error in {10} seconds...")
                await asyncio.sleep(10)  # Longer wait between retries
            else:
                logger.critical(f"Max retries ({max_retries}) reached. Stopping bot.")
                break

# Improved startup with watchdog mechanism
if __name__ == '__main__':
    restart_count = 0
    max_restarts = 3
    
    while restart_count < max_restarts:
        try:
            logger.info(f"Starting bot (restart {restart_count}/{max_restarts})")
            asyncio.run(main())
            # If main exits normally, break the loop
            logger.info("Bot exited normally")
            break
        except KeyboardInterrupt:
            logger.info("Bot stopped manually")
            break
        except Exception as e:
            restart_count += 1
            logger.critical(f"Fatal error (restart {restart_count}/{max_restarts}): {e}")
            logger.critical(traceback.format_exc())
            
            if restart_count < max_restarts:
                logger.info(f"Waiting 15 seconds before restarting...")
                # Use time.sleep instead of asyncio.sleep since we're outside of an async function
                import time
                time.sleep(15)
            else:
                logger.critical("Maximum restart attempts reached. Exiting.")
                
    logger.info("Bot process terminated")
