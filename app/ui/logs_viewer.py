"""
CheckPoint — Logs Viewer screen.

Real-time view of application logs stored in the database,
with level filtering and export support.
"""

from __future__ import annotations

import customtkinter as ctk
from typing import TYPE_CHECKING, Optional

from app.ui.theme import COLORS, FONTS, SPACING, RADIUS, ICONS
from app.database.models import LogRepository
from app.utils.logger import get_logger

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = get_logger("ui.logs_viewer")


class LogsViewerScreen(ctk.CTkFrame):
    """
    Logs Viewer screen.
    """

    def __init__(self, master: ctk.CTkFrame, app: "MainWindow", **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = app
        self._log_repo = LogRepository()
        self._level_var = ctk.StringVar(value="ALL")
        self._build_ui()

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        ctk.CTkLabel(header, text="System Logs", font=FONTS["heading_xl"],
                     text_color=COLORS["text_primary"]).pack(side="left")

        # Filters
        filter_frame = ctk.CTkFrame(header, fg_color="transparent")
        filter_frame.pack(side="right")

        self._level_menu = ctk.CTkOptionMenu(
            filter_frame, values=["ALL", "INFO", "WARNING", "ERROR"],
            variable=self._level_var, command=lambda _: self.refresh()
        )
        self._level_menu.pack(side="left", padx=SPACING["sm"])

        ctk.CTkButton(header, text="Clear Logs", fg_color=COLORS["accent_danger"], width=100, command=self._clear_logs).pack(side="right", padx=SPACING["sm"])
        ctk.CTkButton(header, text="Refresh", width=100, command=self.refresh).pack(side="right")

        # Log Table
        self._table_container = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"])
        self._table_container.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["xl"]))

        self.refresh()

    def refresh(self) -> None:
        for widget in self._table_container.winfo_children():
            widget.destroy()

        lvl = None if self._level_var.get() == "ALL" else self._level_var.get()
        logs = self._log_repo.get_recent(limit=100, level=lvl)

        for log in logs:
            row = ctk.CTkFrame(self._table_container, fg_color="transparent")
            row.pack(fill="x", pady=2)

            color = COLORS["text_secondary"]
            if log.level == "ERROR": color = COLORS["accent_danger"]
            if log.level == "WARNING": color = COLORS["accent_warning"]

            ctk.CTkLabel(row, text=log.timestamp, font=FONTS["mono_sm"], text_color=COLORS["text_tertiary"], width=150).pack(side="left")
            ctk.CTkLabel(row, text=f"[{log.level}]", font=FONTS["mono_sm"], text_color=color, width=80).pack(side="left")
            ctk.CTkLabel(row, text=log.message, font=FONTS["body_sm"], text_color=COLORS["text_primary"], anchor="w").pack(side="left", fill="x", expand=True)

    def _clear_logs(self) -> None:
        self._log_repo.clear()
        self.refresh()
