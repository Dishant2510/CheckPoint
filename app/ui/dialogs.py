"""
CheckPoint — Dialog windows.

Modal dialogs for adding games, confirming actions, restoring
backups, and safe game deletion.
"""

from __future__ import annotations

import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from typing import Optional, Callable

from app.ui.theme import COLORS, FONTS, SPACING, RADIUS, ICONS


class AddGameDialog(ctk.CTkToplevel):
    """
    Dialog for adding a new game to the library.

    Provides fields for game name, executable path, save path,
    and launcher type with file/folder browse buttons.
    """

    def __init__(self, master: ctk.CTk,
                 on_submit: Optional[Callable[[dict], None]] = None,
                 **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.title("Add Game — CheckPoint")
        self.geometry("520x560")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_primary"])
        self.transient(master)
        self.grab_set()

        self._on_submit = on_submit
        self._result: Optional[dict] = None

        self._build_ui()
        self.after(100, self._center_on_parent)

    def _center_on_parent(self) -> None:
        """Center the dialog over the parent window."""
        self.update_idletasks()
        parent = self.master
        px = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build_ui(self) -> None:
        """Construct the dialog UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text=f"{ICONS['add']}  Add New Game",
            font=FONTS["heading_md"], text_color=COLORS["text_primary"],
        ).pack(side="left", padx=SPACING["lg"])

        # Form body
        body = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["scrollbar_thumb"],
        )
        body.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["lg"])

        # Game Name
        self._name_entry = self._create_field(body, "Game Name *",
                                               "e.g. Elden Ring")

        # Executable Path
        exe_frame = ctk.CTkFrame(body, fg_color="transparent")
        exe_frame.pack(fill="x", pady=(SPACING["md"], 0))

        ctk.CTkLabel(
            exe_frame, text="Executable Path", font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w")

        exe_row = ctk.CTkFrame(exe_frame, fg_color="transparent")
        exe_row.pack(fill="x", pady=(SPACING["xs"], 0))

        self._exe_entry = ctk.CTkEntry(
            exe_row, font=FONTS["body_md"],
            fg_color=COLORS["bg_input"], border_color=COLORS["border_primary"],
            text_color=COLORS["text_primary"],
            placeholder_text="Browse or paste path...",
            height=38,
        )
        self._exe_entry.pack(side="left", fill="x", expand=True, padx=(0, SPACING["sm"]))

        ctk.CTkButton(
            exe_row, text="Browse", font=FONTS["button_sm"],
            fg_color=COLORS["bg_tertiary"], text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_hover"], width=70, height=38,
            corner_radius=RADIUS["md"],
            command=self._browse_exe,
        ).pack(side="right")

        # Save Path
        save_frame = ctk.CTkFrame(body, fg_color="transparent")
        save_frame.pack(fill="x", pady=(SPACING["md"], 0))

        ctk.CTkLabel(
            save_frame, text="Save File Location", font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w")

        save_row = ctk.CTkFrame(save_frame, fg_color="transparent")
        save_row.pack(fill="x", pady=(SPACING["xs"], 0))

        self._save_entry = ctk.CTkEntry(
            save_row, font=FONTS["body_md"],
            fg_color=COLORS["bg_input"], border_color=COLORS["border_primary"],
            text_color=COLORS["text_primary"],
            placeholder_text="Auto-detect or browse...",
            height=38,
        )
        self._save_entry.pack(side="left", fill="x", expand=True, padx=(0, SPACING["sm"]))

        ctk.CTkButton(
            save_row, text="Browse", font=FONTS["button_sm"],
            fg_color=COLORS["bg_tertiary"], text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_hover"], width=70, height=38,
            corner_radius=RADIUS["md"],
            command=self._browse_save,
        ).pack(side="right")

        # Install Path
        install_frame = ctk.CTkFrame(body, fg_color="transparent")
        install_frame.pack(fill="x", pady=(SPACING["md"], 0))

        ctk.CTkLabel(
            install_frame, text="Install Directory", font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w")

        install_row = ctk.CTkFrame(install_frame, fg_color="transparent")
        install_row.pack(fill="x", pady=(SPACING["xs"], 0))

        self._install_entry = ctk.CTkEntry(
            install_row, font=FONTS["body_md"],
            fg_color=COLORS["bg_input"], border_color=COLORS["border_primary"],
            text_color=COLORS["text_primary"],
            placeholder_text="Optional — game install folder",
            height=38,
        )
        self._install_entry.pack(side="left", fill="x", expand=True, padx=(0, SPACING["sm"]))

        ctk.CTkButton(
            install_row, text="Browse", font=FONTS["button_sm"],
            fg_color=COLORS["bg_tertiary"], text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_hover"], width=70, height=38,
            corner_radius=RADIUS["md"],
            command=self._browse_install,
        ).pack(side="right")

        # Launcher Type
        launcher_frame = ctk.CTkFrame(body, fg_color="transparent")
        launcher_frame.pack(fill="x", pady=(SPACING["md"], 0))

        ctk.CTkLabel(
            launcher_frame, text="Launcher", font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w")

        self._launcher_var = ctk.StringVar(value="unknown")
        self._launcher_menu = ctk.CTkOptionMenu(
            launcher_frame,
            values=["steam", "epic", "emulator", "offline", "unknown"],
            variable=self._launcher_var,
            font=FONTS["body_md"],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["bg_tertiary"],
            button_hover_color=COLORS["bg_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            dropdown_hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"],
            height=38,
            corner_radius=RADIUS["md"],
        )
        self._launcher_menu.pack(fill="x", pady=(SPACING["xs"], 0))

        # Notes
        self._notes_entry = self._create_field(body, "Notes", "Optional notes...")

        # Footer buttons
        footer = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=60)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer, text="Cancel", font=FONTS["button"],
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_hover"],
            height=36, width=100,
            corner_radius=RADIUS["md"],
            command=self.destroy,
        ).pack(side="right", padx=SPACING["sm"], pady=SPACING["md"])

        ctk.CTkButton(
            footer, text="Add Game", font=FONTS["button"],
            fg_color=COLORS["accent_primary"],
            text_color=COLORS["text_on_accent"],
            hover_color=COLORS["accent_primary_hover"],
            height=36, width=120,
            corner_radius=RADIUS["md"],
            command=self._submit,
        ).pack(side="right", pady=SPACING["md"])

    def _create_field(self, parent: ctk.CTkFrame, label: str,
                      placeholder: str = "") -> ctk.CTkEntry:
        """Create a labeled text input field."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(SPACING["md"], 0))

        ctk.CTkLabel(
            frame, text=label, font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w")

        entry = ctk.CTkEntry(
            frame, font=FONTS["body_md"],
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border_primary"],
            text_color=COLORS["text_primary"],
            placeholder_text=placeholder,
            height=38,
        )
        entry.pack(fill="x", pady=(SPACING["xs"], 0))
        return entry

    def _browse_exe(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Game Executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if path:
            self._exe_entry.delete(0, "end")
            self._exe_entry.insert(0, path)

    def _browse_save(self) -> None:
        path = filedialog.askdirectory(title="Select Save File Location")
        if path:
            self._save_entry.delete(0, "end")
            self._save_entry.insert(0, path)

    def _browse_install(self) -> None:
        path = filedialog.askdirectory(title="Select Install Directory")
        if path:
            self._install_entry.delete(0, "end")
            self._install_entry.insert(0, path)

    def _submit(self) -> None:
        name = self._name_entry.get().strip()
        if not name:
            self._name_entry.configure(border_color=COLORS["accent_danger"])
            return

        result = {
            "name": name,
            "exe_path": self._exe_entry.get().strip(),
            "save_path": self._save_entry.get().strip(),
            "install_path": self._install_entry.get().strip(),
            "launcher_type": self._launcher_var.get(),
            "notes": self._notes_entry.get().strip(),
        }

        if self._on_submit:
            self._on_submit(result)
        self.destroy()


class ConfirmDialog(ctk.CTkToplevel):
    """
    Simple confirmation dialog with Yes/No buttons.

    Used for delete confirmations and irreversible actions.
    """

    def __init__(self, master: ctk.CTk, title: str, message: str,
                 confirm_text: str = "Confirm",
                 cancel_text: str = "Cancel",
                 on_confirm: Optional[Callable[[], None]] = None,
                 danger: bool = False, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.title(title)
        self.geometry("420x200")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_primary"])
        self.transient(master)
        self.grab_set()

        self._on_confirm = on_confirm

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        icon = ICONS["warning"] if danger else ICONS["info"]
        ctk.CTkLabel(
            content, text=icon, font=("Segoe UI", 36),
            text_color=COLORS["accent_danger"] if danger else COLORS["accent_primary"],
        ).pack()

        ctk.CTkLabel(
            content, text=message, font=FONTS["body_md"],
            text_color=COLORS["text_primary"], wraplength=360,
        ).pack(pady=(SPACING["md"], 0))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))

        btn_color = COLORS["accent_danger"] if danger else COLORS["accent_primary"]
        btn_hover = COLORS["accent_danger_hover"] if danger else COLORS["accent_primary_hover"]

        ctk.CTkButton(
            btn_frame, text=cancel_text, font=FONTS["button"],
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_hover"], height=36, width=100,
            corner_radius=RADIUS["md"],
            command=self.destroy,
        ).pack(side="right", padx=(SPACING["sm"], 0))

        ctk.CTkButton(
            btn_frame, text=confirm_text, font=FONTS["button"],
            fg_color=btn_color, text_color="#FFFFFF",
            hover_color=btn_hover, height=36, width=120,
            corner_radius=RADIUS["md"],
            command=self._confirm,
        ).pack(side="right")

        self.after(100, self._center_on_parent)

    def _center_on_parent(self) -> None:
        self.update_idletasks()
        parent = self.master
        px = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _confirm(self) -> None:
        if self._on_confirm:
            self._on_confirm()
        self.destroy()


class RestoreDialog(ctk.CTkToplevel):
    """
    Dialog for selecting a backup to restore.

    Shows backup metadata and allows choosing original or custom path.
    """

    def __init__(self, master: ctk.CTk, backups: list,
                 on_restore: Optional[Callable[[int, Optional[str]], None]] = None,
                 **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.title("Restore Backup — CheckPoint")
        self.geometry("500x450")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_primary"])
        self.transient(master)
        self.grab_set()

        self._on_restore = on_restore
        self._backups = backups
        self._selected_id: Optional[int] = None
        self._custom_path: Optional[str] = None

        self._build_ui()
        self.after(100, self._center_on_parent)

    def _center_on_parent(self) -> None:
        self.update_idletasks()
        parent = self.master
        px = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build_ui(self) -> None:
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text=f"{ICONS['restore']}  Restore Backup",
            font=FONTS["heading_sm"], text_color=COLORS["text_primary"],
        ).pack(side="left", padx=SPACING["lg"])

        # Backup list
        list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["scrollbar_thumb"],
        )
        list_frame.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["md"])

        self._radio_var = ctk.IntVar(value=-1)

        for i, backup in enumerate(self._backups):
            from app.utils.helpers import format_bytes
            row = ctk.CTkFrame(list_frame, fg_color=COLORS["bg_card"],
                               corner_radius=RADIUS["md"])
            row.pack(fill="x", pady=SPACING["xs"])

            rb = ctk.CTkRadioButton(
                row, text="", variable=self._radio_var, value=i,
                fg_color=COLORS["accent_primary"],
                border_color=COLORS["border_primary"],
                hover_color=COLORS["accent_primary_hover"],
            )
            rb.pack(side="left", padx=SPACING["md"], pady=SPACING["sm"])

            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, pady=SPACING["sm"])

            ctk.CTkLabel(
                info_frame, text=backup.backup_name,
                font=FONTS["body_sm"], text_color=COLORS["text_primary"],
                anchor="w",
            ).pack(fill="x")

            meta_text = f"{backup.created_at}  •  {format_bytes(backup.size_bytes)}"
            ctk.CTkLabel(
                info_frame, text=meta_text,
                font=FONTS["body_xs"], text_color=COLORS["text_tertiary"],
                anchor="w",
            ).pack(fill="x")

        # Custom path option
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.pack(fill="x", padx=SPACING["lg"], pady=(0, SPACING["sm"]))

        self._use_custom = ctk.CTkCheckBox(
            path_frame, text="Restore to custom path",
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"],
            fg_color=COLORS["accent_primary"],
            border_color=COLORS["border_primary"],
            hover_color=COLORS["accent_primary_hover"],
            command=self._toggle_custom_path,
        )
        self._use_custom.pack(side="left")

        self._path_entry = ctk.CTkEntry(
            path_frame, font=FONTS["body_sm"],
            fg_color=COLORS["bg_input"], border_color=COLORS["border_primary"],
            text_color=COLORS["text_primary"], height=32,
            state="disabled", placeholder_text="Select folder...",
        )
        self._path_entry.pack(side="left", fill="x", expand=True, padx=(SPACING["sm"], SPACING["sm"]))

        ctk.CTkButton(
            path_frame, text="...", width=32, height=32,
            font=FONTS["button_sm"],
            fg_color=COLORS["bg_tertiary"], text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_hover"], corner_radius=RADIUS["sm"],
            command=self._browse_custom,
        ).pack(side="right")

        # Footer
        footer = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=50)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer, text="Cancel", font=FONTS["button"],
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_hover"], height=36, width=90,
            corner_radius=RADIUS["md"],
            command=self.destroy,
        ).pack(side="right", padx=SPACING["sm"], pady=SPACING["sm"])

        ctk.CTkButton(
            footer, text="Restore", font=FONTS["button"],
            fg_color=COLORS["accent_primary"],
            text_color=COLORS["text_on_accent"],
            hover_color=COLORS["accent_primary_hover"],
            height=36, width=100,
            corner_radius=RADIUS["md"],
            command=self._do_restore,
        ).pack(side="right", pady=SPACING["sm"])

    def _toggle_custom_path(self) -> None:
        if self._use_custom.get():
            self._path_entry.configure(state="normal")
        else:
            self._path_entry.configure(state="disabled")

    def _browse_custom(self) -> None:
        path = filedialog.askdirectory(title="Select Restore Location")
        if path:
            self._path_entry.configure(state="normal")
            self._path_entry.delete(0, "end")
            self._path_entry.insert(0, path)
            self._use_custom.select()

    def _do_restore(self) -> None:
        idx = self._radio_var.get()
        if idx < 0 or idx >= len(self._backups):
            return

        backup = self._backups[idx]
        custom = None
        if self._use_custom.get():
            custom = self._path_entry.get().strip() or None

        if self._on_restore:
            self._on_restore(backup.id, custom)
        self.destroy()


class SafeDeleteDialog(ctk.CTkToplevel):
    """
    Safe delete flow dialog.

    Warns user about save files, offers backup before deletion,
    and requires explicit confirmation.
    """

    def __init__(self, master: ctk.CTk, game_name: str,
                 has_saves: bool = True,
                 on_backup_and_delete: Optional[Callable[[], None]] = None,
                 on_delete_only: Optional[Callable[[], None]] = None,
                 **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.title("Safe Delete — CheckPoint")
        self.geometry("460x320")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_primary"])
        self.transient(master)
        self.grab_set()

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        # Warning icon
        ctk.CTkLabel(
            content, text="⚠", font=("Segoe UI", 48),
            text_color=COLORS["accent_warning"],
        ).pack()

        ctk.CTkLabel(
            content, text=f"Delete '{game_name}'?",
            font=FONTS["heading_md"], text_color=COLORS["text_primary"],
        ).pack(pady=(SPACING["sm"], 0))

        if has_saves:
            ctk.CTkLabel(
                content,
                text="Save files were detected for this game.\n"
                     "Would you like to back them up before removing?",
                font=FONTS["body_md"], text_color=COLORS["text_secondary"],
                wraplength=380, justify="center",
            ).pack(pady=(SPACING["md"], 0))

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(SPACING["xl"], 0))

        if has_saves and on_backup_and_delete:
            ctk.CTkButton(
                btn_frame, text="Backup & Delete",
                font=FONTS["button"],
                fg_color=COLORS["accent_primary"],
                text_color=COLORS["text_on_accent"],
                hover_color=COLORS["accent_primary_hover"],
                height=38, corner_radius=RADIUS["md"],
                command=lambda: (on_backup_and_delete(), self.destroy()),
            ).pack(fill="x", pady=(0, SPACING["sm"]))

        if on_delete_only:
            ctk.CTkButton(
                btn_frame, text="Delete Without Backup",
                font=FONTS["button"],
                fg_color=COLORS["accent_danger"],
                text_color="#FFFFFF",
                hover_color=COLORS["accent_danger_hover"],
                height=38, corner_radius=RADIUS["md"],
                command=lambda: (on_delete_only(), self.destroy()),
            ).pack(fill="x", pady=(0, SPACING["sm"]))

        ctk.CTkButton(
            btn_frame, text="Cancel", font=FONTS["button"],
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_hover"],
            height=38, corner_radius=RADIUS["md"],
            command=self.destroy,
        ).pack(fill="x")

        self.after(100, self._center_on_parent)

    def _center_on_parent(self) -> None:
        self.update_idletasks()
        parent = self.master
        px = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
