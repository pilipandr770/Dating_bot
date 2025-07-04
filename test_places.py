import asyncio
import sys
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append('.')
from app.booking.services import BookingService

async def test_places_for_city():
    service = BookingService()
    
    # Test cities
    cities = ["Frankfurt", "Berlin", "Paris", "London", "New York"]
    date = "2023-07-01"
    
    for city in cities:
        logger.info(f"\n===== Testing city: {city} =====")
        
        # Test all place types
        place_types = ["restaurant", "cafe", "bar", "cinema", "event", "park"]
        
        for place_type in place_types:
            recommendations = await service.get_recommendations(city, date, place_type)
            
            logger.info(f"{city} - {place_type}: found {len(recommendations)} recommendations")
            
            if recommendations:
                # Print first recommendation details
                rec = recommendations[0]
                logger.info(f"First item: {rec.get('name')} ({rec.get('type')}) in {rec.get('city')}")
                
                # Check if the recommendation city matches the requested city
                if rec.get('city') != city:
                    logger.warning(f"City mismatch! Requested {city} but got {rec.get('city')}")
            else:
                logger.warning(f"No recommendations found for {city} - {place_type}")
    
    # Test a specific booking search
    city = "Frankfurt"
    place_type = "park"
    
    logger.info(f"\n===== Detailed test for {city} parks =====")
    parks = await service.get_recommendations(city, date, place_type)
    
    if parks:
        logger.info(f"Found {len(parks)} parks in {city}")
        # Print full details of each park
        for i, park in enumerate(parks):
            logger.info(f"Park {i+1}:\n{json.dumps(park, indent=2)}")
    else:
        logger.error(f"No parks found for {city}")

if __name__ == "__main__":
    asyncio.run(test_places_for_city())
