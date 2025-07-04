# app/booking/services.py

import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Всегда добавляем вывод в консоль
)
logger = logging.getLogger(__name__)

# Тестовый вывод для проверки логирования
logger.info("Simplified booking services loaded - logging is working")

# Класс для работы с бронированиями - упрощенный
class BookingService:
    """Сервис для работы с бронированием мест - упрощенная версия"""
    
    async def get_venue_info(self, place_type):
        """Получить информацию о доступных заведениях"""
        # В будущем здесь будет запрос в БД
        venue_info = {
            "restaurant": [
                {"name": "Итальянская пиццерия", "url": "https://example.com/italian-pizza", "description": "Лучшая пицца в городе"},
                {"name": "Французский ресторан", "url": "https://example.com/french-cuisine", "description": "Изысканная французская кухня"}
            ],
            "cafe": [
                {"name": "Уютное кафе", "url": "https://example.com/cozy-cafe", "description": "Отличное место для встреч и общения"},
                {"name": "Кофейня \"Аромат\"", "url": "https://example.com/coffee-aroma", "description": "Лучший кофе и десерты"}
            ],
            "bar": [
                {"name": "Спорт-бар", "url": "https://example.com/sports-bar", "description": "Трансляции всех важных матчей"},
                {"name": "Коктейль-бар", "url": "https://example.com/cocktail-bar", "description": "Уникальные авторские коктейли"}
            ],
            "cinema": [
                {"name": "Кинотеатр \"Звезда\"", "url": "https://example.com/star-cinema", "description": "Премьеры и классика кино"},
                {"name": "IMAX Кинотеатр", "url": "https://example.com/imax-cinema", "description": "Максимальное погружение в фильм"}
            ],
            "event": [
                {"name": "Городской парк развлечений", "url": "https://example.com/city-park", "description": "Развлечения на свежем воздухе"},
                {"name": "Концертный зал", "url": "https://example.com/concert-hall", "description": "Живая музыка и выступления"}
            ],
            "park": [
                {"name": "Центральный парк", "url": "https://example.com/central-park", "description": "Тихие аллеи и красивые виды"},
                {"name": "Ботанический сад", "url": "https://example.com/botanical-garden", "description": "Редкие растения и экзотические цветы"}
            ]
        }
        
        return venue_info.get(place_type, [])
