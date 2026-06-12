"""
CheckPoint — Process monitor.

Uses psutil to track running game processes and trigger
callbacks on game launch/close events for auto-backup.
"""

import threading
import time
from pathlib import Path
from typing import Callable, Optional

import psutil

from app.database.models import GameRepository
from app.utils.logger import get_logger

logger = get_logger("monitoring.process")


class ProcessMonitor:
    """
    Monitors running processes to detect game launches and exits.

    Polls the process list at configurable intervals and invokes
    callbacks when monitored game executables start or stop.
    """

    def __init__(self, interval: int = 10) -> None:
        """
        Initialize the process monitor.

        Args:
            interval: Polling interval in seconds.
        """
        self._interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._game_repo = GameRepository()
        self._active_games: dict[int, int] = {}  # game_id -> pid
        self._on_game_launch: Optional[Callable[[int, str], None]] = None
        self._on_game_close: Optional[Callable[[int, str], None]] = None
        self._lock = threading.Lock()

    def set_callbacks(self,
                      on_launch: Optional[Callable[[int, str], None]] = None,
                      on_close: Optional[Callable[[int, str], None]] = None) -> None:
        """
        Set callback functions for game events.

        Args:
            on_launch: Called with (game_id, game_name) when a game starts.
            on_close: Called with (game_id, game_name) when a game exits.
        """
        self._on_game_launch = on_launch
        self._on_game_close = on_close

    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop,
                                        daemon=True,
                                        name="process-monitor")
        self._thread.start()
        logger.info("Process monitor started (interval: %ds)", self._interval)

    def stop(self) -> None:
        """Stop the monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._interval + 2)
            self._thread = None
        logger.info("Process monitor stopped")

    @property
    def is_running(self) -> bool:
        """Return whether the monitor is currently active."""
        return self._running

    def _monitor_loop(self) -> None:
        """Main polling loop — runs in background thread."""
        while self._running:
            try:
                self._check_processes()
            except Exception as e:
                logger.error("Process monitor error: %s", e)
            time.sleep(self._interval)

    def _check_processes(self) -> None:
        """Check for game process launches and exits."""
        games = self._game_repo.get_all(active_only=True)

        # Build map of exe names to game info
        exe_map: dict[str, tuple[int, str]] = {}
        for game in games:
            if game.exe_path:
                exe_name = Path(game.exe_path).name.lower()
                exe_map[exe_name] = (game.id, game.name)

        if not exe_map:
            return

        # Get current running processes
        current_pids: dict[int, int] = {}  # game_id -> pid
        try:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    proc_name = proc.info["name"].lower() if proc.info["name"] else ""
                    if proc_name in exe_map:
                        game_id, game_name = exe_map[proc_name]
                        current_pids[game_id] = proc.info["pid"]
                except (psutil.NoSuchProcess, psutil.AccessDenied,
                        psutil.ZombieProcess):
                    continue
        except Exception:
            return

        with self._lock:
            # Detect new launches
            for game_id, pid in current_pids.items():
                if game_id not in self._active_games:
                    game_name = next(
                        (name for gid, name in exe_map.values() if gid == game_id),
                        "Unknown"
                    )
                    logger.info("Game launched: %s (PID: %d)", game_name, pid)
                    self._active_games[game_id] = pid
                    if self._on_game_launch:
                        try:
                            self._on_game_launch(game_id, game_name)
                        except Exception as e:
                            logger.error("Launch callback error: %s", e)

            # Detect exits
            closed_ids = [
                gid for gid in self._active_games
                if gid not in current_pids
            ]
            for game_id in closed_ids:
                game_name = next(
                    (name for gid, name in exe_map.values() if gid == game_id),
                    "Unknown"
                )
                logger.info("Game closed: %s", game_name)
                del self._active_games[game_id]
                if self._on_game_close:
                    try:
                        self._on_game_close(game_id, game_name)
                    except Exception as e:
                        logger.error("Close callback error: %s", e)

    def get_active_games(self) -> dict[int, int]:
        """Return a dict of currently running game_id -> pid."""
        with self._lock:
            return dict(self._active_games)
