# Admin Message Fix and Error-Proofing Guide

## ⚠️ CRITICAL: How to Prevent Bot Crashes ⚠️

The bot is still stopping on errors. To prevent this and make your bot resilient:

**NEVER run the bot directly with `python main.py`. Always use one of these auto-restart methods**:

### Option 1: For Windows users (easiest)
Simply double-click:
```
start_bot.bat
```

### Option 2: Using the simple auto-restart script
```
python run_bot.py
```

### Option 3: Using the advanced watchdog
```
python watchdog.py
```

All these methods will automatically restart the bot if it crashes, ensuring your bot stays online.

## LATEST FIX (July 4, 2025): Venue Selection Button Fix

We've fixed two important issues affecting the venue selection:

### 1. Fix for Place Type Buttons (Restaurant/Cafe/etc.)
- The `create_place_type_keyboard()` function was being called without required arguments
- Now it properly creates buttons for restaurant, cafe, bar, cinema, etc.
- Added detailed logging so you can see when buttons are created and what they contain

You can run the test yourself to verify:
```
.\venv\Scripts\python test_keyboard.py
```

### 2. Fix for Venue List Buttons (July 4, 2025 16:59)
- Fixed the "'dict' object has no attribute 'name'" error that occurred when showing venue lists
- The bug prevented venue names from being displayed after selecting a place type
- Updated the `create_place_keyboard()` function to properly handle both dictionary and model objects
- Added detailed logging to track venue data formatting

You can run this test to verify venue buttons are working:
```
.\venv\Scripts\python test_place_keyboard.py
```

These fixes together should resolve all issues with the venue selection flow.

## ⚠️ IMPORTANT: Use Virtual Environment ⚠️

Our auto-restart scripts have been updated to use the virtual environment (`venv`) where all dependencies are installed. 

The scripts now automatically check for and use:
1. `venv/Scripts/python.exe` on Windows
2. `venv/bin/python` on Linux/Mac
3. Fallback to system Python if no virtual environment is found

All three auto-restart methods now work correctly with the virtual environment.

## Problem Diagnosed
We identified several issues causing admin messages not to appear in the Telegram bot and causing the bot to crash:

1. **Multiple Handler Files**: There were several handler files (`handlers_fixed.py`, `new_handlers.py`, `patched_handler.py`) with similar functionality but different implementations.

2. **Handler Registration Confusion**: The project was using `patched_handler.py` via `__init__.py`, but other handler files were still present.

3. **Inadequate Error Handling**: Errors in handling admin messages would crash the entire bot process.

4. **Logging Issues**: Logging was not properly configured, causing Unicode encoding errors and missing logs.

## Solution Implemented

We've made the following changes to fix these issues:

1. **Unified Handler**: Created a unified handler file (`unified_handler.py`) that combines the best features of all previous handlers with extensive error handling.

2. **Error-Proof Code**: Added multiple layers of error catching to prevent the bot from crashing due to admin message or database issues.

3. **Improved Logging**: Configured proper logging with UTF-8 encoding support to capture all events.

4. **Fallback Mechanisms**: Implemented multiple fallback strategies for retrieving admin messages and displaying them.

5. **Backup of Old Code**: All old handler files have been renamed with `.bak` extensions to avoid confusion.

6. **Diagnostic Tools**: Created tools to help diagnose and monitor the bot's operation.

## How to Use the Improved Bot

1. **Start the Bot WITH AUTO-RESTART** (critical for preventing crashes):
   ```
   # Easiest method (Windows):
   start_bot.bat
   
   # OR using simple Python script:
   python run_bot.py
   
   # OR using advanced watchdog:
   python watchdog.py
   ```

2. **Monitor Operation** (optional, in a separate terminal):
   ```
   python diagnostic_monitor.py
   ```

3. **Test the Booking Flow** in Telegram:
   - Start a conversation with the bot
   - Use the `/booking` command
   - Enter a city name
   - Select a place type from the menu
   - Verify that admin messages appear correctly

## Key Improvements for Error Prevention

1. **Multiple Fallbacks**: The bot now has three different strategies for displaying admin messages:
   - Edit existing message (primary)
   - Send a new message (first fallback)
   - Send a simplified message (second fallback)

2. **Database Error Handling**: Errors in database queries are caught and handled gracefully.

3. **Safe State Management**: Even if state management fails, the bot continues to function.

4. **Robust Callback Handling**: Validation of callback data prevents crashes from malformed data.

5. **Defensive Keyboard Creation**: The keyboard builder has fallback options if data is missing.

## Troubleshooting Guide

If you encounter issues:

1. **STOP USING DIRECT EXECUTION**: If the bot is crashing, make sure you're using one of the auto-restart methods!
   ```
   # DO NOT RUN THESE - will crash on errors
   python main.py
   .\venv\Scripts\python main.py
   
   # INSTEAD USE ONE OF THESE - auto-restarts on errors
   start_bot.bat                    # Easiest for Windows users (uses venv automatically)
   .\venv\Scripts\python run_bot.py # Simple Python auto-restart with venv
   .\venv\Scripts\python watchdog.py # Advanced watchdog with venv
   ```

2. **Check Log Files**:
   - `unified_handler.log` for handler-related issues
   - `keyboards.log` for keyboard-related issues
   - `verification.log` for startup issues
   - `watchdog.log` for crash and restart information

2. **Run the Diagnostic Monitor**:
   ```
   python diagnostic_monitor.py
   ```
   This tool will show:
   - Current database state
   - Admin message testing results
   - Real-time log monitoring

3. **Verify Admin Messages in Database**:
   The bot now uses fallbacks, but it's best to have properly formatted admin messages:
   - Make sure your city names match exactly (though case-insensitive matching is supported)
   - Check that place types match the available options
   - Use the admin interface to add or edit messages

4. **If Bot Still Crashes**:
   - Check for other possible issues like network connectivity or Telegram API limits
   - Check if you have proper environment variables set
   - Review the main bot.py file for any initialization errors

## Enhanced Error Handling (July 2025 Update)

We've implemented a comprehensive error handling system to prevent the bot from crashing:

1. **Global Error Handler**: The bot now has an enhanced global error handler in `app/bot.py` that catches and logs all exceptions while allowing the bot to continue running.

2. **Resilient Main Loop**: The bot's main loop has been improved with multiple restart attempts and better error recovery strategies.

3. **Watchdog Script**: A new `watchdog.py` script provides an additional layer of protection by monitoring the bot and restarting it if it crashes completely.

### How to Use the Auto-Restart Tools

Instead of starting the bot directly, use one of these methods:

#### Option 1: For Windows users (easiest)
Simply double-click the batch file:
```
start_bot.bat
```

#### Option 2: Using the simple auto-restart script
```
python run_bot.py
```

#### Option 3: Using the advanced watchdog
```
python watchdog.py
```

All these methods will automatically restart the bot if it crashes. The watchdog will implement exponential backoff to avoid rapid restart cycles if there are too many crashes in a short period.

### Error Logs

Check these log files for error diagnostics:

- `bot.log` - Main bot logs
- `unified_handler.log` - Booking handler logs
- `watchdog.log` - Watchdog activity and crash reports

This enhanced error handling ensures that the bot continues to function even if unexpected errors occur, and provides detailed logging for troubleshooting.

## Adding New Admin Messages

To add a new admin message for a specific city and place type:

1. Use the admin interface in the bot
2. Or add directly to the database:
   ```sql
   INSERT INTO dating_bot.admin_messages (city, place_type, message)
   VALUES ('Moscow', 'restaurant', 'Your admin message here');
   ```

## Future Improvements

1. **Centralized Error Handling**: Consider implementing global error handlers for aiogram.

2. **Database Health Checks**: Add periodic database connection verification.

3. **User Feedback**: Implement clear user feedback when errors occur.

This solution ensures the bot remains operational even when errors occur with admin messages or database queries. The multiple fallback mechanisms make the system much more resilient.
