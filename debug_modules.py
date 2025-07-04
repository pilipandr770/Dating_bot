import sys
import os
import inspect
import importlib

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("==== ПРОВЕРКА МОДУЛЕЙ PYTHON ====")
print(f"Python версия: {sys.version}")
print(f"Текущая директория: {os.getcwd()}")
print(f"sys.path: {sys.path}")

try:
    print("\n==== ИМПОРТ МОДУЛЯ app.booking ====")
    import app.booking
    print(f"Путь к модулю app.booking: {app.booking.__file__}")
    print(f"Содержимое app.booking.__all__: {app.booking.__all__}")
    
    print("\n==== ИМПОРТ ФУНКЦИИ register_booking_handlers ====")
    from app.booking import register_booking_handlers
    print(f"Источник функции register_booking_handlers: {inspect.getmodule(register_booking_handlers).__file__}")

    print("\n==== ИМПОРТ МОДУЛЯ app.booking.handlers_fixed ====")
    import app.booking.handlers_fixed
    print(f"Путь к модулю app.booking.handlers_fixed: {app.booking.handlers_fixed.__file__}")
    
    # Проверяем, существует ли модуль handlers
    try:
        print("\n==== ПРОВЕРКА НАЛИЧИЯ app.booking.handlers ====")
        import app.booking.handlers
        print(f"Путь к модулю app.booking.handlers: {app.booking.handlers.__file__}")
        print("ВНИМАНИЕ: Модуль app.booking.handlers существует!")
        
        # Проверяем функцию process_place_type в handlers_fixed и handlers
        print("\n==== СРАВНЕНИЕ ФУНКЦИЙ process_place_type ====")
        if hasattr(app.booking.handlers_fixed, "process_place_type") and hasattr(app.booking.handlers, "process_place_type"):
            fixed_func = app.booking.handlers_fixed.process_place_type
            handlers_func = app.booking.handlers.process_place_type
            print(f"process_place_type из handlers_fixed: {fixed_func}")
            print(f"process_place_type из handlers: {handlers_func}")
            print(f"Одинаковые функции: {fixed_func is handlers_func}")
        else:
            print("Функция process_place_type отсутствует в одном из модулей")
    except ImportError:
        print("Модуль app.booking.handlers не найден (это хорошо)")
    
    print("\n==== ПРОВЕРКА РЕГИСТРАЦИИ ОБРАБОТЧИКОВ ====")
    from aiogram import Dispatcher
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    
    # Создаем тестовый диспетчер
    test_dp = Dispatcher(None, storage=MemoryStorage())
    
    # Регистрируем обработчики
    register_booking_handlers(test_dp)
    
    # Анализируем зарегистрированные обработчики
    print("\nЗарегистрированные callback query handlers:")
    for handler in test_dp.callback_query_handlers.handlers:
        filters = [f"{f.__class__.__name__}" for f in handler.filters]
        print(f"Handler: {handler.handler}, Filters: {filters}")

except Exception as e:
    print(f"Ошибка при импорте/анализе модулей: {e}")

print("\n==== ПРОВЕРКА ЗАВЕРШЕНА ====")
