"""
CheckPoint — Restore service.

Handles extracting backup archives to restore game save files
to their original or a custom destination path.
"""

import shutil
import zipfile
from pathlib import Path
from typing import Optional, Callable

from app.database.models import Backup, BackupRepository, GameRepository, LogRepository
from app.utils.helpers import format_bytes, calculate_file_checksum
from app.utils.logger import get_logger

logger = get_logger("services.restore")


class RestoreService:
    """
    Engine for restoring game save backups.

    Extracts ZIP archives back to original save paths or
    user-specified custom paths, with integrity checks.
    """

    def __init__(self) -> None:
        """Initialize the restore service."""
        self._backup_repo = BackupRepository()
        self._game_repo = GameRepository()
        self._log_repo = LogRepository()

    def restore_backup(self, backup_id: int,
                       target_path: Optional[str] = None,
                       progress_callback: Optional[Callable[[float], None]] = None
                       ) -> bool:
        """
        Restore a backup to the original save path or a custom path.

        Args:
            backup_id: The backup record ID.
            target_path: Custom restore path. If None, uses the game's save_path.
            progress_callback: Optional callback(progress: 0.0-1.0).

        Returns:
            True if restoration succeeded.
        """
        backup = self._backup_repo.get_by_id(backup_id)
        if not backup:
            logger.error("Backup ID %d not found", backup_id)
            return False

        backup_file = Path(backup.backup_path)
        if not backup_file.exists():
            logger.error("Backup file not found: %s", backup.backup_path)
            self._log_repo.add("ERROR", "RestoreService",
                               f"Backup file missing: {backup.backup_name}")
            return False

        # Determine target directory
        if target_path:
            restore_dir = Path(target_path)
        else:
            game = self._game_repo.get_by_id(backup.game_id)
            if not game or not game.save_path:
                logger.error("No save path for game ID %d", backup.game_id)
                return False
            restore_dir = Path(game.save_path)

        try:
            # Verify backup integrity first
            if backup.checksum:
                current_checksum = calculate_file_checksum(backup_file)
                if current_checksum != backup.checksum:
                    logger.warning("Checksum mismatch for %s — restoring anyway",
                                   backup.backup_name)
                    self._log_repo.add("WARNING", "RestoreService",
                                       f"Checksum mismatch: {backup.backup_name}")

            # Create target directory
            restore_dir.mkdir(parents=True, exist_ok=True)

            # Extract the ZIP archive
            with zipfile.ZipFile(str(backup_file), "r") as zf:
                members = zf.namelist()
                total = len(members)

                for i, member in enumerate(members):
                    zf.extract(member, str(restore_dir))
                    if progress_callback:
                        progress_callback((i + 1) / total)

            logger.info("Restored backup '%s' to %s (%d files)",
                        backup.backup_name, restore_dir, len(members))
            self._log_repo.add("INFO", "RestoreService",
                               f"Restored '{backup.backup_name}' to {restore_dir}")
            return True

        except zipfile.BadZipFile:
            logger.error("Corrupted backup file: %s", backup.backup_name)
            self._log_repo.add("ERROR", "RestoreService",
                               f"Corrupted backup: {backup.backup_name}")
            return False
        except Exception as e:
            logger.error("Restore failed for '%s': %s", backup.backup_name, e)
            self._log_repo.add("ERROR", "RestoreService",
                               f"Restore failed: {e}")
            return False

    def preview_backup(self, backup_id: int) -> Optional[dict]:
        """
        Get metadata about a backup without extracting it.

        Args:
            backup_id: The backup record ID.

        Returns:
            Dict with keys: files, total_size, created_at, checksum_valid.
        """
        backup = self._backup_repo.get_by_id(backup_id)
        if not backup:
            return None

        backup_file = Path(backup.backup_path)
        if not backup_file.exists():
            return None

        try:
            with zipfile.ZipFile(str(backup_file), "r") as zf:
                files = []
                total_uncompressed = 0
                for info in zf.infolist():
                    files.append({
                        "name": info.filename,
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "modified": f"{info.date_time[0]}-{info.date_time[1]:02d}-"
                                    f"{info.date_time[2]:02d} "
                                    f"{info.date_time[3]:02d}:{info.date_time[4]:02d}",
                    })
                    total_uncompressed += info.file_size

            # Verify checksum
            checksum_valid = True
            if backup.checksum:
                current = calculate_file_checksum(backup_file)
                checksum_valid = current == backup.checksum

            return {
                "backup_name": backup.backup_name,
                "files": files,
                "file_count": len(files),
                "compressed_size": backup.size_bytes,
                "uncompressed_size": total_uncompressed,
                "created_at": backup.created_at,
                "checksum_valid": checksum_valid,
                "backup_type": backup.backup_type,
            }

        except zipfile.BadZipFile:
            logger.error("Cannot preview corrupted backup: %s",
                         backup.backup_name)
            return None

    def get_restorable_backups(self, game_id: int) -> list[Backup]:
        """
        Get all backups for a game that have valid ZIP files on disk.

        Args:
            game_id: The game's ID.

        Returns:
            List of restorable backup records.
        """
        backups = self._backup_repo.get_by_game(game_id)
        return [b for b in backups if Path(b.backup_path).exists()]
