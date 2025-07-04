"""
This script renames the old handler files to .bak 
to avoid confusion and ensure only the unified_handler.py is used.
"""

import os
import shutil
import sys

def backup_file(path):
    """Backup a file by renaming it to .bak"""
    if os.path.exists(path):
        backup_path = f"{path}.bak"
        
        # Remove existing backup if it exists
        if os.path.exists(backup_path):
            os.remove(backup_path)
            
        # Rename file to .bak
        shutil.move(path, backup_path)
        print(f"Backed up {path} to {backup_path}")
    else:
        print(f"File {path} does not exist, skipping")

def main():
    # Set the booking directory path
    booking_dir = os.path.join("app", "booking")
    
    # Files to backup
    files_to_backup = [
        "handlers_fixed.py",
        "handlers.py",
        "new_handlers.py",
        "patched_handler.py"
    ]
    
    # Backup each file
    for file_name in files_to_backup:
        file_path = os.path.join(booking_dir, file_name)
        backup_file(file_path)
    
    print("\nBackup completed. Only unified_handler.py should be used now.")
    print("Remember to restart the bot for changes to take effect.")

if __name__ == "__main__":
    main()
