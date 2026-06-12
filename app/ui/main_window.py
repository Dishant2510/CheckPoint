"""
CheckPoint — Main application window.

Root CTk window providing sidebar navigation, screen switching,
and system tray integration.
"""

from __future__ import annotations

import customtkinter as ctk
from typing import Dict, Any, Optional

from app.ui.theme import COLORS, FONTS, SPACING, RADIUS, ICONS, SIDEBAR_WIDTH
from app.ui.dashboard import DashboardScreen
from app.ui.games_library import GamesLibraryScreen
from app.ui.game_details import GameDetailsScreen
from app.ui.backup_manager import BackupManagerScreen
from app.ui.settings_screen import SettingsScreen
from app.ui.logs_viewer import LogsViewerScreen

from app.services.backup_service import BackupService
from app.monitoring.process_monitor import ProcessMonitor
from app.utils.config import ConfigManager
from app.utils.logger import get_logger

logger = get_logger("ui.main_window")


class MainWindow(ctk.CTk):
    """
    CheckPoint Main Window.
    """

    def __init__(self) -> None:
        super().__init__()

        # Setup
        self.title("CheckPoint — PC Save Manager")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_primary"])

        self._config = ConfigManager()
        self._backup_service = BackupService()
        self._monitor = ProcessMonitor()

        # State
        self._current_screen: Optional[ctk.CTkFrame] = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self._build_ui()
        self._start_services()

        # Set default screen
        self.show_screen("dashboard")

    def _build_ui(self) -> None:
        # Sidebar
        self._sidebar = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=SPACING["xl"])
        
        ctk.CTkLabel(logo_frame, text="🛡 CheckPoint", font=FONTS["heading_lg"], text_color=COLORS["accent_primary"]).pack()

        # Nav Items
        self._create_nav_item("dashboard", f"{ICONS['dashboard']}  Dashboard")
        self._create_nav_item("games", f"{ICONS['games']}  Library")
        self._create_nav_item("backups", f"{ICONS['backup']}  Backups")
        self._create_nav_item("logs", f"{ICONS['logs']}  Logs")
        
        # Spacer
        spacer = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        self._create_nav_item("settings", f"{ICONS['settings']}  Settings")

        # Main Content Area
        self._container = ctk.CTkFrame(self, fg_color=COLORS["bg_primary"])
        self._container.pack(side="right", fill="both", expand=True)

    def _create_nav_item(self, screen_id: str, label: str) -> None:
        btn = ctk.CTkButton(
            self._sidebar, text=label, font=FONTS["nav_item"],
            anchor="w", height=45, corner_radius=0,
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_hover"],
            command=lambda sid=screen_id: self.show_screen(sid)
        )
        btn.pack(fill="x", padx=SPACING["sm"], pady=2)
        self._nav_buttons[screen_id] = btn

    def show_screen(self, screen_id: str) -> None:
        if self._current_screen:
            self._current_screen.destroy()

        # Update Nav Styles
        for sid, btn in self._nav_buttons.items():
            if sid == screen_id:
                btn.configure(fg_color=COLORS["bg_active"], text_color=COLORS["accent_primary"], font=FONTS["nav_item_active"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"], font=FONTS["nav_item"])

        # Create Screen
        if screen_id == "dashboard":
            self._current_screen = DashboardScreen(self._container, self)
        elif screen_id == "games":
            self._current_screen = GamesLibraryScreen(self._container, self)
        elif screen_id == "backups":
            self._current_screen = BackupManagerScreen(self._container, self)
        elif screen_id == "settings":
            self._current_screen = SettingsScreen(self._container, self)
        elif screen_id == "logs":
            self._current_screen = LogsViewerScreen(self._container, self)
        
        if self._current_screen:
            self._current_screen.pack(fill="both", expand=True)

    def show_game_details(self, game_id: int) -> None:
        if self._current_screen:
            self._current_screen.destroy()
        
        self._current_screen = GameDetailsScreen(self._container, self, game_id)
        self._current_screen.pack(fill="both", expand=True)

    def _start_services(self) -> None:
        if self._config.get("auto_backup_enabled"):
            self._monitor.set_callbacks(on_close=self._handle_game_close)
            self._monitor.start()

    def _handle_game_close(self, game_id: int, game_name: str) -> None:
        logger.info("Automatic backup triggered for %s", game_name)
        self._backup_service.create_backup(game_id, is_auto=True)
        self.notify("Auto-Backup", f"Saved progress for {game_name}")

    def notify(self, title: str, message: str) -> None:
        # Mock notification for now. Real notifications could use toast-notifications.
        logger.info("UI Notify: [%s] %s", title, message)

    def on_closing(self):
        self._monitor.stop()
        self.destroy()
