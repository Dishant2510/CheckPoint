"""
CheckPoint — Storage analytics service.

Provides disk usage analysis, per-game statistics, and
storage breakdown for the dashboard.
"""

from pathlib import Path
from typing import Optional

from app.database.models import GameRepository, BackupRepository, Game
from app.utils.config import ConfigManager
from app.utils.helpers import calculate_dir_size, format_bytes
from app.utils.logger import get_logger

logger = get_logger("services.storage")


class StorageService:
    """
    Analyzes storage usage across games and backups.

    Provides aggregate statistics for dashboard display
    and per-game storage breakdowns.
    """

    def __init__(self) -> None:
        """Initialize the storage service."""
        self._game_repo = GameRepository()
        self._backup_repo = BackupRepository()
        self._config = ConfigManager()

    def get_dashboard_stats(self) -> dict:
        """
        Calculate aggregate statistics for the dashboard.

        Returns:
            Dict with keys: total_games, total_backups, total_backup_size,
            total_backup_size_formatted, games_without_backup, 
            latest_backup_date.
        """
        total_games = self._game_repo.count()
        total_backups = self._backup_repo.count()
        total_backup_size = self._backup_repo.total_size()
        
        # Find games without backups
        all_games = self._game_repo.get_all()
        games_without_backup = sum(
            1 for g in all_games if not g.last_backed_up
        )

        # Find latest backup date
        recent = self._backup_repo.get_recent(limit=1)
        latest_backup_date = recent[0].created_at if recent else "Never"

        return {
            "total_games": total_games,
            "total_backups": total_backups,
            "total_backup_size": total_backup_size,
            "total_backup_size_formatted": format_bytes(total_backup_size),
            "games_without_backup": games_without_backup,
            "latest_backup_date": latest_backup_date,
        }

    def get_per_game_stats(self) -> list[dict]:
        """
        Calculate storage stats per game.

        Returns:
            List of dicts with keys: game_id, game_name, backup_count,
            total_size, total_size_formatted, save_size, save_size_formatted.
        """
        games = self._game_repo.get_all()
        stats: list[dict] = []

        for game in games:
            backups = self._backup_repo.get_by_game(game.id)
            total_size = sum(b.size_bytes for b in backups)
            save_size = 0
            if game.save_path and Path(game.save_path).exists():
                save_size = calculate_dir_size(Path(game.save_path))

            stats.append({
                "game_id": game.id,
                "game_name": game.name,
                "backup_count": len(backups),
                "total_size": total_size,
                "total_size_formatted": format_bytes(total_size),
                "save_size": save_size,
                "save_size_formatted": format_bytes(save_size),
                "last_backed_up": game.last_backed_up or "Never",
            })

        # Sort by total backup size descending
        stats.sort(key=lambda s: s["total_size"], reverse=True)
        return stats

    def get_backup_directory_size(self) -> int:
        """Calculate the total size of the backup directory on disk."""
        backup_dir = self._config.get_backup_dir()
        if backup_dir.exists():
            return calculate_dir_size(backup_dir)
        return 0

    def get_backup_directory_size_formatted(self) -> str:
        """Return formatted backup directory size."""
        return format_bytes(self.get_backup_directory_size())

    def get_largest_games(self, limit: int = 5) -> list[dict]:
        """
        Get the games with the largest backup storage usage.

        Returns:
            List of dicts sorted by backup size descending.
        """
        stats = self.get_per_game_stats()
        return stats[:limit]

    def get_recoverable_space(self) -> dict:
        """
        Estimate space that could be recovered by cleaning old backups.

        Considers the retention policy (backup_retention_days) and
        max_backups_per_game settings.

        Returns:
            Dict with keys: excess_backups, recoverable_bytes,
            recoverable_formatted.
        """
        max_per_game = self._config.get("max_backups_per_game", 10)
        games = self._game_repo.get_all()
        excess_count = 0
        recoverable_bytes = 0

        for game in games:
            backups = self._backup_repo.get_by_game(game.id)
            if len(backups) > max_per_game:
                excess = backups[max_per_game:]
                excess_count += len(excess)
                recoverable_bytes += sum(b.size_bytes for b in excess)

        return {
            "excess_backups": excess_count,
            "recoverable_bytes": recoverable_bytes,
            "recoverable_formatted": format_bytes(recoverable_bytes),
        }

    def get_storage_breakdown(self) -> list[dict]:
        """
        Get a storage breakdown suitable for chart display.

        Returns:
            List of dicts with keys: name, size, percentage.
        """
        stats = self.get_per_game_stats()
        total = sum(s["total_size"] for s in stats)

        breakdown: list[dict] = []
        for s in stats:
            pct = (s["total_size"] / total * 100) if total > 0 else 0
            breakdown.append({
                "name": s["game_name"],
                "size": s["total_size"],
                "size_formatted": s["total_size_formatted"],
                "percentage": round(pct, 1),
            })

        return breakdown
