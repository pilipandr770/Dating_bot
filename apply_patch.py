import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("apply_patch.log"), logging.StreamHandler()]
)
logger = logging.getLogger("apply_patch")

def update_init_file():
    """Update __init__.py to use the patched handler"""
    init_path = "app/booking/__init__.py"
    
    if not os.path.exists(init_path):
        logger.error(f"Cannot find {init_path}")
        return False
    
    # Read current content
    with open(init_path, 'r', encoding='utf-8') as file:
        content = file.read()
        logger.info(f"Current content of {init_path}:\n{content}")
    
    # Create backup
    backup_path = f"{init_path}.bak"
    with open(backup_path, 'w', encoding='utf-8') as file:
        file.write(content)
        logger.info(f"Created backup at {backup_path}")
    
    # Replace imports
    new_content = content
    imports_to_replace = [
        "from app.booking.handlers import register_booking_handlers", 
        "from app.booking.new_handlers import register_booking_handlers",
        "from app.booking.handlers_fixed import register_booking_handlers"
    ]
    
    for import_line in imports_to_replace:
        if import_line in new_content:
            new_content = new_content.replace(
                import_line, 
                "from app.booking.patched_handler import register_booking_handlers"
            )
            logger.info(f"Replaced {import_line} with patched version")
    
    # Write updated content
    with open(init_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
        logger.info(f"Updated {init_path} to use patched_handler")
    
    return True

def verify_update():
    """Verify that the update was successful"""
    init_path = "app/booking/__init__.py"
    
    if not os.path.exists(init_path):
        logger.error(f"Cannot find {init_path}")
        return False
    
    # Read content
    with open(init_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if "from app.booking.patched_handler import register_booking_handlers" in content:
        logger.info("Verification successful: patched_handler is being imported")
        return True
    else:
        logger.error("Verification failed: patched_handler is not being imported")
        logger.info(f"Current content of {init_path}:\n{content}")
        return False

if __name__ == "__main__":
    logger.info("Starting patch application")
    
    if update_init_file():
        logger.info("Patch application completed")
        
        if verify_update():
            logger.info("Patch verification successful")
            sys.exit(0)
        else:
            logger.error("Patch verification failed")
            sys.exit(1)
    else:
        logger.error("Patch application failed")
        sys.exit(1)
