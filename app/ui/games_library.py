"""
CheckPoint — Games Library screen.

Searchable grid of game cards with add/scan functionality
and quick-action buttons per game.
"""

from __future__ import annotations

import customtkinter as ctk
from typing import Optional, TYPE_CHECKING

from app.ui.theme import COLORS, FONTS, SPACING, RADIUS, ICONS
from app.ui.components import GameCard, EmptyState, SectionHeader
from app.ui.dialogs import AddGameDialog
from app.services.game_service import GameService
from app.services.backup_service import BackupService
from app.database.models import Game
from app.utils.helpers import format_bytes
from app.utils.logger import get_logger

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = get_logger("ui.games_library")


class GamesLibraryScreen(ctk.CTkFrame):
    """
    Games Library — displays all registered games as a card grid.

    Features:
    - Search/filter bar
    - Add Game button
    - Scan for games button
    - Clickable game cards leading to game details
    """

    def __init__(self, master: ctk.CTkFrame, app: "MainWindow", **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._app = app
        self._game_service = GameService()
        self._backup_service = BackupService()
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the library layout."""
        # Header area
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        ctk.CTkLabel(
            header, text="Games Library", font=FONTS["heading_xl"],
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        # Action buttons
        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row, text=f"{ICONS['add']}  Add Game",
            font=FONTS["button"],
            fg_color=COLORS["accent_primary"],
            text_color=COLORS["text_on_accent"],
            hover_color=COLORS["accent_primary_hover"],
            height=36, width=130, corner_radius=RADIUS["md"],
            command=self._open_add_dialog,
        ).pack(side="left", padx=(0, SPACING["sm"]))

        ctk.CTkButton(
            btn_row, text=f"{ICONS['search']}  Scan",
            font=FONTS["button"],
            fg_color=COLORS["bg_tertiary"],
            text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_hover"],
            height=36, width=100, corner_radius=RADIUS["md"],
            command=self._scan_for_games,
        ).pack(side="left")

        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["md"]))

        self._search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text=f"{ICONS['search']}  Search games...",
            font=FONTS["body_md"],
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border_primary"],
            text_color=COLORS["text_primary"],
            height=40, corner_radius=RADIUS["md"],
        )
        self._search_entry.pack(fill="x")

        # Game grid (scrollable)
        self._grid_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["scrollbar_thumb"],
            scrollbar_button_hover_color=COLORS["scrollbar_thumb_hover"],
        )
        self._grid_scroll.pack(fill="both", expand=True, padx=SPACING["xl"],
                               pady=(0, SPACING["xl"]))

        self.refresh()

    def refresh(self, search_query: str = "") -> None:
        """Reload the game grid."""
        # Clear existing cards
        for widget in self._grid_scroll.winfo_children():
            widget.destroy()

        if search_query:
            games = self._game_service.search_games(search_query)
        else:
            games = self._game_service.get_all_games()

        if not games:
            EmptyState(
                self._grid_scroll,
                icon=ICONS["games"],
                title="No Games Found",
                message="Add your first game or scan for installed games.",
                button_text="Add Game",
                button_command=self._open_add_dialog,
            ).pack(fill="both", expand=True)
            return

        # Configure grid columns
        self._grid_scroll.columnconfigure((0, 1, 2), weight=1, uniform="game")

        for i, game in enumerate(games):
            row = i // 3
            col = i % 3

            # Determine save status
            save_status = "Save path set" if game.save_path else "No saves"
            last_backup = game.last_backed_up or "Never"

            card = GameCard(
                self._grid_scroll,
                game_name=game.name,
                launcher=game.launcher_type,
                save_status=save_status,
                last_backup=last_backup,
                on_click=lambda gid=game.id: self._open_game_details(gid),
            )
            card.grid(row=row, column=col, sticky="nsew",
                      padx=SPACING["sm"], pady=SPACING["sm"])

    def _on_search(self, *args) -> None:
        """Handle search input changes."""
        query = self._search_var.get().strip()
        self.refresh(search_query=query)

    def _open_add_dialog(self) -> None:
        """Open the Add Game dialog."""
        AddGameDialog(
            self._app,
            on_submit=self._handle_add_game,
        )

    def _handle_add_game(self, data: dict) -> None:
        """Process the Add Game form submission."""
        try:
            self._game_service.add_game(
                name=data["name"],
                install_path=data.get("install_path", ""),
                save_path=data.get("save_path", ""),
                exe_path=data.get("exe_path", ""),
                launcher_type=data.get("launcher_type", "unknown"),
                notes=data.get("notes", ""),
            )
            self.refresh()
            logger.info("Game added via dialog: %s", data["name"])
        except Exception as e:
            logger.error("Failed to add game: %s", e)

    def _scan_for_games(self) -> None:
        """Scan for installed games across platforms."""
        try:
            from app.scanners.platform_scanner import scan_all_platforms
            discovered = scan_all_platforms()

            existing_names = {g.name.lower() for g in self._game_service.get_all_games()}
            added = 0

            for game_info in discovered:
                if game_info["name"].lower() not in existing_names:
                    self._game_service.add_game(
                        name=game_info["name"],
                        install_path=game_info.get("install_path", ""),
                        launcher_type=game_info.get("launcher", "unknown"),
                    )
                    added += 1

            self.refresh()
            logger.info("Scan complete: %d new games found", added)
        except Exception as e:
            logger.error("Scan failed: %s", e)

    def _open_game_details(self, game_id: int) -> None:
        """Navigate to the game details screen."""
        self._app.show_game_details(game_id)
