"""
CheckPoint — Helper utilities.

General-purpose formatting, hashing, and convenience functions
used across the application.
"""

import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


def format_bytes(size_bytes: int) -> str:
    """
    Format a byte count into a human-readable string.

    Args:
        size_bytes: Number of bytes.

    Returns:
        Formatted string like '1.23 GB', '456.7 MB', etc.
    """
    if size_bytes < 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024.0:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_timestamp(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime into a display string.

    Args:
        dt: The datetime to format. If None, uses current time.
        fmt: strftime format string.

    Returns:
        Formatted timestamp string.
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def get_backup_timestamp() -> str:
    """Return a filename-safe timestamp string like '2026-05-23_18-30'."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M")


def calculate_dir_size(directory: Path) -> int:
    """
    Calculate the total size in bytes of all files in a directory tree.

    Args:
        directory: Path to the directory.

    Returns:
        Total size in bytes.
    """
    total = 0
    if not directory.exists():
        return 0
    try:
        for entry in directory.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
    except PermissionError:
        pass
    return total


def calculate_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """
    Calculate a hash checksum for a file.

    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm name (sha256, md5, etc.).

    Returns:
        Hex digest string of the checksum.
    """
    hasher = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def time_ago(dt: datetime) -> str:
    """
    Return a human-readable 'time ago' string.

    Args:
        dt: The past datetime.

    Returns:
        String like '5 minutes ago', '2 hours ago', '3 days ago'.
    """
    now = datetime.now()
    delta = now - dt
    seconds = int(delta.total_seconds())

    if seconds < 0:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours}h ago"
    if seconds < 2592000:
        days = seconds // 86400
        return f"{days}d ago"
    if seconds < 31536000:
        months = seconds // 2592000
        return f"{months}mo ago"
    years = seconds // 31536000
    return f"{years}y ago"


def safe_game_folder_name(game_name: str) -> str:
    """
    Convert a game name to a safe folder name for backup storage.

    Args:
        game_name: The game's display name.

    Returns:
        A filesystem-safe folder name.
    """
    safe = re.sub(r'[<>:"/\\|?*]', "", game_name)
    safe = safe.strip(". ")
    safe = re.sub(r"\s+", " ", safe)
    return safe if safe else "Unknown Game"


def get_file_count(directory: Path) -> int:
    """
    Count the number of files in a directory tree.

    Args:
        directory: Path to scan.

    Returns:
        Total file count.
    """
    if not directory.exists():
        return 0
    count = 0
    try:
        for entry in directory.rglob("*"):
            if entry.is_file():
                count += 1
    except PermissionError:
        pass
    return count


def truncate_path(path: str, max_length: int = 50) -> str:
    """
    Truncate a file path for display, keeping the start and end.

    Args:
        path: The full path string.
        max_length: Maximum display length.

    Returns:
        Truncated path with '...' in the middle if needed.
    """
    if len(path) <= max_length:
        return path
    keep = (max_length - 3) // 2
    return path[:keep] + "..." + path[-keep:]
