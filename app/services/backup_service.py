"""
CheckPoint — Backup service.

Handles creating ZIP-compressed backups of game save files,
with timestamped naming, checksums, and version management.
"""

import os
import shutil
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from app.database.models import Backup, BackupRepository, GameRepository, LogRepository
from app.utils.config import ConfigManager
from app.utils.helpers import (
    format_bytes,
    get_backup_timestamp,
    calculate_file_checksum,
    safe_game_folder_name,
    calculate_dir_size,
)
from app.utils.logger import get_logger

logger = get_logger("services.backup")


class BackupService:
    """
    Engine for creating and managing game save backups.

    Creates ZIP-compressed, timestamped backup archives with
    SHA-256 integrity checksums.
    """

    def __init__(self) -> None:
        """Initialize the backup service."""
        self._backup_repo = BackupRepository()
        self._game_repo = GameRepository()
        self._log_repo = LogRepository()
        self._config = ConfigManager()
        self._lock = threading.Lock()

    def _get_backup_dir(self, game_name: str) -> Path:
        """
        Get the backup directory for a specific game.

        Creates the directory structure if it doesn't exist.
        """
        backup_root = self._config.get_backup_dir()
        game_dir = backup_root / safe_game_folder_name(game_name)
        game_dir.mkdir(parents=True, exist_ok=True)
        return game_dir

    def create_backup(self, game_id: int, backup_name: Optional[str] = None,
                      is_auto: bool = False,
                      progress_callback: Optional[Callable[[float], None]] = None
                      ) -> Optional[Backup]:
        """
        Create a backup of a game's save files.

        Args:
            game_id: The ID of the game to back up.
            backup_name: Optional custom name for the backup.
            is_auto: Whether this is an automatic backup.
            progress_callback: Optional callback(progress: 0.0-1.0).

        Returns:
            The created Backup record, or None on failure.
        """
        with self._lock:
            game = self._game_repo.get_by_id(game_id)
            if not game:
                logger.error("Game ID %d not found", game_id)
                return None

            if not game.save_path or not Path(game.save_path).exists():
                logger.error("Save path not found for '%s': %s",
                             game.name, game.save_path)
                self._log_repo.add("ERROR", "BackupService",
                                   f"Save path not found for '{game.name}'")
                return None

            # Generate backup filename
            timestamp = get_backup_timestamp()
            if backup_name:
                zip_name = f"{timestamp}_{backup_name}.zip"
            else:
                zip_name = f"{timestamp}.zip"

            backup_dir = self._get_backup_dir(game.name)
            zip_path = backup_dir / zip_name

            try:
                # Collect files to backup
                save_path = Path(game.save_path)
                files_to_backup: list[Path] = []

                if save_path.is_file():
                    files_to_backup.append(save_path)
                else:
                    for fp in save_path.rglob("*"):
                        if fp.is_file():
                            files_to_backup.append(fp)

                if not files_to_backup:
                    logger.warning("No files found in save path for '%s'",
                                   game.name)
                    self._log_repo.add("WARNING", "BackupService",
                                       f"No files found for '{game.name}'")
                    return None

                total_files = len(files_to_backup)
                compression = self._config.get("compression_level", 6)

                # Create ZIP archive
                with zipfile.ZipFile(str(zip_path), "w",
                                     zipfile.ZIP_DEFLATED,
                                     compresslevel=compression) as zf:
                    for i, file_path in enumerate(files_to_backup):
                        if save_path.is_file():
                            arcname = file_path.name
                        else:
                            arcname = str(file_path.relative_to(save_path))
                        zf.write(str(file_path), arcname)

                        if progress_callback:
                            progress_callback((i + 1) / total_files)

                # Calculate checksum and size
                zip_size = zip_path.stat().st_size
                checksum = calculate_file_checksum(zip_path)

                # Create database record
                backup = Backup(
                    game_id=game_id,
                    backup_path=str(zip_path),
                    backup_name=zip_name,
                    size_bytes=zip_size,
                    backup_type="auto" if is_auto else "manual",
                    checksum=checksum,
                    is_auto=1 if is_auto else 0,
                )

                backup_id = self._backup_repo.add(backup)
                backup.id = backup_id

                # Update game's last backed up timestamp
                self._game_repo.update_last_backed_up(game_id)

                # Enforce retention policy
                self._enforce_retention(game_id, game.name)

                logger.info("Backup created: %s (%s, %d files)",
                            zip_name, format_bytes(zip_size), total_files)
                self._log_repo.add("INFO", "BackupService",
                                   f"Backup created for '{game.name}': "
                                   f"{zip_name} ({format_bytes(zip_size)})")
                return backup

            except Exception as e:
                logger.error("Backup failed for '%s': %s", game.name, e)
                self._log_repo.add("ERROR", "BackupService",
                                   f"Backup failed for '{game.name}': {e}")
                # Clean up partial ZIP
                if zip_path.exists():
                    zip_path.unlink()
                return None

    def create_backup_async(self, game_id: int,
                            backup_name: Optional[str] = None,
                            is_auto: bool = False,
                            callback: Optional[Callable[[Optional[Backup]], None]] = None,
                            progress_callback: Optional[Callable[[float], None]] = None
                            ) -> threading.Thread:
        """
        Create a backup in a background thread.

        Args:
            game_id: The game ID.
            backup_name: Optional custom name.
            is_auto: Whether automatic.
            callback: Called with the Backup result when done.
            progress_callback: Called with progress float 0.0–1.0.

        Returns:
            The background thread.
        """
        def _run() -> None:
            result = self.create_backup(game_id, backup_name, is_auto,
                                        progress_callback)
            if callback:
                callback(result)

        thread = threading.Thread(target=_run, daemon=True,
                                  name=f"backup-{game_id}")
        thread.start()
        return thread

    def backup_all_games(self, progress_callback: Optional[Callable[[int, int, str], None]] = None
                         ) -> list[Backup]:
        """
        Backup all registered games that have valid save paths.

        Args:
            progress_callback: Called with (current, total, game_name).

        Returns:
            List of successfully created backups.
        """
        games = self._game_repo.get_all(active_only=True)
        results: list[Backup] = []
        total = len(games)

        for i, game in enumerate(games):
            if game.save_path and Path(game.save_path).exists():
                if progress_callback:
                    progress_callback(i + 1, total, game.name)
                backup = self.create_backup(game.id)
                if backup:
                    results.append(backup)

        logger.info("Bulk backup complete: %d/%d games backed up",
                     len(results), total)
        return results

    def _enforce_retention(self, game_id: int, game_name: str) -> None:
        """Remove the oldest backups if the game exceeds the max limit."""
        max_backups = self._config.get("max_backups_per_game", 10)
        backups = self._backup_repo.get_by_game(game_id)

        if len(backups) > max_backups:
            excess = backups[max_backups:]
            for old_backup in excess:
                # Delete the file
                backup_path = Path(old_backup.backup_path)
                if backup_path.exists():
                    backup_path.unlink()
                    logger.info("Retention: deleted old backup %s",
                                old_backup.backup_name)
                # Delete the record
                self._backup_repo.delete(old_backup.id)

    def get_backups_for_game(self, game_id: int) -> list[Backup]:
        """Fetch all backups for a game."""
        return self._backup_repo.get_by_game(game_id)

    def get_all_backups(self) -> list[Backup]:
        """Fetch all backups."""
        return self._backup_repo.get_all()

    def get_recent_backups(self, limit: int = 10) -> list[Backup]:
        """Fetch the most recent backups."""
        return self._backup_repo.get_recent(limit)

    def delete_backup(self, backup_id: int) -> bool:
        """
        Delete a backup record and its ZIP file.

        Args:
            backup_id: The backup ID to delete.

        Returns:
            True if successful.
        """
        backup = self._backup_repo.get_by_id(backup_id)
        if not backup:
            return False

        # Delete the physical file
        backup_path = Path(backup.backup_path)
        if backup_path.exists():
            backup_path.unlink()

        # Delete the record
        self._backup_repo.delete(backup_id)
        logger.info("Deleted backup: %s", backup.backup_name)
        return True

    def verify_backup(self, backup_id: int) -> bool:
        """
        Verify a backup's integrity by recalculating its checksum.

        Args:
            backup_id: The backup ID to verify.

        Returns:
            True if the checksum matches.
        """
        backup = self._backup_repo.get_by_id(backup_id)
        if not backup:
            return False

        backup_path = Path(backup.backup_path)
        if not backup_path.exists():
            return False

        current_checksum = calculate_file_checksum(backup_path)
        is_valid = current_checksum == backup.checksum

        if not is_valid:
            logger.warning("Backup integrity check FAILED for %s",
                           backup.backup_name)
            self._log_repo.add("WARNING", "BackupService",
                               f"Integrity check failed: {backup.backup_name}")

        return is_valid

    def get_backup_count(self) -> int:
        """Return total number of backups."""
        return self._backup_repo.count()

    def get_total_backup_size(self) -> int:
        """Return total size of all backups in bytes."""
        return self._backup_repo.total_size()
