"""
CheckPoint — Save file detector.

Heuristic engine that scans common directories and matches against
known game save path signatures to detect save file locations.
"""

import json
import os
from pathlib import Path
from typing import Optional

from app.utils.paths import (
    get_documents_dir,
    get_saved_games_dir,
    get_appdata_local,
    get_appdata_roaming,
    get_steam_userdata_dir,
    get_data_dir,
)
from app.utils.logger import get_logger

logger = get_logger("scanners.save_detector")


class SaveDetector:
    """
    Detects game save file locations using signatures and heuristics.

    Loads known patterns from signatures.json and provides methods
    to scan the filesystem for matching save directories.
    """

    def __init__(self) -> None:
        """Initialize the detector and load signatures."""
        self._signatures: dict = {}
        self._load_signatures()

    def _load_signatures(self) -> None:
        """Load the game save signatures from the data directory."""
        import shutil
        import sys
        
        sig_path = get_data_dir() / "signatures.json"
        
        if not sig_path.exists():
            # Find the bundled signatures file
            if getattr(sys, "frozen", False):
                # Under PyInstaller onedir/onefile, sys._MEIPASS contains the path to the bundled files.
                bundled_sig = Path(sys._MEIPASS) / "data" / "signatures.json"
            else:
                bundled_sig = Path(__file__).resolve().parent.parent.parent / "data" / "signatures.json"

            if bundled_sig.exists():
                try:
                    # Copy to user data directory for persistence and customization
                    shutil.copy(bundled_sig, sig_path)
                    logger.info("Copied bundled signatures.json to %s", sig_path)
                except OSError as e:
                    logger.warning("Failed to copy bundled signatures to user data dir: %s. Loading direct from bundle.", e)
                    sig_path = bundled_sig

        if sig_path.exists():
            try:
                with open(sig_path, "r", encoding="utf-8") as f:
                    self._signatures = json.load(f)
                logger.info("Loaded %d game signatures",
                            len(self._signatures.get("patterns", [])))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load signatures: %s", e)
                self._signatures = {"patterns": [], "save_extensions": [],
                                    "save_folder_names": [], "save_file_names": []}
        else:
            logger.warning("Signatures file not found at %s", sig_path)
            self._signatures = {"patterns": [], "save_extensions": [],
                                "save_folder_names": [], "save_file_names": []}

    def _expand_path(self, pattern_path: str) -> Optional[Path]:
        """
        Expand environment-variable-style tokens in a signature path.

        Supported tokens:
            %APPDATA%     → AppData/Roaming
            %LOCALAPPDATA% → AppData/Local
            %DOCUMENTS%   → User Documents
            %SAVEDGAMES%  → Saved Games
            %STEAMID%     → Steam userdata directory
        """
        replacements = {
            "%APPDATA%": str(get_appdata_roaming()),
            "%LOCALAPPDATA%": str(get_appdata_local()),
            "%DOCUMENTS%": str(get_documents_dir()),
            "%SAVEDGAMES%": str(get_saved_games_dir()),
        }

        expanded = pattern_path
        for token, value in replacements.items():
            expanded = expanded.replace(token, value)

        # Handle Steam userdata paths
        if "%STEAMID%" in expanded:
            steam_ud = get_steam_userdata_dir()
            if steam_ud:
                # Try each user ID directory
                try:
                    for user_dir in steam_ud.iterdir():
                        if user_dir.is_dir():
                            candidate = expanded.replace("%STEAMID%",
                                                         str(user_dir))
                            if Path(candidate).exists():
                                return Path(candidate)
                except PermissionError:
                    pass
            return None

        result = Path(expanded)
        return result if result.exists() else None

    def detect_by_signature(self, game_name: str) -> Optional[str]:
        """
        Try to find the save path for a game using known signatures.

        Args:
            game_name: The name of the game to look up.

        Returns:
            The save path string if found, None otherwise.
        """
        patterns = self._signatures.get("patterns", [])
        name_lower = game_name.lower()

        for pattern in patterns:
            if pattern["game"].lower() in name_lower or name_lower in pattern["game"].lower():
                for path_template in pattern.get("paths", []):
                    resolved = self._expand_path(path_template)
                    if resolved:
                        logger.info("Signature match for '%s': %s",
                                    game_name, resolved)
                        return str(resolved)

        logger.debug("No signature match for '%s'", game_name)
        return None

    def detect_by_heuristic(self, game_name: str) -> Optional[str]:
        """
        Attempt to find save files by scanning common directories
        for folders matching the game name.

        Args:
            game_name: The game name to search for.

        Returns:
            The discovered save path, or None.
        """
        search_dirs = [
            get_documents_dir(),
            get_saved_games_dir(),
            get_appdata_local(),
            get_appdata_roaming(),
        ]

        # Simplify game name for matching
        search_terms = [
            game_name.lower(),
            game_name.lower().replace(" ", ""),
            game_name.lower().replace(":", "").replace("-", ""),
        ]

        for base_dir in search_dirs:
            if not base_dir.exists():
                continue
            try:
                for entry in base_dir.iterdir():
                    if not entry.is_dir():
                        continue
                    entry_name = entry.name.lower()
                    for term in search_terms:
                        if term in entry_name or entry_name in term:
                            # Check if it contains save-like files
                            if self._looks_like_save_dir(entry):
                                logger.info("Heuristic match for '%s': %s",
                                            game_name, entry)
                                return str(entry)
            except PermissionError:
                continue

        return None

    def _looks_like_save_dir(self, directory: Path) -> bool:
        """
        Check whether a directory contains files that look like game saves.

        Uses known extensions and folder names from signatures.
        """
        save_extensions = set(self._signatures.get("save_extensions", []))
        save_folder_names = set(
            n.lower() for n in self._signatures.get("save_folder_names", [])
        )

        # Check if it's a known save folder name
        if directory.name.lower() in save_folder_names:
            return True

        # Check for save-like files within (max 2 levels deep)
        try:
            for item in directory.rglob("*"):
                if item.is_file() and item.suffix.lower() in save_extensions:
                    return True
                # Don't go too deep
                relative = item.relative_to(directory)
                if len(relative.parts) > 2:
                    continue
        except (PermissionError, OSError):
            pass

        return False

    def detect_save_path(self, game_name: str) -> Optional[str]:
        """
        Combined detection: try signatures first, then heuristics.

        Args:
            game_name: The game name to detect saves for.

        Returns:
            The detected save path, or None.
        """
        # Try signature-based detection first
        result = self.detect_by_signature(game_name)
        if result:
            return result

        # Fall back to heuristic scan
        return self.detect_by_heuristic(game_name)

    def scan_all_known_saves(self) -> list[dict]:
        """
        Scan for all known games from signatures that have saves present.

        Returns:
            List of dicts with keys: game, save_path, launcher.
        """
        found: list[dict] = []
        patterns = self._signatures.get("patterns", [])

        for pattern in patterns:
            for path_template in pattern.get("paths", []):
                resolved = self._expand_path(path_template)
                if resolved:
                    found.append({
                        "game": pattern["game"],
                        "save_path": str(resolved),
                        "launcher": pattern.get("launcher", "unknown"),
                    })
                    break  # Found one valid path for this game

        logger.info("Found %d known game saves on this system", len(found))
        return found
