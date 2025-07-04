"""
Telegram Bot Watchdog Script

This script monitors the bot and restarts it if it crashes.
Run this script instead of app/bot.py directly for additional crash protection.
"""

import subprocess
import time
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - WATCHDOG - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("watchdog.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("watchdog")

def get_python_executable():
    """Get the path to the Python executable, preferring virtualenv if available"""
    # Check for virtual environment first
    if os.path.exists('venv/Scripts/python.exe'):
        return os.path.abspath('venv/Scripts/python.exe')
    elif os.path.exists('venv/bin/python'):
        return os.path.abspath('venv/bin/python')
    # Fallback to system Python
    else:
        return sys.executable

def run_bot():
    """Run the bot as a subprocess and restart it if it crashes"""
    
    max_crashes = 10
    crash_count = 0
    cooldown_period = 60  # seconds to wait after multiple crashes
    
    # Store crash times to implement exponential backoff
    crash_times = []
    
    # Get the correct Python executable (from virtualenv if available)
    python_exe = get_python_executable()
    logger.info(f"Using Python executable: {python_exe}")
    
    logger.info("==== WATCHDOG STARTED ====")
    
    while crash_count < max_crashes:
        # Calculate wait time based on recent crashes (exponential backoff)
        now = time.time()
        # Remove crash times older than 1 hour
        crash_times = [t for t in crash_times if now - t < 3600]
        
        # Wait longer if we've had multiple crashes recently
        if len(crash_times) >= 3:
            wait_time = cooldown_period * (2 ** (len(crash_times) - 3))
            wait_time = min(wait_time, 900)  # Cap at 15 minutes
            logger.warning(f"Multiple crashes detected. Waiting {wait_time} seconds before restart")
            time.sleep(wait_time)
        
        start_time = time.time()
        logger.info(f"Starting bot process (attempt {crash_count + 1}/{max_crashes})")
        
        try:
            # Start the bot process using main.py with the correct Python executable
            process = subprocess.Popen([python_exe, "main.py"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      universal_newlines=True,
                                      bufsize=1)
            
            # Log process start
            logger.info(f"Bot process started with PID {process.pid}")
            
            # Forward output in real-time and capture for logging
            stdout_lines = []
            stderr_lines = []
            
            while process.poll() is None:
                # Read stdout
                if process.stdout:
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        print(stdout_line.rstrip())
                        stdout_lines.append(stdout_line)
                
                # Read stderr
                if process.stderr:
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        print(f"ERROR: {stderr_line.rstrip()}", file=sys.stderr)
                        stderr_lines.append(stderr_line)
                
                # Short sleep to prevent CPU overuse
                if not stdout_line and not stderr_line:
                    time.sleep(0.1)
            
            # Process is complete
            exit_code = process.returncode
            
            # Get any remaining output
            if process.stdout:
                remaining_stdout = process.stdout.read()
                if remaining_stdout:
                    stdout_lines.append(remaining_stdout)
                    print(remaining_stdout.rstrip())
            
            if process.stderr:
                remaining_stderr = process.stderr.read()
                if remaining_stderr:
                    stderr_lines.append(remaining_stderr)
                    print(f"ERROR: {remaining_stderr.rstrip()}", file=sys.stderr)
            
            # Combine captured output
            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines)
            
            # If the process exited, check if it was a crash
            runtime = time.time() - start_time
            if exit_code != 0:
                logger.error(f"Bot crashed with exit code {exit_code}")
                logger.error(f"STDERR: {stderr}")
                crash_count += 1
                crash_times.append(time.time())
                
                # If it ran for less than 10 seconds, it's probably a startup crash
                if runtime < 10:
                    logger.critical("Bot crashed immediately after startup!")
                    # Wait longer before retrying for immediate crashes
                    time.sleep(30)
            else:
                # Normal exit
                logger.info("Bot process exited normally")
                break
                
        except KeyboardInterrupt:
            logger.info("Watchdog terminated by user")
            try:
                process.terminate()
                logger.info("Bot process terminated")
            except:
                pass
            break
            
        except Exception as e:
            logger.error(f"Error in watchdog: {e}")
            crash_count += 1
            time.sleep(5)
    
    if crash_count >= max_crashes:
        logger.critical(f"Bot crashed {max_crashes} times. Watchdog giving up.")
    
    logger.info("==== WATCHDOG STOPPED ====")

if __name__ == "__main__":
    try:
        # Create a timestamp file to record when the watchdog was last started
        with open("watchdog_started.txt", "w") as f:
            f.write(f"Watchdog started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        run_bot()
    except KeyboardInterrupt:
        logger.info("Watchdog stopped by user")
    except Exception as e:
        logger.critical(f"Fatal watchdog error: {e}")
