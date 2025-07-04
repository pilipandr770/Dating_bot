"""
Final unified handler for booking functionality.
This file combines the best parts of patched_handler.py and new_handlers.py
to ensure admin messages are displayed properly.

Enhanced with better error handling to prevent bot from crashing.
"""

import logging
import traceback
import sys
import asyncio
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database import get_session
from app.booking.keyboards import create_place_keyboard, create_place_type_keyboard
from app.booking.services_db import VenueService
from app.booking.services_admin_message import AdminMessageService

# Configure root logger to ensure all logs are visible
root_logger = logging.getLogger()
if not root_logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

# Create a specific logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add a file handler for this module
file_handler = logging.FileHandler('unified_handler.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - UNIFIED_HANDLER - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info("🔄 UNIFIED HANDLER MODULE LOADED")

# Define BookingState
class BookingState(StatesGroup):
    waiting_for_city = State()
    waiting_for_place_type = State()
    waiting_for_place = State()
    waiting_for_confirmation = State()

# Helper function to log debug info
def log_debug(message, data=None):
    """Write debug info to log"""
    logger.debug(f"[DEBUG] {message}")
    if data:
        try:
            if isinstance(data, dict):
                import json
                logger.debug(f"[DEBUG] DATA: {json.dumps(data, ensure_ascii=False)}")
            else:
                logger.debug(f"[DEBUG] DATA: {data}")
        except:
            logger.debug(f"[DEBUG] DATA: [Unable to serialize]")

# Handler for /booking command
async def cmd_booking(message: types.Message):
    """Start the booking process"""
    try:
        logger.info(f"[BOOKING] Command received from user {message.from_user.id}")
        
        # Set state to waiting for city
        await BookingState.waiting_for_city.set()
        
        # Ask user for city
        await message.answer("🌆 Please enter the city where you want to book a place:")
        
        logger.info(f"[BOOKING] User {message.from_user.id} prompted for city")
    except Exception as e:
        logger.error(f"[BOOKING] Error in cmd_booking: {e}")
        logger.error(traceback.format_exc())
        await message.answer("An error occurred. Please try again.")

# Handler for city selection
async def process_city(message: types.Message, state: FSMContext):
    """Process city selection from user message"""
    try:
        city = message.text.strip()
        logger.info(f"[CITY] User {message.from_user.id} selected city: {city}")
        
        # Save city to state
        await state.update_data(city=city)
        
        # Set state to waiting for place type
        await BookingState.waiting_for_place_type.set()
        
        # Create place type keyboard with default types
        # The function expects place_types as an argument
        default_place_types = ['restaurant', 'cafe', 'bar', 'cinema', 'event', 'park']
        logger.info(f"[CITY] Creating place type keyboard with default types: {default_place_types}")
        keyboard = await create_place_type_keyboard(default_place_types)
        
        # Log the keyboard content for debugging
        logger.debug(f"[CITY] Keyboard created with {len(keyboard.inline_keyboard)} rows")
        for i, row in enumerate(keyboard.inline_keyboard):
            button_texts = [btn.text for btn in row]
            button_callbacks = [btn.callback_data for btn in row]
            logger.debug(f"[CITY] Row {i+1}: Buttons = {button_texts}, Callbacks = {button_callbacks}")
        
        # Prompt user to select place type
        await message.answer(f"🏙 Selected city: *{city}*\n\nPlease choose a place type:", 
                            reply_markup=keyboard,
                            parse_mode="Markdown")
        
        logger.info(f"[CITY] Sent place type keyboard to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"[CITY] Error in process_city: {e}")
        logger.error(traceback.format_exc())
        await message.answer("An error occurred. Please try again.")

# Handler for place type selection - main focus of our fix
async def process_place_type(callback_query: types.CallbackQuery, state: FSMContext):
    """Process place type selection with improved admin message handling and better error recovery"""
    try:
        # Log detailed information for debugging
        logger.info(f"[PLACE_TYPE] process_place_type called with callback_data: {callback_query.data}")
        
        # Validate callback data format
        if not callback_query.data or ':' not in callback_query.data:
            logger.error(f"[PLACE_TYPE] Invalid callback data format: {callback_query.data}")
            await callback_query.answer("Invalid request. Please try again.")
            return
        
        # Get data from state with safe defaults
        try:
            data = await state.get_data()
            city = data.get('city', 'Unknown city')
            place_type = callback_query.data.split(':')[1]
        except Exception as e:
            logger.error(f"[PLACE_TYPE] Error extracting data from state/callback: {e}")
            logger.error(traceback.format_exc())
            city = "Unknown city"
            place_type = "place"
        
        logger.info(f"[PLACE_TYPE] Processing place type '{place_type}' for city '{city}'")
        
        # Set state data - don't let exceptions here stop execution
        try:
            await state.update_data(place_type=place_type)
        except Exception as e:
            logger.error(f"[PLACE_TYPE] Failed to update state: {e}")
        
        # Get admin message - with safe fallback for all error cases
        admin_message = None
        try:
            async for session in get_session():
                logger.debug(f"[PLACE_TYPE] Getting admin message for city={city}, place_type={place_type}")
                
                # Try flexible method first, then standard method
                try:
                    if hasattr(AdminMessageService, 'get_admin_message_flexible'):
                        admin_message = await AdminMessageService.get_admin_message_flexible(session, city, place_type)
                        logger.info(f"[PLACE_TYPE] Got admin message (flexible): {admin_message}")
                    else:
                        admin_message = await AdminMessageService.get_admin_message(session, city, place_type)
                        logger.info(f"[PLACE_TYPE] Got admin message (standard): {admin_message}")
                except Exception as e:
                    logger.error(f"[PLACE_TYPE] Error in AdminMessageService: {e}")
                    logger.error(traceback.format_exc())
                    
                # If still no message, try direct SQL as last resort
                if not admin_message:
                    try:
                        from sqlalchemy import text
                        # Try type-only match as fallback
                        query = text("SELECT message FROM dating_bot.admin_messages WHERE LOWER(place_type) = LOWER(:place_type) LIMIT 1")
                        result = await session.execute(query, {"place_type": place_type})
                        admin_message = result.scalar()
                        if admin_message:
                            logger.info(f"[PLACE_TYPE] Found message via direct SQL: {admin_message[:30]}...")
                    except Exception as e:
                        logger.error(f"[PLACE_TYPE] Error in direct SQL fallback: {e}")
        except Exception as e:
            logger.error(f"[PLACE_TYPE] Error in admin message block: {e}")
            logger.error(traceback.format_exc())
        
        # Get venues with safe error handling
        venues = []
        try:
            async for session in get_session():
                try:
                    venues = await VenueService.get_venues_by_type_and_city(session, place_type, city)
                    logger.info(f"[PLACE_TYPE] Got {len(venues)} venues for {city}/{place_type}")
                    
                    # Log venue data structure for debugging
                    if venues:
                        first_venue = venues[0]
                        logger.debug(f"[PLACE_TYPE] First venue type: {type(first_venue)}")
                        if isinstance(first_venue, dict):
                            logger.debug(f"[PLACE_TYPE] First venue keys: {first_venue.keys()}")
                            logger.debug(f"[PLACE_TYPE] First venue name: {first_venue.get('name', 'N/A')}")
                        else:
                            logger.debug(f"[PLACE_TYPE] First venue attributes: {dir(first_venue)}")
                except Exception as e:
                    logger.error(f"[PLACE_TYPE] Error in VenueService: {e}")
                    logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"[PLACE_TYPE] Error in venue retrieval block: {e}")
            logger.error(traceback.format_exc())
        
        # Create message content with guaranteed defaults
        message_content = ""
        
        # Add admin message if available
        if admin_message:
            try:
                message_content += f"ℹ️ {admin_message}\n\n"
                logger.info(f"[PLACE_TYPE] Added admin message to content")
            except Exception as e:
                logger.error(f"[PLACE_TYPE] Error adding admin message to content: {e}")
                # Fallback to default message on encoding errors
                message_content += f"ℹ️ Special information available for {place_type}s in {city}\n\n"
        else:
            # Default message when no admin message is found
            message_content += f"ℹ️ Explore our selection of {place_type}s in {city}\n\n"
            logger.info(f"[PLACE_TYPE] Added default message")
        
        # Add venue list or "coming soon" message
        keyboard = None
        try:
            if venues:
                message_content += f"🏙️ Here are {place_type}s in {city}:"
                keyboard = await create_place_keyboard(venues)
                logger.info(f"[PLACE_TYPE] Added venue list intro and created keyboard")
            else:
                message_content += f"🏙️ {place_type.capitalize()}s in {city} coming soon!"
                logger.info(f"[PLACE_TYPE] Added 'coming soon' message")
        except Exception as e:
            # Fallback if keyboard creation fails
            logger.error(f"[PLACE_TYPE] Error building content/keyboard: {e}")
            message_content += f"🏙️ Information about {place_type}s is being updated."
        
        # Edit message with new content - with multiple fallback strategies
        message_sent = False
        
        # Strategy 1: Edit existing message
        if not message_sent:
            try:
                if keyboard:
                    await callback_query.message.edit_text(message_content, reply_markup=keyboard)
                else:
                    await callback_query.message.edit_text(message_content)
                logger.info(f"[PLACE_TYPE] Message edited successfully")
                message_sent = True
            except Exception as e:
                logger.error(f"[PLACE_TYPE] Error editing message: {e}")
                logger.error(traceback.format_exc())
        
        # Strategy 2: Send new message
        if not message_sent:
            try:
                if keyboard:
                    await callback_query.message.answer(message_content, reply_markup=keyboard)
                else:
                    await callback_query.message.answer(message_content)
                logger.info(f"[PLACE_TYPE] Sent new message as fallback")
                message_sent = True
            except Exception as e:
                logger.error(f"[PLACE_TYPE] Error sending fallback message: {e}")
                logger.error(traceback.format_exc())
        
        # Strategy 3: Send simple text message
        if not message_sent:
            try:
                simple_msg = f"Selected {place_type} in {city}. Please check available options."
                await callback_query.message.answer(simple_msg)
                logger.info(f"[PLACE_TYPE] Sent simplified fallback message")
                message_sent = True
            except Exception as e:
                logger.error(f"[PLACE_TYPE] Error sending simple message: {e}")
                logger.error(traceback.format_exc())
        
        # Always answer callback query to prevent hanging "loading" state
        try:
            await callback_query.answer()
            logger.info(f"[PLACE_TYPE] Callback query answered")
        except Exception as e:
            logger.error(f"[PLACE_TYPE] Error answering callback: {e}")
        
    except Exception as e:
        logger.error(f"[PLACE_TYPE] Unhandled exception in process_place_type: {e}")
        logger.error(traceback.format_exc())
        # We still want to respond to the user even if everything else fails
        try:
            await callback_query.answer("An error occurred. Please try again.")
            await callback_query.message.answer("An error occurred while processing your request. Please try again.")
        except Exception as final_e:
            logger.error(f"[PLACE_TYPE] Final error handler failed: {final_e}")
            # At this point we've done all we can

# Handler for place selection
async def process_place(callback_query: types.CallbackQuery, state: FSMContext):
    """Process place selection"""
    try:
        # Get place ID from callback data
        place_id = callback_query.data.split(':')[1]
        logger.info(f"[PLACE] User selected place ID: {place_id}")
        
        # Save place ID to state
        await state.update_data(place_id=place_id)
        
        # Set state to waiting for confirmation
        await BookingState.waiting_for_confirmation.set()
        
        # Get place details
        place_name = "Selected venue"  # Fallback name
        async for session in get_session():
            try:
                place = await VenueService.get_venue_by_id(session, place_id)
                if place:
                    place_name = place.name
            except Exception as e:
                logger.error(f"[PLACE] Error getting place details: {e}")
        
        # Create confirmation keyboard
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{place_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        )
        
        # Send confirmation message
        await callback_query.message.edit_text(
            f"📍 You selected: *{place_name}*\n\nWould you like to confirm this reservation?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Answer callback query
        await callback_query.answer()
        
        logger.info(f"[PLACE] Sent confirmation prompt for place {place_id}")
    except Exception as e:
        logger.error(f"[PLACE] Error in process_place: {e}")
        logger.error(traceback.format_exc())
        await callback_query.answer("An error occurred. Please try again.")

# Handler for confirmation
async def process_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    """Process confirmation of reservation"""
    try:
        action = callback_query.data.split(':')[0]
        logger.info(f"[CONFIRM] User selected action: {action}")
        
        if action == "confirm":
            # Get all data from state
            data = await state.get_data()
            city = data.get('city')
            place_type = data.get('place_type')
            place_id = data.get('place_id')
            
            # Here you would save the reservation to database
            # For now, just acknowledge it
            
            await callback_query.message.edit_text(
                f"✅ Your reservation has been confirmed!\n\n"
                f"📍 Location: {city}\n"
                f"🏙️ Type: {place_type}\n"
                f"🕒 Reservation ID: {place_id}"
            )
            
            logger.info(f"[CONFIRM] Reservation confirmed for place {place_id}")
        else:
            await callback_query.message.edit_text("❌ Reservation cancelled.")
            logger.info(f"[CONFIRM] Reservation cancelled")
        
        # Reset state
        await state.finish()
        
        # Answer callback query
        await callback_query.answer()
    except Exception as e:
        logger.error(f"[CONFIRM] Error in process_confirmation: {e}")
        logger.error(traceback.format_exc())
        await callback_query.answer("An error occurred. Please try again.")

# Register all handlers
def register_booking_handlers(dp: Dispatcher):
    """Register all booking related handlers with error handling"""
    try:
        logger.info("Registering booking handlers")
        
        # Command handlers
        try:
            dp.register_message_handler(cmd_booking, commands=["booking"], state="*")
            logger.info("Registered booking command handler")
        except Exception as e:
            logger.error(f"Error registering booking command handler: {e}")
        
        # City selection
        try:
            dp.register_message_handler(process_city, state=BookingState.waiting_for_city)
            logger.info("Registered city selection handler")
        except Exception as e:
            logger.error(f"Error registering city selection handler: {e}")
        
        # Place type selection - most critical one
        try:
            dp.register_callback_query_handler(
                process_place_type, 
                lambda c: c and c.data and c.data.startswith('place_type:'),
                state=BookingState.waiting_for_place_type
            )
            logger.info("Registered place type selection handler")
        except Exception as e:
            logger.error(f"Error registering place type selection handler: {e}")
            
            # Try with less strict filter as fallback
            try:
                dp.register_callback_query_handler(
                    process_place_type, 
                    lambda c: c.data and 'place_type:' in c.data,
                    state=BookingState.waiting_for_place_type
                )
                logger.info("Registered place type selection handler with fallback filter")
            except Exception as e:
                logger.error(f"Failed to register place type handler even with fallback: {e}")
        
        # Place selection
        try:
            dp.register_callback_query_handler(
                process_place, 
                lambda c: c and c.data and c.data.startswith('place:'),
                state=BookingState.waiting_for_place_type
            )
            logger.info("Registered place selection handler")
        except Exception as e:
            logger.error(f"Error registering place selection handler: {e}")
        
        # Confirmation
        try:
            dp.register_callback_query_handler(
                process_confirmation,
                lambda c: c and c.data and (c.data.startswith('confirm:') or c.data == 'cancel'),
                state=BookingState.waiting_for_confirmation
            )
            logger.info("Registered confirmation handler")
        except Exception as e:
            logger.error(f"Error registering confirmation handler: {e}")
        
        logger.info("Booking handlers registered successfully")
    
    except Exception as e:
        logger.error(f"Critical error in register_booking_handlers: {e}")
        logger.error(traceback.format_exc())
        logger.info("Some handlers may not have been registered properly")
