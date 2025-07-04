# app/booking/services_db.py

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.booking.models import Place, PlaceType, AdminMessage

# Настройка логирования
logger = logging.getLogger(__name__)

class VenueService:
    """Сервис для работы с заведениями в базе данных"""

    @staticmethod
    async def get_venues_by_type_and_city(
        session: AsyncSession, 
        place_type: str, 
        city: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получает список заведений определенного типа в указанном городе.
        Если город не указан, возвращает все заведения указанного типа.
        """
        try:
            # Создаем базовый запрос с явным приведением типа к строке для надежности
            logger.info(f"Запрос заведений типа '{place_type}' - поиск по точному совпадению")
            
            # Используем текстовый SQL для более точного контроля над запросом
            query = text("""
                SELECT * FROM dating_bot.places 
                WHERE type = :place_type
            """).bindparams(place_type=place_type)
            
            if city:
                query = text("""
                    SELECT * FROM dating_bot.places 
                    WHERE type = :place_type
                    AND city ILIKE :city_pattern
                """).bindparams(place_type=place_type, city_pattern=f"%{city}%")
            
            # Выполняем запрос
            result = await session.execute(query)
            rows = result.fetchall()
            logger.info(f"SQL запрос вернул {len(rows)} строк")
            
            # Преобразуем результаты в список словарей
            venues = []
            for row in rows:
                venue_dict = {
                    "id": row.id,
                    "name": row.name,
                    "url": row.link or "#",  # Используем поле link вместо url
                    "city": row.city
                }
                
                # Добавляем координаты, если они есть
                if row.latitude and row.longitude:
                    venue_dict["coordinates"] = (row.latitude, row.longitude)
                
                # У нас нет image_url в БД, но можно добавить статическое фото, если нужно
                venue_dict["photo_url"] = None
                
                # Пытаемся найти админское сообщение для этого города и типа заведения в БД
                try:
                    # Получаем админское сообщение из базы данных с использованием SQLAlchemy
                    from app.booking.services_admin_message import AdminMessageService
                    logger.info(f"[DEBUG] Запрос админского сообщения для заведения '{row.name}', город '{row.city}', тип '{place_type}'")
                    
                    # Выводим типы параметров для отладки
                    logger.info(f"[DEBUG] Типы параметров: city={type(row.city).__name__}, place_type={type(place_type).__name__}")
                    
                    # Проверяем наличие значения row.city
                    city_value = row.city if row.city else "Unknown"
                    
                    admin_message = await AdminMessageService.get_admin_message(
                        session=session,
                        city=city_value,
                        place_type=place_type
                    )
                    
                    if admin_message:
                        logger.info(f"Найдено админское сообщение для '{row.name}': {admin_message}")
                        venue_dict["admin_message"] = admin_message
                    else:
                        logger.info(f"Админское сообщение для '{row.name}' не найдено, проверяем тестовые данные")
                        # Если в БД нет сообщения, ищем в тестовых данных как запасной вариант
                        from app.booking.handlers_fixed import default_venues
                        for test_venue in default_venues.get(place_type, []):
                            if test_venue["name"] == row.name:
                                venue_dict["admin_message"] = test_venue.get("admin_message", "")
                                logger.info(f"Найдено тестовое сообщение для '{row.name}': {venue_dict['admin_message']}")
                except (ImportError, AttributeError, Exception) as e:
                    logger.error(f"Ошибка при получении админского сообщения для '{row.name}': {e}")
                    pass
                
                venues.append(venue_dict)
            
            logger.info(f"Найдено {len(venues)} заведений типа {place_type} в городе {city or 'любом'}")
            return venues
            
        except Exception as e:
            logger.error(f"Ошибка при получении заведений из БД: {e}")
            return []
    
    @staticmethod
    async def add_venue(
        session: AsyncSession,
        name: str,
        place_type: str,
        city: str,
        url: str = None,
        description: str = None,  # Не сохраняется в БД, но используется в логике
        admin_message: str = None,  # Не сохраняется в БД, но используется в логике
        coordinates: Optional[Tuple[float, float]] = None  # Широта и долгота
    ) -> Optional[Place]:
        """
        Добавляет новое заведение в базу данных.
        Возвращает созданный объект Place или None в случае ошибки.
        """
        try:
            # Создаем новое заведение только с полями, которые существуют в БД
            new_place = Place(
                name=name,
                type=place_type,
                city=city
            )
            
            # Добавляем URL как link (поле в БД)
            if url:
                new_place.link = url
                
            # Добавляем координаты, если они указаны
            if coordinates and len(coordinates) == 2:
                latitude, longitude = coordinates
                new_place.latitude = latitude
                new_place.longitude = longitude
            
            # По умолчанию это не партнерское заведение
            new_place.is_partner = False
            
            # Логируем дополнительную информацию, которая не хранится в БД
            if description:
                logger.info(f"Описание для {name}: {description} (не сохраняется в БД)")
            
            # Если предоставлено админское сообщение, сохраняем его в базе данных
            if admin_message:
                try:
                    from app.booking.services_admin_message import AdminMessageService
                    await AdminMessageService.add_admin_message(
                        session=session,
                        city=city,
                        place_type=place_type,
                        message=admin_message
                    )
                    logger.info(f"Сохранено админское сообщение для города {city}, тип {place_type}: {admin_message}")
                except Exception as e:
                    logger.error(f"Ошибка при сохранении админского сообщения: {e}")
            
            # Добавляем в сессию и коммитим изменения
            session.add(new_place)
            await session.commit()
            await session.refresh(new_place)
            
            logger.info(f"Добавлено новое заведение: {name} (тип: {place_type}, город: {city})")
            return new_place
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении заведения: {e}")
            return None
    
    @staticmethod
    async def update_venue(
        session: AsyncSession,
        place_id: int,
        **kwargs
    ) -> Optional[Place]:
        """
        Обновляет информацию о заведении.
        Принимает ID заведения и именованные аргументы с полями для обновления.
        
        Поддерживаемые аргументы:
        - name: название заведения
        - type: тип заведения (строка)
        - city: город
        - url/link: ссылка на заведение (будет сохранена как link)
        - latitude, longitude: координаты
        - is_partner: является ли партнером (булево)
        """
        try:
            # Находим заведение по ID
            query = select(Place).where(Place.id == place_id)
            result = await session.execute(query)
            place = result.scalar_one_or_none()
            
            if not place:
                logger.warning(f"Заведение с ID {place_id} не найдено")
                return None
            
            # Специальная обработка для url (сохраняем как link)
            if 'url' in kwargs:
                kwargs['link'] = kwargs.pop('url')
                
            # Обработка координат как кортежа
            if 'coordinates' in kwargs and kwargs['coordinates']:
                try:
                    latitude, longitude = kwargs.pop('coordinates')
                    kwargs['latitude'] = latitude
                    kwargs['longitude'] = longitude
                except (ValueError, TypeError):
                    logger.warning(f"Некорректный формат координат: {kwargs['coordinates']}")
            
            # Обновляем поля
            for key, value in kwargs.items():
                if hasattr(place, key):
                    setattr(place, key, value)
            
            # Сохраняем изменения
            await session.commit()
            await session.refresh(place)
            
            logger.info(f"Обновлено заведение с ID {place_id}")
            return place
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при обновлении заведения: {e}")
            return None
            
    @staticmethod
    async def get_venue_by_id(
        session: AsyncSession, 
        place_id: int
    ) -> Optional[Place]:
        """Получает заведение по ID"""
        try:
            query = select(Place).where(Place.id == place_id)
            result = await session.execute(query)
            place = result.scalar_one_or_none()
            return place
        except Exception as e:
            logger.error(f"Ошибка при получении заведения по ID {place_id}: {e}")
            return None
            
    @staticmethod
    async def delete_venue(
        session: AsyncSession, 
        place_id: int
    ) -> bool:
        """
        Удаляет заведение из базы данных.
        Возвращает True в случае успеха, False в случае ошибки.
        """
        try:
            place = await VenueService.get_venue_by_id(session, place_id)
            if not place:
                return False
            
            await session.delete(place)
            await session.commit()
            
            logger.info(f"Удалено заведение с ID {place_id}")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при удалении заведения: {e}")
            return False
    
    @staticmethod
    async def debug_db_schema(session: AsyncSession, table_name: str = "dating_bot.places") -> None:
        """
        Выводит в лог информацию о структуре таблицы для отладки.
        """
        try:
            # Извлекаем схему и имя таблицы
            schema = table_name.split('.')[0] if '.' in table_name else 'public'
            table = table_name.split('.')[-1]
            
            # Запрос для получения информации о колонках таблицы, используя text()
            query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = :table_name
            AND table_schema = :schema_name
            """).bindparams(table_name=table, schema_name=schema)
            
            # Выполняем запрос
            result = await session.execute(query)
            columns = result.all()
            
            logger.info(f"==== СТРУКТУРА ТАБЛИЦЫ {table_name} ====")
            for column in columns:
                logger.info(f"Колонка: {column[0]}, Тип: {column[1]}")
            logger.info("====================================")
            
        except Exception as e:
            logger.error(f"Ошибка при получении структуры таблицы {table_name}: {e}")
    
    @staticmethod
    async def get_admin_messages(session: AsyncSession) -> List[Dict[str, Any]]:
        """
        Получает список всех админских сообщений через AdminMessageService.
        Этот метод-обертка упрощает доступ к админским сообщениям из VenueService.
        """
        try:
            from app.booking.services_admin_message import AdminMessageService
            return await AdminMessageService.list_admin_messages(session)
        except Exception as e:
            logger.error(f"Ошибка при получении списка админских сообщений: {e}")
            return []
