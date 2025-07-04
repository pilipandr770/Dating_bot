"""
Install dependencies needed for the diagnostic tools
"""

import subprocess
import sys
import os

def install_dependencies():
    print("Installing dependencies for diagnostic tools...")
    
    # List of required packages
    dependencies = [
        "watchdog",  # For file monitoring
        "aiogram",   # For telegram bot functionality
        "sqlalchemy" # For database operations
    ]
    
    # Try to install dependencies
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")
            
    print("\nDependencies installation completed.")
    print("You can now run the diagnostic monitor with: python diagnostic_monitor.py")

if __name__ == "__main__":
    install_dependencies()
