"""
CheckPoint — Backup Manager screen.

Global view of all backups across all games with filtering,
bulk actions, and search.
"""

from __future__ import annotations

import customtkinter as ctk
from typing import TYPE_CHECKING, Optional

from app.ui.theme import COLORS, FONTS, SPACING, RADIUS, ICONS
from app.ui.components import SectionHeader, EmptyState
from app.ui.dialogs import ConfirmDialog, RestoreDialog
from app.services.backup_service import BackupService
from app.services.game_service import GameService
from app.services.restore_service import RestoreService
from app.utils.helpers import format_bytes, time_ago
from app.utils.logger import get_logger
from datetime import datetime

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = get_logger("ui.backup_manager")


class BackupManagerScreen(ctk.CTkFrame):
    """
    Backup Manager — a global overview of all backups.

    Features:
    - Search backups by name
    - Filter by game or backup type
    - Bulk delete
    - Quick restore from global list
    """

    def __init__(self, master: ctk.CTkFrame, app: "MainWindow", **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = app
        self._backup_service = BackupService()
        self._game_service = GameService()
        self._restore_service = RestoreService()
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search)

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the backup manager layout."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        ctk.CTkLabel(
            header, text="Backup Manager", font=FONTS["heading_xl"],
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        # Global actions
        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row, text=f"{ICONS['backup']}  Backup All",
            font=FONTS["button"],
            fg_color=COLORS["accent_primary"],
            text_color=COLORS["text_on_accent"],
            hover_color=COLORS["accent_primary_hover"],
            height=36, width=130, corner_radius=RADIUS["md"],
            command=self._backup_all,
        ).pack(side="left", padx=(0, SPACING["sm"]))

        # Controls (Search + Filters)
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["md"]))

        self._search_entry = ctk.CTkEntry(
            controls, textvariable=self._search_var,
            placeholder_text=f"{ICONS['search']}  Search backups...",
            font=FONTS["body_md"],
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border_primary"],
            text_color=COLORS["text_primary"],
            height=40, corner_radius=RADIUS["md"],
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, SPACING["md"]))

        # Backup List (Scrollable)
        self._list_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["scrollbar_thumb"],
            scrollbar_button_hover_color=COLORS["scrollbar_thumb_hover"],
        )
        self._list_scroll.pack(fill="both", expand=True, padx=SPACING["xl"],
                             pady=(0, SPACING["xl"]))

        self.refresh()

    def refresh(self) -> None:
        """Reload the backup list."""
        for widget in self._list_scroll.winfo_children():
            widget.destroy()

        query = self._search_var.get().strip().lower()
        all_backups = self._backup_service.get_all_backups()

        # Filter
        if query:
            backups = [b for b in all_backups if query in b.backup_name.lower()]
        else:
            backups = all_backups

        if not backups:
            EmptyState(
                self._list_scroll, icon=ICONS["backup"],
                title="No Backups Found",
                message="Create backups in the Games Library to see them here."
            ).pack(fill="both", expand=True)
            return

        # Table Header
        header_row = ctk.CTkFrame(self._list_scroll, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, SPACING["sm"]))

        ctk.CTkLabel(header_row, text="Backup Name", font=FONTS["body_sm"],
                     text_color=COLORS["text_tertiary"], width=200, anchor="w").pack(side="left", padx=SPACING["md"])
        ctk.CTkLabel(header_row, text="Game", font=FONTS["body_sm"],
                     text_color=COLORS["text_tertiary"], width=150, anchor="w").pack(side="left")
        ctk.CTkLabel(header_row, text="Size", font=FONTS["body_sm"],
                     text_color=COLORS["text_tertiary"], width=80, anchor="w").pack(side="left")
        ctk.CTkLabel(header_row, text="Date", font=FONTS["body_sm"],
                     text_color=COLORS["text_tertiary"], width=150, anchor="w").pack(side="left")
        ctk.CTkLabel(header_row, text="Actions", font=FONTS["body_sm"],
                     text_color=COLORS["text_tertiary"], width=100, anchor="w").pack(side="right")

        # Rows
        for backup in backups:
            self._create_backup_row(backup)

    def _create_backup_row(self, backup) -> None:
        row = ctk.CTkFrame(self._list_scroll, fg_color=COLORS["bg_card"], corner_radius=RADIUS["md"])
        row.pack(fill="x", pady=SPACING["xs"])

        game = self._game_service.get_game(backup.game_id)
        game_name = game.name if game else "Deleted Game"

        # Content
        ctk.CTkLabel(row, text=backup.backup_name, font=FONTS["body_sm"],
                     text_color=COLORS["text_primary"], width=200, anchor="w").pack(side="left", padx=SPACING["md"], pady=SPACING["sm"])

        ctk.CTkLabel(row, text=game_name, font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"], width=150, anchor="w").pack(side="left")

        ctk.CTkLabel(row, text=format_bytes(backup.size_bytes), font=FONTS["body_sm"],
                     text_color=COLORS["text_tertiary"], width=80, anchor="w").pack(side="left")

        ctk.CTkLabel(row, text=backup.created_at, font=FONTS["body_xs"],
                     text_color=COLORS["text_tertiary"], width=150, anchor="w").pack(side="left")

        # Action Buttons
        actions_frame = ctk.CTkFrame(row, fg_color="transparent")
        actions_frame.pack(side="right", padx=SPACING["sm"])

        ctk.CTkButton(
            actions_frame, text=ICONS["restore"], font=FONTS["body_sm"],
            fg_color="transparent", text_color=COLORS["accent_primary"],
            hover_color=COLORS["bg_hover"], width=30, height=30,
            command=lambda bid=backup.id: self._restore_selected(bid)
        ).pack(side="left")

        ctk.CTkButton(
            actions_frame, text=ICONS["delete"], font=FONTS["body_sm"],
            fg_color="transparent", text_color=COLORS["accent_danger"],
            hover_color=COLORS["bg_hover"], width=30, height=30,
            command=lambda bid=backup.id: self._delete_selected(bid)
        ).pack(side="left")

    def _on_search(self, *args) -> None:
        self.refresh()

    def _backup_all(self) -> None:
        ConfirmDialog(
            self._app, title="Backup All Games",
            message="This will create a backup for every registered game. Continue?",
            on_confirm=self._do_backup_all
        )

    def _do_backup_all(self) -> None:
        self._backup_service.backup_all_games()
        self.refresh()
        self._app.notify("Success", "All games backed up successfully.")

    def _restore_selected(self, backup_id: int) -> None:
        backup = self._backup_service._backup_repo.get_by_id(backup_id)
        if not backup: return

        RestoreDialog(
            self._app, backups=[backup],
            on_restore=lambda bid, path: self._do_restore(bid, path)
        )

    def _do_restore(self, backup_id: int, custom_path: Optional[str]) -> None:
        success = self._restore_service.restore_backup(backup_id, custom_path)
        if success:
            self._app.notify("Success", "Backup restored successfully.")

    def _delete_selected(self, backup_id: int) -> None:
        ConfirmDialog(
            self._app, title="Delete Backup",
            message="Are you sure you want to permanently delete this backup?",
            danger=True,
            on_confirm=lambda: (self._backup_service.delete_backup(backup_id), self.refresh())
        )
