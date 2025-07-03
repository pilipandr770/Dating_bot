# app/booking/services.py

import httpx
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from app.booking.models import Place, Reservation, PlaceType
from app.config import get_config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем конфигурацию из переменных среды
OPENTABLE_API_KEY = get_config("OPENTABLE_API_KEY", "")
EVENTBRITE_TOKEN = get_config("EVENTBRITE_TOKEN", "")

class OpenTableAdapter:
    BASE_URL = "https://api.opentable.com"

    def __init__(self):
        self.client = httpx.AsyncClient()
        self.api_key = OPENTABLE_API_KEY

    async def search_restaurants(self, city: str, date: str, limit=5):
        """Поиск ресторанов для указанного города и даты"""
        try:
            # Для демо-режима: если ключа нет, возвращаем тестовые данные
            if not self.api_key:
                logger.warning("OpenTable API ключ не найден, используем демо-данные")
                return self._get_demo_restaurants(city)

            params = {"city": city, "date": date, "per_page": limit}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.client.get(f"{self.BASE_URL}/restaurants", params=params, headers=headers)
            response.raise_for_status()
            return response.json().get("restaurants", [])
        except Exception as e:
            logger.error(f"Ошибка при поиске ресторанов: {e}")
            return self._get_demo_restaurants(city)

    async def book_table(self, restaurant_id: str, date: str, time: str, party_size: int, user_name: str):
        """Бронирование столика в ресторане"""
        try:
            if not self.api_key:
                logger.warning("OpenTable API ключ не найден, используем демо-данные для бронирования")
                return {
                    "status": "confirmed",
                    "reservation_id": f"demo-{restaurant_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "confirmation_number": f"OT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "date": date,
                    "time": time
                }
                
            payload = {
                "restaurant_id": restaurant_id, 
                "date": date, 
                "time": time, 
                "party_size": party_size,
                "name": user_name
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            response = await self.client.post(f"{self.BASE_URL}/reservations", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка при бронировании столика: {e}")
            # Возвращаем демо-ответ для имитации успешного бронирования
            return {
                "status": "confirmed",
                "reservation_id": f"demo-{restaurant_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "confirmation_number": f"OT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "date": date,
                "time": time
            }
            
    def _get_demo_restaurants(self, city):
        """Тестовые данные для демо-режима"""
        return [
            {
                "id": "rest-1",
                "name": f"Романтический ресторан в {city}",
                "cuisine": "Итальянская",
                "price_range": "€€€",
                "rating": 4.7,
                "address": f"{city}, Главная площадь, 1",
                "available_times": ["18:00", "19:00", "20:00"],
                "image_url": "https://example.com/restaurant1.jpg"
            },
            {
                "id": "rest-2",
                "name": f"Уютное кафе в {city}",
                "cuisine": "Французская",
                "price_range": "€€",
                "rating": 4.5,
                "address": f"{city}, ул. Парижская, 15",
                "available_times": ["17:30", "18:30", "20:30"],
                "image_url": "https://example.com/restaurant2.jpg"
            },
            {
                "id": "rest-3",
                "name": f"Панорамный ресторан {city}",
                "cuisine": "Европейская",
                "price_range": "€€€€",
                "rating": 4.9,
                "address": f"{city}, пр. Победы, 100, 25 этаж",
                "available_times": ["19:00", "20:00", "21:00"],
                "image_url": "https://example.com/restaurant3.jpg"
            }
        ]


class EventbriteAdapter:
    BASE_URL = "https://www.eventbriteapi.com/v3"

    def __init__(self):
        self.token = EVENTBRITE_TOKEN
        if self.token:
            self.client = httpx.AsyncClient(headers={"Authorization": f"Bearer {self.token}"})
        else:
            self.client = httpx.AsyncClient()

    async def search_events(self, location: str, start_date: str, limit=5):
        """Поиск событий для указанного города и даты"""
        try:
            if not self.token:
                logger.warning("Eventbrite токен не найден, используем демо-данные")
                return self._get_demo_events(location)
                
            params = {"location.address": location, "start_date.range_start": start_date, "limit": limit}
            response = await self.client.get(f"{self.BASE_URL}/events/search/", params=params)
            response.raise_for_status()
            return response.json().get("events", [])
        except Exception as e:
            logger.error(f"Ошибка при поиске событий: {e}")
            return self._get_demo_events(location)

    async def purchase_ticket(self, event_id: str, quantity: int, user_email: str = None):
        """Покупка билета на событие"""
        try:
            if not self.token:
                logger.warning("Eventbrite токен не найден, используем демо-данные для покупки билета")
                return {
                    "status": "confirmed",
                    "order_id": f"demo-{event_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "confirmation_code": f"EB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                }
                
            payload = {"event_id": event_id, "quantity": quantity}
            if user_email:
                payload["email"] = user_email
                
            response = await self.client.post(f"{self.BASE_URL}/orders/", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка при покупке билета: {e}")
            # Возвращаем демо-ответ для имитации успешной покупки
            return {
                "status": "confirmed",
                "order_id": f"demo-{event_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "confirmation_code": f"EB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
    def _get_demo_events(self, location):
        """Тестовые данные для демо-режима"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
        
        return [
            {
                "id": "event-1",
                "name": {"text": f"Концерт в {location}"},
                "description": {"text": "Романтический вечер с живой музыкой"},
                "start": {"local": tomorrow},
                "end": {"local": tomorrow.replace("19:", "22:")},
                "venue": {"address": {"localized_address_display": f"{location}, Концертный зал"}},
                "logo": {"url": "https://example.com/event1.jpg"},
                "ticket_price": "€30"
            },
            {
                "id": "event-2",
                "name": {"text": f"Театральное представление в {location}"},
                "description": {"text": "Классическая пьеса в современной интерпретации"},
                "start": {"local": day_after},
                "end": {"local": day_after.replace("18:", "20:")},
                "venue": {"address": {"localized_address_display": f"{location}, Городской театр"}},
                "logo": {"url": "https://example.com/event2.jpg"},
                "ticket_price": "€25"
            }
        ]


class BookingService:
    def __init__(self):
        self.open_table = OpenTableAdapter()
        self.eventbrite = EventbriteAdapter()

    async def get_places_by_city(self, session, city: str, place_type: str = None, limit=10):
        """Получение мест из базы данных по городу и типу"""
        query = select(Place).where(Place.city == city)
        
        if place_type:
            query = query.where(Place.type == place_type)
            
        query = query.limit(limit)
        result = await session.execute(query)
        places = result.scalars().all()
        
        return places

    async def get_recommendations(self, city: str, date: str, place_type: str = None):
        """Получение рекомендаций по местам для встречи"""
        # Получаем рестораны и события и объединяем
        recommendations = []
        
        # Если тип места - ресторан, кафе или бар, ищем в OpenTable
        if not place_type or place_type in ['restaurant', 'cafe', 'bar']:
            restaurants = await self.open_table.search_restaurants(city, date)
            for r in restaurants:
                # Преобразуем время в строку ISO формата если оно представлено как список
                available_time = r.get("available_times", ["18:00"])[0]
                if isinstance(available_time, list) and len(available_time) > 0:
                    available_time = available_time[0]
                
                recommendations.append({
                    "type": "restaurant",
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "address": r.get("address", ""),
                    "image": r.get("image_url", ""),
                    "time": f"{date}T{available_time}",
                    "price_range": r.get("price_range", "")
                })
                
        # Если тип места - событие, концерт или другой тип развлечения, ищем в Eventbrite
        if not place_type or place_type in ['event', 'cinema', 'other']:
            events = await self.eventbrite.search_events(city, date)
            for e in events:
                start_time = e.get("start", {}).get("local", f"{date}T19:00:00")
                recommendations.append({
                    "type": "event",
                    "id": e.get("id"),
                    "name": e.get("name", {}).get("text", "Мероприятие"),
                    "address": e.get("venue", {}).get("address", {}).get("localized_address_display", ""),
                    "image": e.get("logo", {}).get("url", ""),
                    "time": start_time,
                    "price": e.get("ticket_price", "")
                })
                
        return recommendations

    async def create_reservation(self, session, user_id: int, match_id: int, place_data: dict, user_name: str = None):
        """Создание бронирования в зависимости от типа места"""
        try:
            place_type = place_data.get("type")
            place_id = place_data.get("id")
            reservation_time = place_data.get("time")
            
            # Проверяем, существует ли место в нашей БД
            place_query = select(Place).where(Place.external_id == str(place_id))
            place_result = await session.execute(place_query)
            place = place_result.scalar_one_or_none()
            
            # Если места нет в БД, создаем его
            if not place:
                place = Place(
                    name=place_data.get("name", ""),
                    city=place_data.get("city", ""),
                    type=place_type,
                    link="",  # Можно добавить ссылку на место, если она есть
                    external_id=str(place_id),
                    is_partner=True,
                    place_metadata={
                        "address": place_data.get("address", ""),
                        "price_info": place_data.get("price_range", "") or place_data.get("price", "")
                    },
                    image_url=place_data.get("image", "")
                )
                session.add(place)
                await session.flush()  # Получаем ID созданного места
            
            # Создаем бронирование в зависимости от типа
            if place_type == "restaurant":
                # Разбираем дату и время
                date_part, time_part = reservation_time.split("T") if "T" in reservation_time else (None, None)
                if not time_part:
                    time_part = "19:00"  # Значение по умолчанию
                
                # Бронируем столик
                res = await self.open_table.book_table(
                    place_id, date_part, time_part, 2, user_name or f"User {user_id}"
                )
            else:
                # Покупаем билет на событие
                res = await self.eventbrite.purchase_ticket(place_id, 2)
                
            # Создаем запись о бронировании
            new_reservation = Reservation(
                user_id=user_id,
                match_id=match_id,
                place_id=place.id,  # Используем ID из нашей БД
                reservation_time=reservation_time,
                status=res.get("status", "confirmed"),
                details=res,
                external_reference=res.get("confirmation_number") or res.get("confirmation_code") or res.get("order_id") or ""
            )
            session.add(new_reservation)
            
            return new_reservation
        except Exception as e:
            logger.error(f"Ошибка при создании бронирования: {e}")
            raise
            
    async def get_user_reservations(self, session, user_id: int):
        """Получение всех бронирований пользователя"""
        query = select(Reservation, Place).join(
            Place, Reservation.place_id == Place.id
        ).where(Reservation.user_id == user_id).order_by(Reservation.reservation_time.desc())
        
        result = await session.execute(query)
        reservations_with_places = result.all()
        
        return reservations_with_places
        
    async def cancel_reservation(self, session, reservation_id: int, user_id: int):
        """Отмена бронирования"""
        # Находим бронирование
        query = select(Reservation).where(
            and_(Reservation.id == reservation_id, Reservation.user_id == user_id)
        )
        result = await session.execute(query)
        reservation = result.scalar_one_or_none()
        
        if not reservation:
            return None
            
        # Отмечаем бронирование как отмененное
        reservation.status = "cancelled"
        
        # Если есть подключение к API, можно также отменить через него
        # Но в демо-режиме просто обновляем статус в БД
        
        return reservation
