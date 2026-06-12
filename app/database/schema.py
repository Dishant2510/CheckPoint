"""
CheckPoint — Database schema definition and migration.

Creates all required tables and handles schema versioning
for future migrations.
"""

from app.database.connection import DatabaseConnection
from app.utils.logger import get_logger

logger = get_logger("database.schema")

SCHEMA_VERSION = 1

TABLES_SQL = [
    # --- Games table ---
    """
    CREATE TABLE IF NOT EXISTS games (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        install_path TEXT   DEFAULT '',
        save_path   TEXT    DEFAULT '',
        exe_path    TEXT   DEFAULT '',
        launcher_type TEXT DEFAULT 'unknown',
        icon_path   TEXT   DEFAULT '',
        added_date  TEXT   NOT NULL DEFAULT (datetime('now', 'localtime')),
        last_played TEXT   DEFAULT '',
        last_backed_up TEXT DEFAULT '',
        notes       TEXT   DEFAULT '',
        is_active   INTEGER DEFAULT 1
    )
    """,

    # --- Backups table ---
    """
    CREATE TABLE IF NOT EXISTS backups (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id     INTEGER NOT NULL,
        backup_path TEXT    NOT NULL,
        backup_name TEXT    NOT NULL,
        size_bytes  INTEGER DEFAULT 0,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        backup_type TEXT    DEFAULT 'manual',
        checksum    TEXT    DEFAULT '',
        is_auto     INTEGER DEFAULT 0,
        notes       TEXT    DEFAULT '',
        FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
    )
    """,

    # --- Settings table ---
    """
    CREATE TABLE IF NOT EXISTS settings (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        key         TEXT    NOT NULL UNIQUE,
        value       TEXT    DEFAULT '',
        updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    )
    """,

    # --- Logs table ---
    """
    CREATE TABLE IF NOT EXISTS logs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        level       TEXT    NOT NULL DEFAULT 'INFO',
        source      TEXT    DEFAULT '',
        message     TEXT    NOT NULL
    )
    """,

    # --- Schema version tracking ---
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version     INTEGER NOT NULL,
        applied_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    )
    """,
]

INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_backups_game_id ON backups(game_id)",
    "CREATE INDEX IF NOT EXISTS idx_backups_created_at ON backups(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)",
    "CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)",
    "CREATE INDEX IF NOT EXISTS idx_games_name ON games(name)",
]


def initialize_database() -> None:
    """
    Create all tables and indexes if they don't exist.

    Safe to call multiple times — uses IF NOT EXISTS guards.
    """
    db = DatabaseConnection()

    logger.info("Initializing database schema (version %d)...", SCHEMA_VERSION)

    # Create tables
    for sql in TABLES_SQL:
        db.execute(sql)

    # Create indexes
    for sql in INDEXES_SQL:
        db.execute(sql)

    # Track schema version
    existing = db.fetchone("SELECT MAX(version) as v FROM schema_version")
    current_version = existing["v"] if existing and existing["v"] else 0

    if current_version < SCHEMA_VERSION:
        db.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,)
        )
        logger.info("Schema version set to %d", SCHEMA_VERSION)

    logger.info("Database schema initialized successfully")


def reset_database() -> None:
    """
    Drop all tables and recreate them.

    WARNING: This destroys all data. Use only for development/testing.
    """
    db = DatabaseConnection()
    tables = ["logs", "backups", "games", "settings", "schema_version"]
    for table in tables:
        db.execute(f"DROP TABLE IF EXISTS {table}")
    logger.warning("All tables dropped — reinitializing...")
    initialize_database()
