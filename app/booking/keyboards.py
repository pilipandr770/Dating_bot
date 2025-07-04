# app/booking/keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import sys

# Improved logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add file handler with UTF-8 encoding
try:
    file_handler = logging.FileHandler('keyboards.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"Failed to set up file logger for keyboards.py: {e}")
    
logger.info("Keyboards module loaded")

def booking_menu_keyboard(lang="ru"):
    """Клавиатура основного меню бронирования с учетом языка пользователя"""
    texts = {
        "ua": {"show": "🔍 Показати варіанти", "cancel": "❌ Скасувати"},
        "ru": {"show": "🔍 Показать варианты", "cancel": "❌ Отмена"},
        "en": {"show": "🔍 Show options", "cancel": "❌ Cancel"},
        "de": {"show": "🔍 Optionen anzeigen", "cancel": "❌ Abbrechen"}
    }
    
    t = texts.get(lang, texts["en"])
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(t["show"], callback_data="booking:show")
    )
    kb.add(InlineKeyboardButton(t["cancel"], callback_data="booking:cancel"))
    return kb

def place_type_keyboard(lang="ru"):
    """Клавиатура для выбора типа места"""
    texts = {
        "ua": {
            "restaurant": "🍽 Ресторан", "cafe": "☕️ Кафе", "bar": "🍸 Бар",
            "cinema": "🎬 Кінотеатр", "event": "🎭 Подія", "park": "🌳 Парк", "back": "🔙 Назад"
        },
        "ru": {
            "restaurant": "🍽 Ресторан", "cafe": "☕️ Кафе", "bar": "🍸 Бар",
            "cinema": "🎬 Кинотеатр", "event": "🎭 Событие", "park": "🌳 Парк", "back": "🔙 Назад"
        },
        "en": {
            "restaurant": "🍽 Restaurant", "cafe": "☕️ Cafe", "bar": "🍸 Bar",
            "cinema": "🎬 Cinema", "event": "🎭 Event", "park": "🌳 Park", "back": "🔙 Back"
        },
        "de": {
            "restaurant": "🍽 Restaurant", "cafe": "☕️ Café", "bar": "🍸 Bar",
            "cinema": "🎬 Kino", "event": "🎭 Veranstaltung", "park": "🌳 Park", "back": "🔙 Zurück"
        }
    }
    
    t = texts.get(lang, texts["en"])
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(t["restaurant"], callback_data="booking:type:restaurant"),
        InlineKeyboardButton(t["cafe"], callback_data="booking:type:cafe")
    )
    kb.add(
        InlineKeyboardButton(t["bar"], callback_data="booking:type:bar"),
        InlineKeyboardButton(t["cinema"], callback_data="booking:type:cinema")
    )
    kb.add(
        InlineKeyboardButton(t["event"], callback_data="booking:type:event"),
        InlineKeyboardButton(t["park"], callback_data="booking:type:park")
    )
    kb.add(InlineKeyboardButton(t["back"], callback_data="booking:back"))
    return kb

def back_button_keyboard(lang="ru"):
    """Клавиатура с одной кнопкой 'Назад'"""
    texts = {
        "ua": {"back": "🔙 Назад"},
        "ru": {"back": "🔙 Назад"},
        "en": {"back": "🔙 Back"},
        "de": {"back": "🔙 Zurück"}
    }
    
    t = texts.get(lang, texts["en"])
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(t["back"], callback_data="booking:back"))
    return kb

async def create_place_type_keyboard(place_types):
    """Create keyboard with place types based on available types from database
    with improved error handling and safety checks"""
    try:
        kb = InlineKeyboardMarkup(row_width=2)
        
        # Validate place_types
        if not place_types:
            logger.warning("Empty place_types list provided to create_place_type_keyboard")
            # Create default buttons if no place types provided
            default_types = [("Restaurant", "restaurant"), ("Cafe", "cafe"), ("Bar", "bar")]
            kb.add(InlineKeyboardButton("Restaurant", callback_data="place_type:restaurant"))
            kb.add(InlineKeyboardButton("Cafe", callback_data="place_type:cafe"))
            kb.add(InlineKeyboardButton("Bar", callback_data="place_type:bar"))
        else:
            # Add buttons for each place type
            for i in range(0, len(place_types), 2):
                row = []
                try:
                    place_type = place_types[i]
                    if hasattr(place_type, 'name') and place_type.name:
                        button_text = f"{place_type.name}"
                        callback_value = place_type.name.lower()
                    else:
                        button_text = str(place_type)
                        callback_value = str(place_type).lower()
                        
                    row.append(InlineKeyboardButton(
                        button_text, 
                        callback_data=f"place_type:{callback_value}"
                    ))
                    
                    # Add second button in row if available
                    if i + 1 < len(place_types):
                        place_type2 = place_types[i + 1]
                        if hasattr(place_type2, 'name') and place_type2.name:
                            button_text = f"{place_type2.name}"
                            callback_value = place_type2.name.lower()
                        else:
                            button_text = str(place_type2)
                            callback_value = str(place_type2).lower()
                            
                        row.append(InlineKeyboardButton(
                            button_text, 
                            callback_data=f"place_type:{callback_value}"
                        ))
                    
                    kb.row(*row)
                except Exception as e:
                    logger.error(f"Error adding button at index {i}: {e}")
                    # Continue adding other buttons
        
        # Add back button - always include this
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="booking:back_to_city"))
        
        return kb
    except Exception as e:
        logger.error(f"Error in create_place_type_keyboard: {e}")
        # Fallback to a minimal keyboard
        try:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Restaurant", callback_data="place_type:restaurant"))
            kb.add(InlineKeyboardButton("🔙 Back", callback_data="booking:back_to_city"))
            return kb
        except:
            # Last resort empty keyboard
            return InlineKeyboardMarkup()

async def create_place_keyboard(places):
    """Create keyboard with places from database
    Works with both SQLAlchemy models and dictionaries from VenueService"""
    try:
        kb = InlineKeyboardMarkup(row_width=1)
        
        # Log the incoming data for debugging
        logger.info(f"Creating venue keyboard with {len(places)} places")
        logger.debug(f"First place object type: {type(places[0] if places else None)}")
        
        # Process each place with careful error handling
        for i, place in enumerate(places):
            try:
                # Check if place is a dictionary (from VenueService) or a model
                if isinstance(place, dict):
                    place_name = place.get("name", "Unknown place")
                    place_id = place.get("id", 0)
                    logger.debug(f"Place {i+1} (dict): name={place_name}, id={place_id}")
                else:
                    # Assume it's a SQLAlchemy model
                    place_name = getattr(place, 'name', "Unknown place") 
                    place_id = getattr(place, 'id', 0)
                    logger.debug(f"Place {i+1} (model): name={place_name}, id={place_id}")
                
                # Add button for the place
                kb.add(InlineKeyboardButton(
                    f"{place_name}", 
                    callback_data=f"place:{place_id}"
                ))
            except Exception as e:
                logger.error(f"Error processing place at index {i}: {e}")
                # Add a placeholder button if we can't process this place
                kb.add(InlineKeyboardButton(
                    f"Place Option {i+1}", 
                    callback_data=f"place:{i+1}"
                ))
        
        # Add back button
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="booking:back_to_place_type"))
        
        logger.info(f"Venue keyboard created with {len(kb.inline_keyboard)} rows")
        return kb
    except Exception as e:
        logger.error(f"Error creating venue keyboard: {e}")
        # Create a basic fallback keyboard
        try:
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("🔙 Back", callback_data="booking:back_to_place_type"))
            return kb
        except:
            # Last resort empty keyboard
            return InlineKeyboardMarkup()
