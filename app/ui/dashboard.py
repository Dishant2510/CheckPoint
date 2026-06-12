"""
CheckPoint — Dashboard screen.

Main landing screen displaying storage analytics cards,
recent backup activity feed, and a storage breakdown chart.
"""

from __future__ import annotations

import math
import customtkinter as ctk
from typing import Optional

from app.ui.theme import COLORS, FONTS, SPACING, RADIUS, ICONS, get_chart_color
from app.ui.components import StatCard, SectionHeader, ActivityItem, EmptyState
from app.services.storage_service import StorageService
from app.services.backup_service import BackupService
from app.services.game_service import GameService
from app.database.models import GameRepository
from app.utils.helpers import format_bytes, time_ago
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger("ui.dashboard")


class DashboardScreen(ctk.CTkFrame):
    """
    Dashboard — the main landing screen.

    Displays:
    - Storage stat cards (total games, backups, storage used)
    - Recent backup activity feed
    - Storage breakdown by game (visual bar chart)
    """

    def __init__(self, master: ctk.CTkFrame, app: "MainWindow", **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = app
        self._storage_service = StorageService()
        self._backup_service = BackupService()
        self._game_service = GameService()

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the dashboard layout."""
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["scrollbar_thumb"],
            scrollbar_button_hover_color=COLORS["scrollbar_thumb_hover"],
        )
        scroll.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        # Page title
        title_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, SPACING["lg"]))

        ctk.CTkLabel(
            title_frame, text="Dashboard", font=FONTS["heading_xl"],
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            title_frame, text="↻  Refresh", font=FONTS["button_sm"],
            fg_color=COLORS["bg_tertiary"], text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_hover"], height=32, width=100,
            corner_radius=RADIUS["md"],
            command=self.refresh,
        ).pack(side="right")

        # ── Stat Cards Row ──
        self._cards_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._cards_frame.pack(fill="x", pady=(0, SPACING["xl"]))
        self._cards_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="card")

        self._stat_cards: dict[str, StatCard] = {}
        self._create_stat_cards()

        # ── Two-Column Layout: Activity + Storage ──
        columns = ctk.CTkFrame(scroll, fg_color="transparent")
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=3)
        columns.columnconfigure(1, weight=2)

        # Left column — Recent Activity
        left = ctk.CTkFrame(columns, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["md"]))

        SectionHeader(left, title="Recent Activity").pack(fill="x", pady=(0, SPACING["md"]))

        self._activity_frame = ctk.CTkFrame(
            left, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"],
        )
        self._activity_frame.pack(fill="both", expand=True)

        # Right column — Storage Breakdown
        right = ctk.CTkFrame(columns, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        SectionHeader(right, title="Storage Breakdown").pack(fill="x", pady=(0, SPACING["md"]))

        self._storage_frame = ctk.CTkFrame(
            right, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"],
        )
        self._storage_frame.pack(fill="both", expand=True)

        # Populate data
        self.refresh()

    def _create_stat_cards(self) -> None:
        """Create the four dashboard stat cards."""
        cards_config = [
            ("total_games", "Total Games", "0", ICONS["games"], COLORS["accent_primary"]),
            ("total_backups", "Total Backups", "0", ICONS["backup"], COLORS["accent_secondary"]),
            ("storage_used", "Storage Used", "0 B", ICONS["storage"], COLORS["accent_warning"]),
            ("unprotected", "Unprotected", "0", ICONS["warning"], COLORS["accent_danger"]),
        ]

        for i, (key, title, value, icon, accent) in enumerate(cards_config):
            card = StatCard(self._cards_frame, title=title, value=value,
                           icon=icon, accent=accent)
            card.grid(row=0, column=i, sticky="nsew",
                      padx=(0 if i == 0 else SPACING["sm"], 0),
                      ipady=SPACING["sm"])
            self._stat_cards[key] = card

    def refresh(self) -> None:
        """Reload all dashboard data."""
        try:
            stats = self._storage_service.get_dashboard_stats()

            self._stat_cards["total_games"].update_value(str(stats["total_games"]))
            self._stat_cards["total_backups"].update_value(str(stats["total_backups"]))
            self._stat_cards["storage_used"].update_value(stats["total_backup_size_formatted"])
            self._stat_cards["unprotected"].update_value(str(stats["games_without_backup"]))

            self._populate_activity()
            self._populate_storage()

        except Exception as e:
            logger.error("Dashboard refresh error: %s", e)

    def _populate_activity(self) -> None:
        """Fill the recent activity feed."""
        # Clear existing items
        for widget in self._activity_frame.winfo_children():
            widget.destroy()

        recent = self._backup_service.get_recent_backups(limit=8)

        if not recent:
            EmptyState(
                self._activity_frame, icon="📋",
                title="No Activity Yet",
                message="Back up your first game to see activity here.",
            ).pack(fill="both", expand=True, pady=SPACING["xl"])
            return

        inner = ctk.CTkFrame(self._activity_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["md"], pady=SPACING["md"])

        for backup in recent:
            game = self._game_service.get_game(backup.game_id)
            game_name = game.name if game else "Unknown Game"
            icon = "🔄" if backup.is_auto else "💾"
            btype = "Auto-backup" if backup.is_auto else "Manual backup"

            try:
                dt = datetime.strptime(backup.created_at, "%Y-%m-%d %H:%M:%S")
                ago = time_ago(dt)
            except (ValueError, TypeError):
                ago = backup.created_at

            ActivityItem(
                inner, icon=icon,
                title=f"{game_name}",
                subtitle=f"{btype} — {format_bytes(backup.size_bytes)}",
                time_ago=ago,
            ).pack(fill="x", pady=(0, SPACING["xs"]))

    def _populate_storage(self) -> None:
        """Fill the storage breakdown section."""
        for widget in self._storage_frame.winfo_children():
            widget.destroy()

        breakdown = self._storage_service.get_storage_breakdown()

        if not breakdown or all(b["size"] == 0 for b in breakdown):
            EmptyState(
                self._storage_frame, icon="💿",
                title="No Storage Data",
                message="Create backups to see storage usage.",
            ).pack(fill="both", expand=True, pady=SPACING["xl"])
            return

        inner = ctk.CTkFrame(self._storage_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["md"], pady=SPACING["md"])

        # Show top entries with progress bars
        for i, entry in enumerate(breakdown[:8]):
            if entry["size"] == 0:
                continue

            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=(0, SPACING["sm"]))

            # Label row
            label_row = ctk.CTkFrame(row, fg_color="transparent")
            label_row.pack(fill="x")

            color = get_chart_color(i)

            # Color dot
            ctk.CTkLabel(
                label_row, text="●", font=FONTS["body_sm"],
                text_color=color, width=20,
            ).pack(side="left")

            ctk.CTkLabel(
                label_row, text=entry["name"], font=FONTS["body_sm"],
                text_color=COLORS["text_primary"],
            ).pack(side="left")

            ctk.CTkLabel(
                label_row, text=entry["size_formatted"],
                font=FONTS["body_xs"], text_color=COLORS["text_tertiary"],
            ).pack(side="right")

            # Progress bar
            bar = ctk.CTkProgressBar(
                row, height=6,
                fg_color=COLORS["bg_primary"],
                progress_color=color,
                corner_radius=3,
            )
            bar.pack(fill="x", pady=(SPACING["xs"], 0))
            bar.set(entry["percentage"] / 100)
