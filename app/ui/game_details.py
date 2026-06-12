"""
CheckPoint — Game Details screen.

Displays detailed information about a single game including
metadata, save path, backup history, and action buttons.
"""

from __future__ import annotations

import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from typing import Optional, TYPE_CHECKING

from app.ui.theme import COLORS, FONTS, SPACING, RADIUS, ICONS, LAUNCHER_CONFIG
from app.ui.components import SectionHeader, EmptyState
from app.ui.dialogs import ConfirmDialog, RestoreDialog, SafeDeleteDialog
from app.services.game_service import GameService
from app.services.backup_service import BackupService
from app.services.restore_service import RestoreService
from app.database.models import Game
from app.utils.helpers import format_bytes, time_ago
from app.utils.logger import get_logger
from datetime import datetime

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = get_logger("ui.game_details")


class GameDetailsScreen(ctk.CTkFrame):
    """
    Game Details — full metadata view for a single game.

    Shows:
    - Game metadata (name, paths, launcher, dates)
    - Backup history timeline
    - Quick actions (backup, restore, edit, delete)
    """

    def __init__(self, master: ctk.CTkFrame, app: "MainWindow",
                 game_id: int, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = app
        self._game_id = game_id
        self._game_service = GameService()
        self._backup_service = BackupService()
        self._restore_service = RestoreService()

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the game details layout."""
        game = self._game_service.get_game(self._game_id)
        if not game:
            EmptyState(self, icon="❌", title="Game Not Found").pack(
                fill="both", expand=True)
            return

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["scrollbar_thumb"],
        )
        scroll.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        # ── Back button + Title ──
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, SPACING["lg"]))

        ctk.CTkButton(
            header, text="← Back", font=FONTS["button"],
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_hover"], height=32, width=80,
            corner_radius=RADIUS["md"],
            command=lambda: self._app.show_screen("games"),
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=game.name, font=FONTS["heading_xl"],
            text_color=COLORS["text_primary"],
        ).pack(side="left", padx=SPACING["md"])

        # Launcher badge
        launcher_info = LAUNCHER_CONFIG.get(game.launcher_type,
                                             LAUNCHER_CONFIG["unknown"])
        ctk.CTkLabel(
            header, text=f"  {launcher_info['label']}  ",
            font=FONTS["body_xs"], text_color="#FFFFFF",
            fg_color=launcher_info["color"], corner_radius=RADIUS["sm"],
        ).pack(side="left")

        # ── Action Buttons ──
        actions = ctk.CTkFrame(scroll, fg_color="transparent")
        actions.pack(fill="x", pady=(0, SPACING["xl"]))

        ctk.CTkButton(
            actions, text=f"{ICONS['backup']}  Backup Now",
            font=FONTS["button"],
            fg_color=COLORS["accent_primary"],
            text_color=COLORS["text_on_accent"],
            hover_color=COLORS["accent_primary_hover"],
            height=38, width=140, corner_radius=RADIUS["md"],
            command=self._backup_game,
        ).pack(side="left", padx=(0, SPACING["sm"]))

        ctk.CTkButton(
            actions, text=f"{ICONS['restore']}  Restore",
            font=FONTS["button"],
            fg_color=COLORS["accent_secondary"],
            text_color="#FFFFFF", hover_color="#6d28d9",
            height=38, width=120, corner_radius=RADIUS["md"],
            command=self._restore_game,
        ).pack(side="left", padx=(0, SPACING["sm"]))

        ctk.CTkButton(
            actions, text=f"{ICONS['delete']}  Delete",
            font=FONTS["button"],
            fg_color=COLORS["accent_danger"],
            text_color="#FFFFFF",
            hover_color=COLORS["accent_danger_hover"],
            height=38, width=110, corner_radius=RADIUS["md"],
            command=self._delete_game,
        ).pack(side="right")

        # ── Metadata Section ──
        SectionHeader(scroll, title="Game Information").pack(
            fill="x", pady=(0, SPACING["md"]))

        meta_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"],
                                  corner_radius=RADIUS["lg"])
        meta_card.pack(fill="x", pady=(0, SPACING["xl"]))

        meta_inner = ctk.CTkFrame(meta_card, fg_color="transparent")
        meta_inner.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        self._meta_fields: dict[str, ctk.CTkLabel] = {}

        fields = [
            ("Install Path", game.install_path or "Not set"),
            ("Save Path", game.save_path or "Not detected"),
            ("Executable", game.exe_path or "Not set"),
            ("Added", game.added_date or "Unknown"),
            ("Last Played", game.last_played or "Never"),
            ("Last Backed Up", game.last_backed_up or "Never"),
            ("Notes", game.notes or "—"),
        ]

        for label, value in fields:
            row = ctk.CTkFrame(meta_inner, fg_color="transparent")
            row.pack(fill="x", pady=SPACING["xs"])

            ctk.CTkLabel(
                row, text=label, font=FONTS["body_sm"],
                text_color=COLORS["text_tertiary"], width=120, anchor="w",
            ).pack(side="left")

            val_color = COLORS["text_primary"]
            if value in ("Not set", "Not detected", "Never", "Unknown", "—"):
                val_color = COLORS["text_tertiary"]

            val_label = ctk.CTkLabel(
                row, text=value, font=FONTS["body_sm"],
                text_color=val_color, anchor="w",
                wraplength=400,
            )
            val_label.pack(side="left", fill="x", expand=True)
            self._meta_fields[label] = val_label

        # Edit save path button
        edit_frame = ctk.CTkFrame(meta_inner, fg_color="transparent")
        edit_frame.pack(fill="x", pady=(SPACING["md"], 0))

        ctk.CTkButton(
            edit_frame, text="📁 Change Save Path",
            font=FONTS["button_sm"],
            fg_color=COLORS["bg_tertiary"],
            text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_hover"],
            height=32, width=160, corner_radius=RADIUS["md"],
            command=self._change_save_path,
        ).pack(side="left", padx=(0, SPACING["sm"]))

        ctk.CTkButton(
            edit_frame, text="🔍 Auto-Detect",
            font=FONTS["button_sm"],
            fg_color=COLORS["bg_tertiary"],
            text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_hover"],
            height=32, width=130, corner_radius=RADIUS["md"],
            command=self._auto_detect_save,
        ).pack(side="left")

        # ── Backup History Section ──
        SectionHeader(scroll, title="Backup History").pack(
            fill="x", pady=(0, SPACING["md"]))

        self._history_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"],
                                            corner_radius=RADIUS["lg"])
        self._history_frame.pack(fill="x")

        self._populate_history()

    def _populate_history(self) -> None:
        """Fill the backup history timeline."""
        for widget in self._history_frame.winfo_children():
            widget.destroy()

        backups = self._backup_service.get_backups_for_game(self._game_id)

        if not backups:
            EmptyState(
                self._history_frame, icon="📦",
                title="No Backups Yet",
                message="Create your first backup for this game.",
            ).pack(fill="both", expand=True, pady=SPACING["lg"])
            return

        inner = ctk.CTkFrame(self._history_frame, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        for backup in backups:
            row = ctk.CTkFrame(inner, fg_color=COLORS["bg_tertiary"],
                               corner_radius=RADIUS["md"])
            row.pack(fill="x", pady=SPACING["xs"])

            content = ctk.CTkFrame(row, fg_color="transparent")
            content.pack(fill="x", padx=SPACING["md"], pady=SPACING["sm"])

            # Icon + name
            icon = "🔄" if backup.is_auto else "💾"
            ctk.CTkLabel(
                content, text=f"{icon}  {backup.backup_name}",
                font=FONTS["body_sm"], text_color=COLORS["text_primary"],
                anchor="w",
            ).pack(side="left")

            # Size + date
            meta = f"{format_bytes(backup.size_bytes)}  •  {backup.created_at}"
            ctk.CTkLabel(
                content, text=meta, font=FONTS["body_xs"],
                text_color=COLORS["text_tertiary"],
            ).pack(side="right", padx=(0, SPACING["sm"]))

            # Delete button
            ctk.CTkButton(
                content, text="✕", font=FONTS["body_xs"],
                fg_color="transparent", text_color=COLORS["text_tertiary"],
                hover_color=COLORS["accent_danger"], width=24, height=24,
                corner_radius=RADIUS["sm"],
                command=lambda bid=backup.id: self._delete_backup(bid),
            ).pack(side="right")

    def _backup_game(self) -> None:
        """Create a backup for this game."""
        game = self._game_service.get_game(self._game_id)
        if not game:
            return

        if not game.save_path or not Path(game.save_path).exists():
            ConfirmDialog(
                self._app, title="No Save Path",
                message="Save path is not set or doesn't exist. "
                        "Please set the save path first.",
                confirm_text="OK", cancel_text="",
            )
            return

        result = self._backup_service.create_backup(self._game_id)
        if result:
            self._populate_history()
            self._refresh_meta()
            logger.info("Backup created for game ID %d", self._game_id)

    def _restore_game(self) -> None:
        """Open the restore dialog."""
        backups = self._restore_service.get_restorable_backups(self._game_id)
        if not backups:
            ConfirmDialog(
                self._app, title="No Backups",
                message="No restorable backups found for this game.",
                confirm_text="OK", cancel_text="",
            )
            return

        RestoreDialog(
            self._app, backups=backups,
            on_restore=self._do_restore,
        )

    def _do_restore(self, backup_id: int, custom_path: Optional[str]) -> None:
        """Execute the restore operation."""
        success = self._restore_service.restore_backup(backup_id, custom_path)
        if success:
            logger.info("Restore successful for backup ID %d", backup_id)

    def _delete_game(self) -> None:
        """Open the safe delete dialog."""
        game = self._game_service.get_game(self._game_id)
        if not game:
            return

        has_saves = bool(game.save_path and Path(game.save_path).exists())

        SafeDeleteDialog(
            self._app,
            game_name=game.name,
            has_saves=has_saves,
            on_backup_and_delete=lambda: self._do_backup_and_delete(),
            on_delete_only=lambda: self._do_delete(),
        )

    def _do_backup_and_delete(self) -> None:
        """Backup then delete the game."""
        self._backup_service.create_backup(self._game_id)
        self._game_service.delete_game(self._game_id)
        self._app.show_screen("games")

    def _do_delete(self) -> None:
        """Delete the game without backup."""
        self._game_service.delete_game(self._game_id)
        self._app.show_screen("games")

    def _delete_backup(self, backup_id: int) -> None:
        """Delete a specific backup."""
        ConfirmDialog(
            self._app, title="Delete Backup",
            message="Are you sure you want to delete this backup? This cannot be undone.",
            confirm_text="Delete", danger=True,
            on_confirm=lambda: (
                self._backup_service.delete_backup(backup_id),
                self._populate_history(),
            ),
        )

    def _change_save_path(self) -> None:
        """Change the save path via folder dialog."""
        path = filedialog.askdirectory(title="Select Save File Location")
        if path:
            game = self._game_service.get_game(self._game_id)
            if game:
                game.save_path = path
                self._game_service.update_game(game)
                self._meta_fields["Save Path"].configure(
                    text=path, text_color=COLORS["text_primary"])

    def _auto_detect_save(self) -> None:
        """Attempt auto-detection of save path."""
        game = self._game_service.get_game(self._game_id)
        if game:
            detected = self._game_service.detect_save_path(game.name)
            if detected:
                game.save_path = detected
                self._game_service.update_game(game)
                self._meta_fields["Save Path"].configure(
                    text=detected, text_color=COLORS["accent_success"])
            else:
                self._meta_fields["Save Path"].configure(
                    text="Auto-detection failed",
                    text_color=COLORS["accent_warning"])

    def _refresh_meta(self) -> None:
        """Refresh the metadata display after changes."""
        game = self._game_service.get_game(self._game_id)
        if game and "Last Backed Up" in self._meta_fields:
            self._meta_fields["Last Backed Up"].configure(
                text=game.last_backed_up or "Never")
