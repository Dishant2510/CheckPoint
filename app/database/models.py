"""
CheckPoint — Data models and repository.

Dataclass models for Game, Backup, Setting, and LogEntry.
Repository classes for CRUD operations against SQLite.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from app.database.connection import DatabaseConnection
from app.utils.logger import get_logger

logger = get_logger("database.models")


# ──────────────────────────────────────────────────────────
#  Data Models
# ──────────────────────────────────────────────────────────

@dataclass
class Game:
    """Represents a registered game."""
    id: Optional[int] = None
    name: str = ""
    install_path: str = ""
    save_path: str = ""
    exe_path: str = ""
    launcher_type: str = "unknown"
    icon_path: str = ""
    added_date: str = ""
    last_played: str = ""
    last_backed_up: str = ""
    notes: str = ""
    is_active: int = 1

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Game:
        """Create a Game instance from a database row."""
        return cls(**{k: row[k] for k in row.keys()})


@dataclass
class Backup:
    """Represents a save backup record."""
    id: Optional[int] = None
    game_id: int = 0
    backup_path: str = ""
    backup_name: str = ""
    size_bytes: int = 0
    created_at: str = ""
    backup_type: str = "manual"
    checksum: str = ""
    is_auto: int = 0
    notes: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Backup:
        """Create a Backup instance from a database row."""
        return cls(**{k: row[k] for k in row.keys()})


@dataclass
class Setting:
    """Represents a settings key-value pair."""
    id: Optional[int] = None
    key: str = ""
    value: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Setting:
        """Create a Setting instance from a database row."""
        return cls(**{k: row[k] for k in row.keys()})


@dataclass
class LogEntry:
    """Represents a log entry stored in the database."""
    id: Optional[int] = None
    timestamp: str = ""
    level: str = "INFO"
    source: str = ""
    message: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> LogEntry:
        """Create a LogEntry instance from a database row."""
        return cls(**{k: row[k] for k in row.keys()})


# ──────────────────────────────────────────────────────────
#  Game Repository
# ──────────────────────────────────────────────────────────

class GameRepository:
    """CRUD operations for the games table."""

    def __init__(self) -> None:
        self.db = DatabaseConnection()

    def add(self, game: Game) -> int:
        """Insert a new game and return its ID."""
        cursor = self.db.execute(
            """INSERT INTO games (name, install_path, save_path, exe_path,
               launcher_type, icon_path, added_date, last_played,
               last_backed_up, notes, is_active)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'), ?, ?, ?, ?)""",
            (game.name, game.install_path, game.save_path, game.exe_path,
             game.launcher_type, game.icon_path, game.last_played,
             game.last_backed_up, game.notes, game.is_active)
        )
        game_id = cursor.lastrowid
        logger.info("Added game: %s (ID: %d)", game.name, game_id)
        return game_id

    def get_by_id(self, game_id: int) -> Optional[Game]:
        """Fetch a game by its ID."""
        row = self.db.fetchone("SELECT * FROM games WHERE id = ?", (game_id,))
        return Game.from_row(row) if row else None

    def get_all(self, active_only: bool = True) -> list[Game]:
        """Fetch all games, optionally filtering by active status."""
        if active_only:
            rows = self.db.fetchall(
                "SELECT * FROM games WHERE is_active = 1 ORDER BY name"
            )
        else:
            rows = self.db.fetchall("SELECT * FROM games ORDER BY name")
        return [Game.from_row(r) for r in rows]

    def update(self, game: Game) -> None:
        """Update an existing game record."""
        if game.id is None:
            raise ValueError("Cannot update a game without an ID")
        self.db.execute(
            """UPDATE games SET name=?, install_path=?, save_path=?, exe_path=?,
               launcher_type=?, icon_path=?, last_played=?, last_backed_up=?,
               notes=?, is_active=?
               WHERE id=?""",
            (game.name, game.install_path, game.save_path, game.exe_path,
             game.launcher_type, game.icon_path, game.last_played,
             game.last_backed_up, game.notes, game.is_active, game.id)
        )
        logger.info("Updated game: %s (ID: %d)", game.name, game.id)

    def delete(self, game_id: int) -> None:
        """Delete a game by ID (cascades to backups)."""
        self.db.execute("DELETE FROM games WHERE id = ?", (game_id,))
        logger.info("Deleted game ID: %d", game_id)

    def search(self, query: str) -> list[Game]:
        """Search games by name (case-insensitive partial match)."""
        rows = self.db.fetchall(
            "SELECT * FROM games WHERE name LIKE ? AND is_active = 1 ORDER BY name",
            (f"%{query}%",)
        )
        return [Game.from_row(r) for r in rows]

    def count(self) -> int:
        """Return the total number of active games."""
        row = self.db.fetchone("SELECT COUNT(*) as c FROM games WHERE is_active = 1")
        return row["c"] if row else 0

    def update_last_backed_up(self, game_id: int) -> None:
        """Update the last_backed_up timestamp for a game."""
        self.db.execute(
            "UPDATE games SET last_backed_up = datetime('now','localtime') WHERE id = ?",
            (game_id,)
        )

    def update_last_played(self, game_id: int) -> None:
        """Update the last_played timestamp for a game."""
        self.db.execute(
            "UPDATE games SET last_played = datetime('now','localtime') WHERE id = ?",
            (game_id,)
        )


# ──────────────────────────────────────────────────────────
#  Backup Repository
# ──────────────────────────────────────────────────────────

class BackupRepository:
    """CRUD operations for the backups table."""

    def __init__(self) -> None:
        self.db = DatabaseConnection()

    def add(self, backup: Backup) -> int:
        """Insert a new backup record and return its ID."""
        cursor = self.db.execute(
            """INSERT INTO backups (game_id, backup_path, backup_name, size_bytes,
               created_at, backup_type, checksum, is_auto, notes)
               VALUES (?, ?, ?, ?, datetime('now','localtime'), ?, ?, ?, ?)""",
            (backup.game_id, backup.backup_path, backup.backup_name,
             backup.size_bytes, backup.backup_type, backup.checksum,
             backup.is_auto, backup.notes)
        )
        backup_id = cursor.lastrowid
        logger.info("Added backup: %s (ID: %d)", backup.backup_name, backup_id)
        return backup_id

    def get_by_id(self, backup_id: int) -> Optional[Backup]:
        """Fetch a backup by its ID."""
        row = self.db.fetchone("SELECT * FROM backups WHERE id = ?", (backup_id,))
        return Backup.from_row(row) if row else None

    def get_by_game(self, game_id: int) -> list[Backup]:
        """Fetch all backups for a specific game, newest first."""
        rows = self.db.fetchall(
            "SELECT * FROM backups WHERE game_id = ? ORDER BY created_at DESC",
            (game_id,)
        )
        return [Backup.from_row(r) for r in rows]

    def get_all(self) -> list[Backup]:
        """Fetch all backups, newest first."""
        rows = self.db.fetchall(
            "SELECT * FROM backups ORDER BY created_at DESC"
        )
        return [Backup.from_row(r) for r in rows]

    def get_recent(self, limit: int = 10) -> list[Backup]:
        """Fetch the most recent backups."""
        rows = self.db.fetchall(
            "SELECT * FROM backups ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [Backup.from_row(r) for r in rows]

    def delete(self, backup_id: int) -> None:
        """Delete a backup record by ID."""
        self.db.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
        logger.info("Deleted backup ID: %d", backup_id)

    def delete_by_game(self, game_id: int) -> None:
        """Delete all backups for a specific game."""
        self.db.execute("DELETE FROM backups WHERE game_id = ?", (game_id,))
        logger.info("Deleted all backups for game ID: %d", game_id)

    def count(self) -> int:
        """Return the total number of backups."""
        row = self.db.fetchone("SELECT COUNT(*) as c FROM backups")
        return row["c"] if row else 0

    def total_size(self) -> int:
        """Return the total size of all backups in bytes."""
        row = self.db.fetchone("SELECT COALESCE(SUM(size_bytes), 0) as s FROM backups")
        return row["s"] if row else 0

    def get_largest_backups(self, limit: int = 5) -> list[Backup]:
        """Fetch the largest backups by size."""
        rows = self.db.fetchall(
            "SELECT * FROM backups ORDER BY size_bytes DESC LIMIT ?",
            (limit,)
        )
        return [Backup.from_row(r) for r in rows]

    def count_by_game(self, game_id: int) -> int:
        """Return the number of backups for a specific game."""
        row = self.db.fetchone(
            "SELECT COUNT(*) as c FROM backups WHERE game_id = ?",
            (game_id,)
        )
        return row["c"] if row else 0


# ──────────────────────────────────────────────────────────
#  Log Repository
# ──────────────────────────────────────────────────────────

class LogRepository:
    """CRUD operations for the logs table (DB-persisted logs)."""

    def __init__(self) -> None:
        self.db = DatabaseConnection()

    def add(self, level: str, source: str, message: str) -> None:
        """Insert a log entry."""
        self.db.execute(
            "INSERT INTO logs (level, source, message) VALUES (?, ?, ?)",
            (level.upper(), source, message)
        )

    def get_recent(self, limit: int = 100, level: Optional[str] = None) -> list[LogEntry]:
        """Fetch recent log entries, optionally filtered by level."""
        if level:
            rows = self.db.fetchall(
                "SELECT * FROM logs WHERE level = ? ORDER BY timestamp DESC LIMIT ?",
                (level.upper(), limit)
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        return [LogEntry.from_row(r) for r in rows]

    def clear(self) -> None:
        """Delete all log entries."""
        self.db.execute("DELETE FROM logs")
        logger.info("All database logs cleared")

    def count(self) -> int:
        """Return the total number of log entries."""
        row = self.db.fetchone("SELECT COUNT(*) as c FROM logs")
        return row["c"] if row else 0

    def export(self) -> list[dict]:
        """Export all logs as a list of dictionaries."""
        rows = self.db.fetchall("SELECT * FROM logs ORDER BY timestamp DESC")
        return [dict(r) for r in rows]
