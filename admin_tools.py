#!/usr/bin/env python
# файл: admin_tools.py

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import update
from app.database import get_session
from app.models.user import User
import sys

load_dotenv()

async def add_tokens_to_admin():
    """
    Добавляет токены администратору для тестирования
    """
    admin_id = os.getenv("ADMIN_IDS", "").split(",")[0]
    
    if not admin_id:
        print("❌ ID администратора не найден в .env файле")
        return
    
    amount = 1000  # Количество токенов для добавления
    
    print(f"🔄 Добавление {amount} токенов администратору с Telegram ID: {admin_id}")
    
    async for session in get_session():
        try:
            # Поиск пользователя с указанным Telegram ID
            user = await session.execute(
                f"SELECT * FROM dating_bot.users WHERE telegram_id = '{admin_id}'"
            )
            user_row = user.fetchone()
            
            if not user_row:
                print(f"❌ Пользователь с Telegram ID {admin_id} не найден")
                print("Создаем пользователя...")
                
                # Создаем нового пользователя с правами администратора
                await session.execute(
                    f"INSERT INTO dating_bot.users (telegram_id, first_name, token_balance, is_admin) "
                    f"VALUES ('{admin_id}', 'Admin', {amount}, TRUE)"
                )
                await session.commit()
                print(f"✅ Создан новый пользователь-администратор с балансом {amount} токенов")
            else:
                # Обновляем баланс существующего пользователя
                user_id = user_row.id
                current_balance = user_row.token_balance or 0
                new_balance = current_balance + amount
                
                await session.execute(
                    f"UPDATE dating_bot.users SET token_balance = {new_balance}, is_admin = TRUE "
                    f"WHERE telegram_id = '{admin_id}'"
                )
                await session.commit()
                print(f"✅ Баланс администратора обновлен: {current_balance} → {new_balance} токенов")
                
            return True
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при добавлении токенов: {str(e)}")
            return False

async def view_admin_status():
    """
    Просмотр статуса администратора
    """
    admin_id = os.getenv("ADMIN_IDS", "").split(",")[0]
    
    if not admin_id:
        print("❌ ID администратора не найден в .env файле")
        return
    
    print(f"🔍 Проверка статуса администратора с Telegram ID: {admin_id}")
    
    async for session in get_session():
        try:
            # Поиск пользователя с указанным Telegram ID
            user = await session.execute(
                f"SELECT * FROM dating_bot.users WHERE telegram_id = '{admin_id}'"
            )
            user_row = user.fetchone()
            
            if not user_row:
                print(f"❌ Пользователь с Telegram ID {admin_id} не найден")
            else:
                # Выводим информацию о пользователе
                print("\n📊 Информация о пользователе:")
                print(f"ID: {user_row.id}")
                print(f"Telegram ID: {user_row.telegram_id}")
                print(f"Имя: {user_row.first_name}")
                print(f"Баланс токенов: {user_row.token_balance or 0}")
                print(f"Администратор: {'Да' if getattr(user_row, 'is_admin', False) else 'Нет'}")
                print(f"Язык: {user_row.language or 'не установлен'}")
                print(f"Премиум: {'Да' if user_row.is_premium else 'Нет'}")
                print(f"Верифицирован: {'Да' if user_row.is_verified else 'Нет'}")
                print("\n")
                
            return True
        except Exception as e:
            print(f"❌ Ошибка при получении информации: {str(e)}")
            return False

async def main():
    if len(sys.argv) < 2:
        print("Использование: python admin_tools.py [add_tokens|status]")
        return
    
    command = sys.argv[1]
    
    if command == "add_tokens":
        await add_tokens_to_admin()
    elif command == "status":
        await view_admin_status()
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Доступные команды: add_tokens, status")

if __name__ == "__main__":
    asyncio.run(main())
