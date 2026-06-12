"""
CheckPoint — Reusable UI components.

Custom widgets built on CustomTkinter: stat cards, game cards,
status badges, progress bars, and section headers.
"""

from __future__ import annotations

import customtkinter as ctk
from typing import Optional, Callable

from app.ui.theme import COLORS, FONTS, SPACING, RADIUS, ICONS


class StatCard(ctk.CTkFrame):
    """
    Dashboard statistic card displaying a large value with a label.

    Renders as a rounded dark card with accent-colored value text
    and a descriptive label underneath.
    """

    def __init__(self, master: ctk.CTkFrame, title: str, value: str,
                 icon: str = "", accent: str = COLORS["accent_primary"],
                 **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            **kwargs,
        )

        # Inner padding frame
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["lg"])

        # Icon + Title row
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", anchor="w")

        if icon:
            icon_label = ctk.CTkLabel(
                header, text=icon, font=FONTS["heading_md"],
                text_color=accent,
            )
            icon_label.pack(side="left", padx=(0, SPACING["sm"]))

        title_label = ctk.CTkLabel(
            header, text=title, font=FONTS["stat_label"],
            text_color=COLORS["text_secondary"],
        )
        title_label.pack(side="left")

        # Value
        self._value_label = ctk.CTkLabel(
            inner, text=value, font=FONTS["stat_value"],
            text_color=accent, anchor="w",
        )
        self._value_label.pack(fill="x", pady=(SPACING["sm"], 0))

    def update_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value_label.configure(text=value)


class GameCard(ctk.CTkFrame):
    """
    A clickable game card for the library grid.

    Displays game name, launcher badge, save path status,
    and last backup info.
    """

    def __init__(self, master: ctk.CTkFrame, game_name: str,
                 launcher: str = "unknown", save_status: str = "No saves",
                 last_backup: str = "Never",
                 on_click: Optional[Callable[[], None]] = None,
                 **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            cursor="hand2",
            **kwargs,
        )

        self._on_click = on_click

        # Bind click events
        self.bind("<Button-1>", self._handle_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["lg"])
        content.bind("<Button-1>", self._handle_click)

        # Game icon placeholder + name
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")
        header.bind("<Button-1>", self._handle_click)

        icon_label = ctk.CTkLabel(
            header, text=ICONS["games"], font=FONTS["heading_md"],
            text_color=COLORS["accent_primary"],
        )
        icon_label.pack(side="left", padx=(0, SPACING["sm"]))
        icon_label.bind("<Button-1>", self._handle_click)

        name_label = ctk.CTkLabel(
            header, text=game_name, font=FONTS["heading_sm"],
            text_color=COLORS["text_primary"], anchor="w",
        )
        name_label.pack(side="left", fill="x", expand=True)
        name_label.bind("<Button-1>", self._handle_click)

        # Launcher badge
        from app.ui.theme import LAUNCHER_CONFIG
        launcher_info = LAUNCHER_CONFIG.get(launcher, LAUNCHER_CONFIG["unknown"])
        badge = ctk.CTkLabel(
            content, text=f"  {launcher_info['label']}  ",
            font=FONTS["body_xs"],
            text_color=COLORS["text_primary"],
            fg_color=launcher_info["color"],
            corner_radius=RADIUS["sm"],
        )
        badge.pack(anchor="w", pady=(SPACING["sm"], 0))
        badge.bind("<Button-1>", self._handle_click)

        # Save status
        status_row = ctk.CTkFrame(content, fg_color="transparent")
        status_row.pack(fill="x", pady=(SPACING["sm"], 0))
        status_row.bind("<Button-1>", self._handle_click)

        status_color = COLORS["accent_success"] if "detected" in save_status.lower() or save_status != "No saves" else COLORS["text_tertiary"]
        ctk.CTkLabel(
            status_row, text=f"💾 {save_status}", font=FONTS["body_xs"],
            text_color=status_color,
        ).pack(side="left")

        # Last backup
        backup_row = ctk.CTkFrame(content, fg_color="transparent")
        backup_row.pack(fill="x", pady=(SPACING["xs"], 0))
        backup_row.bind("<Button-1>", self._handle_click)

        ctk.CTkLabel(
            backup_row, text=f"⏱ Last backup: {last_backup}",
            font=FONTS["body_xs"],
            text_color=COLORS["text_tertiary"],
        ).pack(side="left")

    def _handle_click(self, event=None) -> None:
        if self._on_click:
            self._on_click()

    def _on_enter(self, event=None) -> None:
        self.configure(fg_color=COLORS["bg_card_hover"])

    def _on_leave(self, event=None) -> None:
        self.configure(fg_color=COLORS["bg_card"])


class StatusBadge(ctk.CTkLabel):
    """Small colored badge indicating a status (Online, Synced, Error, etc.)."""

    STATUS_STYLES = {
        "success": {"fg_color": COLORS["accent_success"], "text": "✓ Active"},
        "warning": {"fg_color": COLORS["accent_warning"], "text": "⚠ Warning"},
        "error": {"fg_color": COLORS["accent_danger"], "text": "✕ Error"},
        "synced": {"fg_color": COLORS["accent_primary"], "text": "⟳ Synced"},
        "idle": {"fg_color": COLORS["text_tertiary"], "text": "○ Idle"},
    }

    def __init__(self, master: ctk.CTkFrame, status: str = "idle", **kwargs):
        style = self.STATUS_STYLES.get(status, self.STATUS_STYLES["idle"])
        super().__init__(
            master,
            text=f"  {style['text']}  ",
            font=FONTS["body_xs"],
            text_color="#FFFFFF",
            fg_color=style["fg_color"],
            corner_radius=RADIUS["sm"],
            **kwargs,
        )


class SectionHeader(ctk.CTkFrame):
    """Section header with title and optional action button."""

    def __init__(self, master: ctk.CTkFrame, title: str,
                 button_text: str = "", button_command: Optional[Callable] = None,
                 **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        ctk.CTkLabel(
            self, text=title, font=FONTS["heading_md"],
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        if button_text and button_command:
            ctk.CTkButton(
                self, text=button_text, font=FONTS["button_sm"],
                fg_color=COLORS["accent_primary"],
                text_color=COLORS["text_on_accent"],
                hover_color=COLORS["accent_primary_hover"],
                corner_radius=RADIUS["md"],
                height=32, width=120,
                command=button_command,
            ).pack(side="right")


class ActivityItem(ctk.CTkFrame):
    """A single row in the recent activity feed."""

    def __init__(self, master: ctk.CTkFrame, icon: str, title: str,
                 subtitle: str, time_ago: str, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", height=48, **kwargs)
        self.pack_propagate(False)

        # Icon
        ctk.CTkLabel(
            self, text=icon, font=FONTS["body_lg"],
            text_color=COLORS["accent_primary"], width=30,
        ).pack(side="left", padx=(0, SPACING["sm"]))

        # Text
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            text_frame, text=title, font=FONTS["body_sm"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            text_frame, text=subtitle, font=FONTS["body_xs"],
            text_color=COLORS["text_tertiary"], anchor="w",
        ).pack(fill="x")

        # Timestamp
        ctk.CTkLabel(
            self, text=time_ago, font=FONTS["body_xs"],
            text_color=COLORS["text_tertiary"],
        ).pack(side="right")


class EmptyState(ctk.CTkFrame):
    """Placeholder for empty screens/sections with icon and message."""

    def __init__(self, master: ctk.CTkFrame, icon: str, title: str,
                 message: str = "", button_text: str = "",
                 button_command: Optional[Callable] = None, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        ctk.CTkLabel(
            self, text=icon, font=("Segoe UI", 48),
            text_color=COLORS["text_tertiary"],
        ).pack(pady=(SPACING["xxl"], SPACING["md"]))

        ctk.CTkLabel(
            self, text=title, font=FONTS["heading_md"],
            text_color=COLORS["text_secondary"],
        ).pack()

        if message:
            ctk.CTkLabel(
                self, text=message, font=FONTS["body_sm"],
                text_color=COLORS["text_tertiary"],
                wraplength=400,
            ).pack(pady=(SPACING["sm"], 0))

        if button_text and button_command:
            ctk.CTkButton(
                self, text=button_text, font=FONTS["button"],
                fg_color=COLORS["accent_primary"],
                text_color=COLORS["text_on_accent"],
                hover_color=COLORS["accent_primary_hover"],
                corner_radius=RADIUS["md"],
                height=40, width=180,
                command=button_command,
            ).pack(pady=(SPACING["lg"], 0))
