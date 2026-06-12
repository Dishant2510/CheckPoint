"""
CheckPoint — Path utilities.

Provides OS-aware resolution for common game save directories,
application data paths, and Steam/Epic installation folders.
"""

import os
import platform
import sys
from pathlib import Path
from typing import Optional


def is_frozen() -> bool:
    """Check if the application is running in a frozen bundle (e.g. PyInstaller)."""
    return getattr(sys, "frozen", False)


def get_app_root() -> Path:
    """Return the root directory of the CheckPoint application."""
    if is_frozen():
        # When frozen, sys.executable points to the .exe itself (e.g. C:\Program Files\CheckPoint\CheckPoint.exe).
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


def get_data_dir() -> Path:
    """Return the data directory for database and config files."""
    if is_frozen():
        # In frozen mode, write configurations and databases to AppData/Local/CheckPoint/data
        # to prevent permission errors when running from Program Files.
        data_dir = get_appdata_local() / "CheckPoint" / "data"
    else:
        # Development mode: write to project folder
        data_dir = get_app_root() / "data"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """Return the logs directory."""
    if is_frozen():
        # In frozen mode, write logs to AppData/Local/CheckPoint/logs
        logs_dir = get_appdata_local() / "CheckPoint" / "logs"
    else:
        logs_dir = get_app_root() / "logs"
    
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_default_backup_dir() -> Path:
    """Return the default backups directory."""
    if is_frozen():
        # A clean default for general users is Documents/CheckPoint/Backups
        backup_dir = get_documents_dir() / "CheckPoint" / "Backups"
    else:
        backup_dir = get_app_root() / "backups"
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_user_home() -> Path:
    """Return the current user's home directory."""
    return Path.home()


def get_documents_dir() -> Path:
    """Return the user's Documents folder."""
    if platform.system() == "Windows":
        docs = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documents"
    else:
        docs = Path.home() / "Documents"
    return docs


def get_saved_games_dir() -> Path:
    """Return the user's Saved Games folder (Windows-specific)."""
    if platform.system() == "Windows":
        return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Saved Games"
    return Path.home() / ".local" / "share" / "saved_games"


def get_appdata_local() -> Path:
    """Return AppData/Local directory."""
    if platform.system() == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    return Path.home() / ".local" / "share"


def get_appdata_roaming() -> Path:
    """Return AppData/Roaming directory."""
    if platform.system() == "Windows":
        return Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
    return Path.home() / ".config"


def get_steam_root() -> Optional[Path]:
    """
    Attempt to locate the Steam installation directory.

    Checks common installation paths on Windows.
    Returns None if Steam is not found.
    """
    if platform.system() != "Windows":
        linux_paths = [
            Path.home() / ".steam" / "steam",
            Path.home() / ".local" / "share" / "Steam",
        ]
        for p in linux_paths:
            if p.exists():
                return p
        return None

    common_paths = [
        Path("C:/Program Files (x86)/Steam"),
        Path("C:/Program Files/Steam"),
        Path("D:/Steam"),
        Path("D:/SteamLibrary"),
        Path("E:/Steam"),
        Path("E:/SteamLibrary"),
    ]

    for steam_path in common_paths:
        if steam_path.exists():
            return steam_path

    # Check registry as fallback
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\WOW6432Node\Valve\Steam")
        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
        winreg.CloseKey(key)
        steam_dir = Path(install_path)
        if steam_dir.exists():
            return steam_dir
    except (OSError, FileNotFoundError, ImportError):
        pass

    return None


def get_steam_userdata_dir() -> Optional[Path]:
    """Return the Steam userdata directory containing per-user saves."""
    steam_root = get_steam_root()
    if steam_root:
        userdata = steam_root / "userdata"
        if userdata.exists():
            return userdata
    return None


def get_epic_games_root() -> Optional[Path]:
    """Attempt to locate the Epic Games installation directory."""
    if platform.system() != "Windows":
        return None

    common_paths = [
        Path("C:/Program Files/Epic Games"),
        Path("C:/Program Files (x86)/Epic Games"),
        Path("D:/Epic Games"),
        Path("E:/Epic Games"),
    ]

    for epic_path in common_paths:
        if epic_path.exists():
            return epic_path

    return None


def get_emulator_dirs() -> list[Path]:
    """
    Return a list of common emulator save directories.

    Scans for RetroArch, Dolphin, PCSX2, RPCS3, Cemu, Yuzu, Ryujinx.
    """
    dirs: list[Path] = []
    appdata_roaming = get_appdata_roaming()
    appdata_local = get_appdata_local()
    documents = get_documents_dir()

    emulator_paths = [
        appdata_roaming / "RetroArch" / "saves",
        appdata_roaming / "RetroArch" / "states",
        documents / "Dolphin Emulator" / "StateSaves",
        documents / "Dolphin Emulator" / "GC",
        documents / "Dolphin Emulator" / "Wii",
        appdata_local / "PCSX2" / "sstates",
        appdata_local / "PCSX2" / "memcards",
        appdata_roaming / "RPCS3" / "dev_hdd0" / "home",
        appdata_local / "Cemu" / "mlc01",
        appdata_roaming / "yuzu" / "nand",
        appdata_roaming / "Ryujinx" / "bis" / "user" / "save",
    ]

    for emu_path in emulator_paths:
        if emu_path.exists():
            dirs.append(emu_path)

    return dirs


def get_common_save_directories() -> list[Path]:
    """
    Return all common directories where game saves may be stored.

    This is used by the save detector to scan for save files.
    """
    dirs: list[Path] = []

    # Standard user directories
    for getter in [get_documents_dir, get_saved_games_dir,
                   get_appdata_local, get_appdata_roaming]:
        d = getter()
        if d.exists():
            dirs.append(d)

    # Steam userdata
    steam_ud = get_steam_userdata_dir()
    if steam_ud:
        dirs.append(steam_ud)

    # Emulator directories
    dirs.extend(get_emulator_dirs())

    return dirs


def sanitize_filename(name: str) -> str:
    """
    Convert a string into a safe filename by removing/replacing invalid characters.

    Args:
        name: The original string.

    Returns:
        A sanitized filename string.
    """
    invalid_chars = '<>:"/\\|?*'
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, "_")
    sanitized = sanitized.strip(". ")
    return sanitized if sanitized else "unnamed"
