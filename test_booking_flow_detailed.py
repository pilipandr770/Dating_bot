import asyncio
import sys
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='booking_test_trace.log',  # Save to file for analysis
                   filemode='w')  # Overwrite previous log
logger = logging.getLogger(__name__)

# Also output to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

sys.path.append('.')
from app.booking.services import BookingService

# Mock objects for testing
class MockState:
    def __init__(self):
        self.data = {}
    
    async def update_data(self, **kwargs):
        self.data.update(kwargs)
        logger.info(f"State updated: {kwargs}")
        return self.data
    
    async def get_data(self):
        return self.data

# Test the full flow from city to place selection
async def test_booking_flow():
    logger.info("========== STARTING BOOKING FLOW TEST ==========")
    
    # Initialize service
    service = BookingService()
    state = MockState()
    
    # Step 1: User enters city
    city = "Frankfurt"
    logger.info(f"STEP 1: User enters city: {city}")
    await state.update_data(city=city)
    
    # Step 2: User selects place type
    place_type = "restaurant"
    logger.info(f"STEP 2: User selects place type: {place_type}")
    await state.update_data(place_type=place_type)
    
    # Step 3: User selects date
    date = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"STEP 3: User selects date: {date}")
    await state.update_data(date=date)
    
    # Step 4: Get recommendations for the selected parameters
    logger.info(f"STEP 4: Getting recommendations for {city}, {date}, {place_type}")
    try:
        recommendations = await service.get_recommendations(city, date, place_type)
        logger.info(f"Found {len(recommendations)} recommendations")
        
        # Check if we have restaurants specifically
        restaurants = [r for r in recommendations if r.get('type') == 'restaurant']
        logger.info(f"Found {len(restaurants)} restaurants")
        
        # Print details of each restaurant
        for i, rec in enumerate(restaurants):
            logger.info(f"Restaurant {i+1}:")
            logger.info(json.dumps(rec, indent=2))
        
        # Save recommendations to state
        await state.update_data(recommendations=recommendations)
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        return
    
    if not recommendations:
        logger.error("No recommendations found!")
        return
    
    # Step 5: User selects a place
    selected_place = recommendations[0]
    logger.info(f"STEP 5: User selects place: {selected_place['name']}")
    await state.update_data(selected_place=selected_place)
    
    # Step 6: Format date for display
    try:
        time_str = selected_place.get('time', '')
        display_date = date
        if isinstance(time_str, str) and "T" in time_str:
            try:
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                display_date = dt.strftime("%d.%m.%Y %H:%M")
            except Exception as e:
                logger.error(f"Error formatting date: {e}", exc_info=True)
        
        logger.info(f"STEP 6: Formatted date: {display_date}")
    except Exception as e:
        logger.error(f"Error in date formatting: {e}", exc_info=True)
    
    # Step 7: User confirms booking
    logger.info("STEP 7: User confirms booking")
    
    try:
        reservation_data = {
            "user_id": "123456789",  # Mock user ID
            "place_id": selected_place['id'],
            "place_type": selected_place['type'],
            "reservation_time": selected_place['time'],
            "status": "confirmed",
            "name": selected_place['name'],
            "address": selected_place.get('address', 'Unknown'),
            "city": city
        }
        
        logger.info(f"Would create reservation with data: {json.dumps(reservation_data, indent=2)}")
        
        # In a real scenario, we would call service.create_reservation() here
        
        logger.info("Booking flow completed successfully!")
    except Exception as e:
        logger.error(f"Error in confirmation step: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_booking_flow())
