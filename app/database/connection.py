"""
CheckPoint — Database connection management.

Provides a thread-safe SQLite connection pool using WAL mode
for concurrent read/write access.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from app.utils.paths import get_data_dir
from app.utils.logger import get_logger

logger = get_logger("database.connection")

_DB_FILENAME = "checkpoint.db"


class DatabaseConnection:
    """
    Thread-safe SQLite database connection manager.

    Uses WAL journal mode for concurrent access and provides
    context-manager support for automatic connection handling.
    """

    _instance: Optional["DatabaseConnection"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "DatabaseConnection":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the database connection."""
        if self._initialized:
            return
        self._db_path: Path = get_data_dir() / _DB_FILENAME
        self._local = threading.local()
        self._initialized = True
        logger.info("Database path: %s", self._db_path)

    @property
    def path(self) -> Path:
        """Return the database file path."""
        return self._db_path

    def get_connection(self) -> sqlite3.Connection:
        """
        Get a thread-local SQLite connection.

        Returns:
            An sqlite3.Connection configured with WAL mode and row factory.
        """
        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(str(self._db_path), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row
            self._local.connection = conn
            logger.debug("Created new thread-local connection for thread %s",
                         threading.current_thread().name)
        return self._local.connection

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query and return the cursor.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            sqlite3.Cursor with results.
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("SQL execution error: %s — Query: %s", e, query[:200])
            raise

    def executemany(self, query: str, params_list: list[tuple]) -> sqlite3.Cursor:
        """
        Execute a SQL query with multiple parameter sets.

        Args:
            query: SQL query string.
            params_list: List of parameter tuples.

        Returns:
            sqlite3.Cursor with results.
        """
        conn = self.get_connection()
        try:
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("SQL executemany error: %s", e)
            raise

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a query and fetch a single row."""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute a query and fetch all rows."""
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def close(self) -> None:
        """Close the thread-local connection if it exists."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug("Closed thread-local connection")

    def close_all(self) -> None:
        """Close the connection and reset the singleton (for shutdown)."""
        self.close()
        DatabaseConnection._instance = None
        logger.info("Database connection manager shut down")
