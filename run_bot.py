# -*- coding: utf-8 -*-
"""
Simplified bot runner with auto-restart - with virtual environment support
"""

import subprocess
import sys
import time
import os

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

def run_bot_with_restarts():
    """Run the bot and automatically restart it if it crashes"""
    print("🤖 Starting bot with auto-restart protection...")
    
    # Get the correct Python executable (from virtualenv if available)
    python_exe = get_python_executable()
    print(f"Using Python executable: {python_exe}")
    
    restart_count = 0
    max_restarts = 100  # Practically unlimited restarts
    
    while restart_count < max_restarts:
        print(f"\n🔄 Running bot (restart #{restart_count})...")
        
        # Start the bot process
        try:
            # Run the process and forward all output
            result = subprocess.run([python_exe, "main.py"], 
                                  check=False)
            
            # Check exit code
            if result.returncode == 0:
                print("✅ Bot exited normally")
                break
            else:
                restart_count += 1
                print(f"❌ Bot crashed with exit code {result.returncode}")
                print(f"🕒 Waiting 5 seconds before restart...")
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n⚠️ Bot stopped by user")
            break
        except Exception as e:
            restart_count += 1
            print(f"❌ Error running bot: {e}")
            print(f"🕒 Waiting 5 seconds before restart...")
            time.sleep(5)
    
    print("👋 Bot runner finished")

if __name__ == "__main__":
    run_bot_with_restarts()
