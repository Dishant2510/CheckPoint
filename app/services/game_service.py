"""
CheckPoint — Game management service.

Handles game registration, metadata, and CRUD operations
with save path auto-detection support.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from app.database.models import Game, GameRepository
from app.scanners.save_detector import SaveDetector
from app.utils.logger import get_logger
from app.utils.helpers import format_timestamp

logger = get_logger("services.game")


class GameService:
    """
    Business logic for game management.

    Wraps the GameRepository with additional functionality
    like save path detection and validation.
    """

    def __init__(self) -> None:
        """Initialize the game service."""
        self._repo = GameRepository()
        self._detector = SaveDetector()

    def add_game(self, name: str, install_path: str = "",
                 save_path: str = "", exe_path: str = "",
                 launcher_type: str = "unknown",
                 notes: str = "") -> int:
        """
        Register a new game.

        If save_path is empty, attempts automatic detection.

        Args:
            name: Display name of the game.
            install_path: Path to the game's install directory.
            save_path: Path to the game's save files.
            exe_path: Path to the game's executable.
            launcher_type: One of 'steam', 'epic', 'emulator', 'offline', 'unknown'.
            notes: Optional notes about the game.

        Returns:
            The newly created game's ID.
        """
        # Auto-detect save path if not provided
        if not save_path:
            detected = self._detector.detect_save_path(name)
            if detected:
                save_path = detected
                logger.info("Auto-detected save path for '%s': %s", name, save_path)

        game = Game(
            name=name,
            install_path=install_path,
            save_path=save_path,
            exe_path=exe_path,
            launcher_type=launcher_type,
            notes=notes,
        )

        game_id = self._repo.add(game)
        logger.info("Game registered: %s (ID: %d)", name, game_id)
        return game_id

    def get_game(self, game_id: int) -> Optional[Game]:
        """Fetch a game by its ID."""
        return self._repo.get_by_id(game_id)

    def get_all_games(self) -> list[Game]:
        """Fetch all active games."""
        return self._repo.get_all(active_only=True)

    def update_game(self, game: Game) -> None:
        """Update a game's metadata."""
        self._repo.update(game)

    def delete_game(self, game_id: int) -> None:
        """Soft-delete a game by marking it inactive."""
        game = self._repo.get_by_id(game_id)
        if game:
            game.is_active = 0
            self._repo.update(game)
            logger.info("Game soft-deleted: %s (ID: %d)", game.name, game_id)

    def hard_delete_game(self, game_id: int) -> None:
        """Permanently delete a game and its backup records."""
        self._repo.delete(game_id)

    def search_games(self, query: str) -> list[Game]:
        """Search games by name."""
        return self._repo.search(query)

    def get_game_count(self) -> int:
        """Return total number of active games."""
        return self._repo.count()

    def detect_save_path(self, game_name: str) -> Optional[str]:
        """
        Attempt to detect the save path for a game.

        Args:
            game_name: The game's display name.

        Returns:
            Detected save path, or None.
        """
        return self._detector.detect_save_path(game_name)

    def update_last_played(self, game_id: int) -> None:
        """Mark a game as recently played."""
        self._repo.update_last_played(game_id)

    def update_last_backed_up(self, game_id: int) -> None:
        """Mark a game as recently backed up."""
        self._repo.update_last_backed_up(game_id)

    def validate_save_path(self, save_path: str) -> bool:
        """
        Check if a save path exists and is accessible.

        Args:
            save_path: The path to validate.

        Returns:
            True if the path exists and is readable.
        """
        if not save_path:
            return False
        path = Path(save_path)
        return path.exists() and os.access(str(path), os.R_OK)

    def get_games_needing_backup(self) -> list[Game]:
        """
        Find games that have saves but haven't been backed up recently.

        Returns:
            List of games that have a save_path but no recent backup.
        """
        all_games = self.get_all_games()
        needs_backup: list[Game] = []
        for game in all_games:
            if game.save_path and not game.last_backed_up:
                needs_backup.append(game)
        return needs_backup


# Need to import os for validate_save_path
import os
