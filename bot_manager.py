#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility to check for running bot instances and manage them
"""

import os
import sys
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_manager.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("bot_manager")

def find_running_bots():
    """Find running Python processes that might be bot instances"""
    try:
        if os.name == 'nt':  # Windows
            # Use WMIC on Windows to get process details
            output = subprocess.check_output('wmic process where name="python.exe" get ProcessId,CommandLine', 
                                            shell=True).decode('utf-8', errors='ignore')
            lines = output.strip().split('\n')
            
            bot_processes = []
            for line in lines[1:]:  # Skip header row
                if 'main.py' in line or 'run_bot.py' in line or 'watchdog.py' in line:
                    parts = line.strip().split()
                    if parts:
                        # Last part should be the PID
                        try:
                            pid = int(parts[-1])
                            bot_processes.append({
                                'pid': pid,
                                'command': line.strip()
                            })
                        except ValueError:
                            pass
            
            return bot_processes
        else:  # Linux/Mac
            # Use ps on Unix-like systems
            output = subprocess.check_output(['ps', 'aux'], text=True)
            lines = output.strip().split('\n')
            
            bot_processes = []
            for line in lines:
                if ('python' in line or 'python3' in line) and ('main.py' in line or 'run_bot.py' in line or 'watchdog.py' in line):
                    parts = line.strip().split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            bot_processes.append({
                                'pid': pid,
                                'command': ' '.join(parts[10:]) if len(parts) > 10 else ''
                            })
                        except ValueError:
                            pass
            
            return bot_processes
    except Exception as e:
        logger.error(f"Error finding running bots: {e}")
        return []

def stop_bot_process(pid):
    """Stop a specific bot process by PID"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/F', '/PID', str(pid)])
        else:  # Linux/Mac
            subprocess.run(['kill', '-9', str(pid)])
        return True
    except Exception as e:
        logger.error(f"Error stopping bot process {pid}: {e}")
        return False

def main():
    print("\n=== Bot Instance Manager ===\n")
    
    # Find running bots
    bot_processes = find_running_bots()
    
    if not bot_processes:
        print("✅ No bot instances found running.")
        print("\nYou can safely start a new bot instance using:")
        print("  - start_bot.bat (easiest for Windows)")
        print("  - python run_bot.py")
        print("  - python watchdog.py")
        return
    
    print(f"Found {len(bot_processes)} bot instance(s) running:\n")
    
    for i, proc in enumerate(bot_processes):
        print(f"{i+1}. PID: {proc['pid']}")
        print(f"   Command: {proc['command']}\n")
    
    print("Options:")
    print("1. Stop all bot instances")
    print("2. Stop a specific bot instance")
    print("3. Exit without stopping any bots")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == '1':
        print("\nStopping all bot instances...")
        for proc in bot_processes:
            if stop_bot_process(proc['pid']):
                print(f"✅ Stopped bot with PID {proc['pid']}")
            else:
                print(f"❌ Failed to stop bot with PID {proc['pid']}")
        
        print("\nWaiting 5 seconds for Telegram servers to update connection status...")
        time.sleep(5)
        print("\n✅ You can now start a new bot instance.")
    
    elif choice == '2':
        idx = input(f"\nEnter the number of the bot to stop (1-{len(bot_processes)}): ")
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(bot_processes):
                pid = bot_processes[idx]['pid']
                if stop_bot_process(pid):
                    print(f"\n✅ Stopped bot with PID {pid}")
                    print("\nWaiting 5 seconds for Telegram servers to update connection status...")
                    time.sleep(5)
                    print("\n✅ You can now start a new bot instance.")
                else:
                    print(f"\n❌ Failed to stop bot with PID {pid}")
            else:
                print("\n❌ Invalid selection.")
        except ValueError:
            print("\n❌ Please enter a valid number.")
    
    elif choice == '3':
        print("\n⚠️ Exiting without stopping any bots.")
    
    else:
        print("\n❌ Invalid choice.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        print(f"\n❌ An error occurred: {e}")
    
    input("\nPress Enter to exit...")
