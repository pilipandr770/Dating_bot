# файл: main.py
# Основний файл для запуску бота з кореневого каталогу проекту

import asyncio
import sys
import os

# Додаємо поточний каталог до шляху, щоб імпорт працював правильно
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Імпортуємо функцію main з модуля app.bot
from app.bot import main

if __name__ == '__main__':
    print("🤖 Запускаємо бота...")
    asyncio.run(main())
