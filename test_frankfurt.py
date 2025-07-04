import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append('.')
from app.booking.services import BookingService

async def test():
    service = BookingService()
    
    city = "Frankfurt"
    date = "2023-07-01"
    place_type = "restaurant"
    
    logger.info(f"Testing get_recommendations with city={city}, date={date}, place_type={place_type}")
    
    try:
        recommendations = await service.get_recommendations(city, date, place_type)
        logger.info(f"Found {len(recommendations)} recommendations for {city}")
        
        for i, r in enumerate(recommendations):
            logger.info(f"- {i+1}: {r.get('name')} ({r.get('type')}) in {r.get('city')}")
        
        # Test with all types
        logger.info(f"\nTesting with all place types for {city}")
        types = ["restaurant", "cafe", "bar", "cinema", "event", "park"]
        
        for test_type in types:
            recommendations = await service.get_recommendations(city, date, test_type)
            logger.info(f"Place type '{test_type}': found {len(recommendations)} recommendations")
            if recommendations:
                logger.info(f"First item: {recommendations[0].get('name')} ({recommendations[0].get('type')})")
    
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test())
