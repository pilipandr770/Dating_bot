@echo off
echo Bot Manager - Checking for running instances...

:: Check for Python virtual environment first
if exist venv\Scripts\python.exe (
    venv\Scripts\python bot_manager.py
) else (
    :: Fallback to system Python
    python bot_manager.py
)
