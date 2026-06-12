"""
CheckPoint — Settings screen.

Application configuration interface for backup paths,
monitoring behavior, and UI theme.
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog
from typing import TYPE_CHECKING

from app.ui.theme import COLORS, FONTS, SPACING, RADIUS, ICONS
from app.utils.config import ConfigManager
from app.utils.logger import get_logger

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = get_logger("ui.settings")


class SettingsScreen(ctk.CTkFrame):
    """
    Settings screen for application configuration.
    """

    def __init__(self, master: ctk.CTkFrame, app: "MainWindow", **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = app
        self._config = ConfigManager()
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        ctk.CTkLabel(scroll, text="Settings", font=FONTS["heading_xl"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, SPACING["lg"]))

        # Storage Section
        self._create_section(scroll, "Storage & Backups")

        # Backup Directory
        dir_frame = self._create_setting_row(scroll, "Backup Directory", "Where the save ZIPs are stored.")
        self._dir_entry = ctk.CTkEntry(dir_frame, font=FONTS["body_sm"], width=300)
        self._dir_entry.insert(0, self._config.get("backup_directory"))
        self._dir_entry.pack(side="left", padx=(0, SPACING["sm"]))
        ctk.CTkButton(dir_frame, text="Browse", width=80, command=self._browse_dir).pack(side="left")

        # Max Backups
        self._create_setting_row(scroll, "Max Backups per Game", "Automatic cleanup of older backups.")
        self._max_backups = ctk.CTkSlider(scroll, from_=1, to=50, number_of_steps=49, command=self._on_slider)
        self._max_backups.set(self._config.get("max_backups_per_game"))
        self._max_backups.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        self._max_label = ctk.CTkLabel(scroll, text=str(int(self._max_backups.get())), font=FONTS["body_xs"])
        self._max_label.pack(anchor="e", padx=SPACING["lg"])

        # Automation Section
        self._create_section(scroll, "Automation")

        self._auto_backup = self._create_switch(scroll, "Enable Auto-Backup", "Backup games automatically on close.", "auto_backup_enabled")
        self._minimize_tray = self._create_switch(scroll, "Minimize to Tray", "Keep app running in background.", "minimize_to_tray")
        self._notifications = self._create_switch(scroll, "Show Notifications", "Notify on backup completion.", "show_notifications")

        # UI Section
        self._create_section(scroll, "Appearance")
        # Theme would go here, defaulting to Dark for now as per gaming aesthetic requirements.

        # Save Button
        ctk.CTkButton(
            scroll, text="Save Settings", font=FONTS["button"],
            fg_color=COLORS["accent_primary"], text_color=COLORS["text_on_accent"],
            hover_color=COLORS["accent_primary_hover"], height=40,
            command=self._save_settings
        ).pack(pady=SPACING["xl"])

    def _create_section(self, parent, title):
        ctk.CTkLabel(parent, text=title, font=FONTS["heading_md"],
                     text_color=COLORS["accent_primary"]).pack(anchor="w", pady=(SPACING["lg"], SPACING["sm"]))
        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border_secondary"]).pack(fill="x", pady=(0, SPACING["md"]))

    def _create_setting_row(self, parent, title, desc):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=SPACING["sm"])
        text_frame = ctk.CTkFrame(frame, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_frame, text=title, font=FONTS["body_md"], text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=desc, font=FONTS["body_xs"], text_color=COLORS["text_tertiary"]).pack(anchor="w")
        return frame

    def _create_switch(self, parent, title, desc, config_key):
        frame = self._create_setting_row(parent, title, desc)
        var = ctk.BooleanVar(value=self._config.get(config_key))
        switch = ctk.CTkSwitch(frame, text="", variable=var, fg_color=COLORS["bg_tertiary"], progress_color=COLORS["accent_primary"])
        switch.pack(side="right")
        return var

    def _on_slider(self, val):
        self._max_label.configure(text=str(int(val)))

    def _browse_dir(self):
        path = filedialog.askdirectory()
        if path:
            self._dir_entry.delete(0, "end")
            self._dir_entry.insert(0, path)

    def _save_settings(self):
        self._config.set("backup_directory", self._dir_entry.get())
        self._config.set("max_backups_per_game", int(self._max_backups.get()))
        self._config.set("auto_backup_enabled", self._auto_backup.get())
        self._config.set("minimize_to_tray", self._minimize_tray.get())
        self._config.set("show_notifications", self._notifications.get())
        self._app.notify("Success", "Settings saved successfully.")
        logger.info("Settings updated by user.")
