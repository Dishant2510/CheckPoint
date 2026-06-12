"""
CheckPoint — Configuration management.

JSON-based configuration with defaults, get/set access, and persistence.
Thread-safe read/write operations with automatic file creation.
"""

import json
import threading
from pathlib import Path
from typing import Any, Optional

from app.utils.paths import get_data_dir, get_default_backup_dir
from app.utils.logger import get_logger

logger = get_logger("config")

# Default configuration values
_DEFAULTS: dict[str, Any] = {
    "backup_directory": str(get_default_backup_dir()),
    "auto_backup_enabled": True,
    "auto_backup_on_close": True,
    "monitor_interval_seconds": 10,
    "max_backups_per_game": 10,
    "compression_level": 6,
    "theme": "dark",
    "minimize_to_tray": True,
    "show_notifications": True,
    "log_level": "INFO",
    "scan_on_startup": False,
    "backup_retention_days": 90,
    "differential_backup": False,
    "portable_mode": False,
}


class ConfigManager:
    """
    Manages application configuration via a JSON file.

    Thread-safe singleton that loads config on first access and
    persists changes immediately.
    """

    _instance: Optional["ConfigManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ConfigManager":
        """Ensure only one ConfigManager instance exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the config manager, loading from disk if available."""
        if self._initialized:
            return
        self._config: dict[str, Any] = {}
        self._config_path: Path = get_data_dir() / "config.json"
        self._rw_lock = threading.RLock()
        self._load()
        self._initialized = True

    def _load(self) -> None:
        """Load configuration from JSON file, falling back to defaults."""
        with self._rw_lock:
            self._config = dict(_DEFAULTS)
            if self._config_path.exists():
                try:
                    with open(self._config_path, "r", encoding="utf-8") as f:
                        stored = json.load(f)
                    self._config.update(stored)
                    logger.info("Configuration loaded from %s", self._config_path)
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning("Failed to load config, using defaults: %s", e)
            else:
                self._save()
                logger.info("Created default configuration at %s", self._config_path)

    def _save(self) -> None:
        """Persist the current configuration to disk."""
        with self._rw_lock:
            try:
                self._config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._config_path, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            except OSError as e:
                logger.error("Failed to save config: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value.

        Args:
            key: The config key.
            default: Fallback if key is not found.

        Returns:
            The configuration value, or default.
        """
        with self._rw_lock:
            return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value and persist immediately.

        Args:
            key: The config key.
            value: The value to store.
        """
        with self._rw_lock:
            self._config[key] = value
            self._save()
        logger.debug("Config updated: %s = %s", key, value)

    def get_all(self) -> dict[str, Any]:
        """Return a copy of the full configuration dictionary."""
        with self._rw_lock:
            return dict(self._config)

    def reset(self) -> None:
        """Reset all configuration to defaults and persist."""
        with self._rw_lock:
            self._config = dict(_DEFAULTS)
            self._save()
        logger.info("Configuration reset to defaults")

    def get_backup_dir(self) -> Path:
        """Return the configured backup directory as a Path object."""
        return Path(self.get("backup_directory", str(get_default_backup_dir())))
