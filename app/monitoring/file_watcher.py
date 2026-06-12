"""
CheckPoint — File system watcher.

Uses watchdog to monitor save directories for changes,
triggering debounced events for auto-backup notifications.
"""

import threading
import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from app.utils.logger import get_logger

logger = get_logger("monitoring.file_watcher")


class _SaveFileHandler(FileSystemEventHandler):
    """Handler that tracks file system changes and fires debounced callbacks."""

    def __init__(self, game_id: int, game_name: str,
                 on_change: Callable[[int, str], None],
                 debounce_seconds: float = 5.0) -> None:
        super().__init__()
        self._game_id = game_id
        self._game_name = game_name
        self._on_change = on_change
        self._debounce = debounce_seconds
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def _trigger(self) -> None:
        """Fire the debounced callback."""
        logger.debug("Save change detected for '%s'", self._game_name)
        try:
            self._on_change(self._game_id, self._game_name)
        except Exception as e:
            logger.error("File watcher callback error: %s", e)

    def _debounce_trigger(self) -> None:
        """Reset the debounce timer on each event."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._trigger)
            self._timer.daemon = True
            self._timer.start()

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._debounce_trigger()

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._debounce_trigger()

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._debounce_trigger()


class FileWatcher:
    """
    Watches game save directories for file changes.

    Manages multiple watchdog observers, one per monitored game,
    with debounced change notifications.
    """

    def __init__(self, debounce_seconds: float = 5.0) -> None:
        """
        Initialize the file watcher.

        Args:
            debounce_seconds: Time to wait after last change before notifying.
        """
        self._debounce = debounce_seconds
        self._observers: dict[int, Observer] = {}  # game_id -> Observer
        self._on_change: Optional[Callable[[int, str], None]] = None
        self._lock = threading.Lock()

    def set_callback(self, on_change: Callable[[int, str], None]) -> None:
        """
        Set the callback for file change events.

        Args:
            on_change: Called with (game_id, game_name) after changes settle.
        """
        self._on_change = on_change

    def watch(self, game_id: int, game_name: str, save_path: str) -> bool:
        """
        Start watching a game's save directory.

        Args:
            game_id: The game's ID.
            game_name: The game's display name.
            save_path: Path to the save directory.

        Returns:
            True if watching started successfully.
        """
        if not self._on_change:
            logger.warning("No callback set for file watcher")
            return False

        path = Path(save_path)
        if not path.exists():
            logger.warning("Save path does not exist: %s", save_path)
            return False

        with self._lock:
            # Stop existing watcher for this game
            if game_id in self._observers:
                self.unwatch(game_id)

            handler = _SaveFileHandler(game_id, game_name,
                                        self._on_change, self._debounce)
            observer = Observer()
            observer.schedule(handler, str(path), recursive=True)
            observer.daemon = True

            try:
                observer.start()
                self._observers[game_id] = observer
                logger.info("Watching save directory for '%s': %s",
                            game_name, save_path)
                return True
            except Exception as e:
                logger.error("Failed to start watcher for '%s': %s",
                             game_name, e)
                return False

    def unwatch(self, game_id: int) -> None:
        """Stop watching a specific game's save directory."""
        with self._lock:
            if game_id in self._observers:
                try:
                    self._observers[game_id].stop()
                    self._observers[game_id].join(timeout=5)
                except Exception as e:
                    logger.warning("Error stopping watcher: %s", e)
                del self._observers[game_id]
                logger.info("Stopped watching game ID %d", game_id)

    def stop_all(self) -> None:
        """Stop all active file watchers."""
        with self._lock:
            for game_id, observer in list(self._observers.items()):
                try:
                    observer.stop()
                    observer.join(timeout=5)
                except Exception:
                    pass
            self._observers.clear()
            logger.info("All file watchers stopped")

    @property
    def watched_count(self) -> int:
        """Return the number of actively watched directories."""
        return len(self._observers)

    def is_watching(self, game_id: int) -> bool:
        """Check if a specific game is being watched."""
        return game_id in self._observers
