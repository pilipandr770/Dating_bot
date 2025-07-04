import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from app.database import get_session
from sqlalchemy import text

async def check_db():
    print('Checking database connection...')
    async for session in get_session():
        # Check if the admin_messages table exists
        result = await session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'dating_bot'
                AND table_name = 'admin_messages'
            );
        """))
        table_exists = result.scalar()
        print(f'admin_messages table exists: {table_exists}')
        
        # If table exists, check if it has any data
        if table_exists:
            result = await session.execute(text("""
                SELECT COUNT(*) FROM dating_bot.admin_messages;
            """))
            count = result.scalar()
            print(f'Number of admin messages in database: {count}')
            
            # Get all messages for debugging
            if count > 0:
                result = await session.execute(text("""
                    SELECT id, city, place_type, message FROM dating_bot.admin_messages;
                """))
                messages = result.fetchall()
                print('Admin messages in database:')
                for msg in messages:
                    print(f'ID: {msg[0]}, City: {msg[1]}, Type: {msg[2]}, Message: {msg[3][:30]}...')
                    
        # Check the structure of the admin_messages table
        result = await session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns
            WHERE table_schema = 'dating_bot'
            AND table_name = 'admin_messages'
            ORDER BY ordinal_position;
        """))
        columns = result.fetchall()
        print('Structure of admin_messages table:')
        for col in columns:
            print(f'Column: {col[0]}, Type: {col[1]}')

        # Now let's try to add a test admin message
        try:
            print("\nAttempting to add a test admin message...")
            from app.booking.services_admin_message import AdminMessageService
            
            test_message = await AdminMessageService.add_admin_message(
                session=session,
                city="Франкфурт",
                place_type="restaurant",
                message="Тестове повідомлення для ресторанів у Франкфурті. Знижка 15% з промокодом SOUL_LINK."
            )
            
            if test_message:
                print(f"Successfully added test message with ID: {test_message.id}")
            
            # Add another one for a different place type
            test_message2 = await AdminMessageService.add_admin_message(
                session=session,
                city="Франкфурт",
                place_type="park",
                message="Тестове повідомлення для парків у Франкфурті. Спеціальні події щовихідних!"
            )
            
            if test_message2:
                print(f"Successfully added second test message with ID: {test_message2.id}")
                
            # Verify they were added
            result = await session.execute(text("""
                SELECT id, city, place_type, message FROM dating_bot.admin_messages
                WHERE city = 'Франкфурт';
            """))
            messages = result.fetchall()
            print('\nVerifying new test messages:')
            for msg in messages:
                print(f'ID: {msg[0]}, City: {msg[1]}, Type: {msg[2]}, Message: {msg[3][:30]}...')
                
        except Exception as e:
            print(f"Error adding test message: {e}")

        # Let's also test getting an admin message for a specific city and place type
        try:
            print("\nTesting admin message retrieval...")
            from app.booking.services_admin_message import AdminMessageService
            
            message = await AdminMessageService.get_admin_message(
                session=session,
                city="Франкфурт",
                place_type="restaurant"
            )
            
            if message:
                print(f"Successfully retrieved message for 'Франкфурт'/'restaurant': {message[:30]}...")
            else:
                print("No message found for 'Франкфурт'/'restaurant'")
                
            message2 = await AdminMessageService.get_admin_message(
                session=session,
                city="Франкфурт",
                place_type="park"
            )
            
            if message2:
                print(f"Successfully retrieved message for 'Франкфурт'/'park': {message2[:30]}...")
            else:
                print("No message found for 'Франкфурт'/'park'")
                
        except Exception as e:
            print(f"Error retrieving admin message: {e}")

asyncio.run(check_db())
