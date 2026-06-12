"""
CheckPoint — Universal PC Game Save Backup & Restore Manager.

Entry point for the application.
"""

import sys
from app.utils.logger import setup_logging, get_logger
from app.database.schema import initialize_database
from app.ui.main_window import MainWindow

def main():
    # 1. Setup Logging
    setup_logging(level="INFO")
    logger = get_logger("main")
    logger.info("CheckPoint starting up...")

    # 2. Initialize Database
    try:
        initialize_database()
        logger.info("Database initialized.")
    except Exception as e:
        logger.critical("Failed to initialize database: %s", e)
        sys.exit(1)

    # 3. Launch UI
    try:
        app = MainWindow()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        logger.info("Main window launched.")
        app.mainloop()
    except Exception as e:
        logger.critical("Application crashed: %s", e)
        raise e

if __name__ == "__main__":
    main()
