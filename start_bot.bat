@echo off
echo Starting Soul Link Bot with auto-restart...
echo.
echo This window will stay open and restart the bot automatically if it crashes.
echo Do not close this window if you want the bot to keep running.
echo.
echo Press Ctrl+C twice to stop the bot.
echo.
echo Starting bot...

:: Check if venv exists and use it
IF EXIST "venv\Scripts\python.exe" (
    echo Using virtual environment Python...
    venv\Scripts\python.exe run_bot.py
) ELSE (
    echo Using system Python...
    python run_bot.py
)

echo.
echo Bot has stopped running. Press any key to exit.
pause > nul
