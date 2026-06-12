"""
CheckPoint — Platform scanner.

Discovers installed games from Steam, Epic Games Store, and common
emulator installations by reading platform-specific manifests and
directory structures.
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

from app.utils.paths import (
    get_steam_root,
    get_steam_userdata_dir,
    get_epic_games_root,
    get_appdata_local,
    get_documents_dir,
)
from app.utils.logger import get_logger

logger = get_logger("scanners.platform")


def scan_steam_library() -> list[dict]:
    """
    Scan Steam for installed games.

    Reads libraryfolders.vdf and appmanifest files to discover
    installed Steam games with their install paths.

    Returns:
        List of dicts with keys: name, install_path, launcher, app_id.
    """
    games: list[dict] = []
    steam_root = get_steam_root()
    if not steam_root:
        logger.info("Steam not found on this system")
        return games

    library_folders = _get_steam_library_folders(steam_root)
    logger.info("Found %d Steam library folders", len(library_folders))

    for lib_folder in library_folders:
        steamapps = lib_folder / "steamapps"
        if not steamapps.exists():
            continue

        for manifest_file in steamapps.glob("appmanifest_*.acf"):
            try:
                game_info = _parse_acf_manifest(manifest_file, steamapps)
                if game_info:
                    games.append(game_info)
            except Exception as e:
                logger.warning("Failed to parse %s: %s", manifest_file.name, e)

    logger.info("Discovered %d Steam games", len(games))
    return games


def _get_steam_library_folders(steam_root: Path) -> list[Path]:
    """Parse libraryfolders.vdf to find all Steam library locations."""
    folders: list[Path] = [steam_root]
    vdf_path = steam_root / "steamapps" / "libraryfolders.vdf"

    if not vdf_path.exists():
        return folders

    try:
        with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Match "path" entries in the VDF file
        path_matches = re.findall(r'"path"\s+"([^"]+)"', content)
        for match in path_matches:
            lib_path = Path(match.replace("\\\\", "\\"))
            if lib_path.exists() and lib_path not in folders:
                folders.append(lib_path)
    except OSError as e:
        logger.warning("Failed to read libraryfolders.vdf: %s", e)

    return folders


def _parse_acf_manifest(manifest_path: Path, steamapps_dir: Path) -> Optional[dict]:
    """Parse a Steam appmanifest ACF file to extract game info."""
    try:
        with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return None

    name_match = re.search(r'"name"\s+"([^"]+)"', content)
    appid_match = re.search(r'"appid"\s+"(\d+)"', content)
    installdir_match = re.search(r'"installdir"\s+"([^"]+)"', content)

    if not name_match or not appid_match or not installdir_match:
        return None

    name = name_match.group(1)
    app_id = appid_match.group(1)
    install_dir = installdir_match.group(1)

    # Skip tools, redistributables, Proton, etc.
    skip_names = [
        "Steamworks Common Redistributables",
        "Proton", "Steam Linux Runtime",
    ]
    if any(skip in name for skip in skip_names):
        return None

    install_path = steamapps_dir / "common" / install_dir

    return {
        "name": name,
        "install_path": str(install_path),
        "launcher": "steam",
        "app_id": app_id,
    }


def scan_epic_games() -> list[dict]:
    """
    Scan Epic Games Store for installed games.

    Reads .item manifest files from the Epic launcher's manifests directory.

    Returns:
        List of dicts with keys: name, install_path, launcher.
    """
    games: list[dict] = []
    manifests_dir = get_appdata_local() / "EpicGamesLauncher" / "Saved" / "Config" / "Windows"

    # Epic stores manifests in ProgramData
    epic_manifests = Path("C:/ProgramData/Epic/EpicGamesLauncher/Data/Manifests")

    if not epic_manifests.exists():
        logger.info("Epic Games manifests directory not found")
        return games

    for manifest_file in epic_manifests.glob("*.item"):
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            name = data.get("DisplayName", "")
            install_path = data.get("InstallLocation", "")

            if name and install_path:
                games.append({
                    "name": name,
                    "install_path": install_path,
                    "launcher": "epic",
                })
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to parse Epic manifest %s: %s",
                           manifest_file.name, e)

    logger.info("Discovered %d Epic Games", len(games))
    return games


def scan_emulators() -> list[dict]:
    """
    Scan for common emulator installations.

    Checks for RetroArch, Dolphin, PCSX2, RPCS3, Cemu, Yuzu, Ryujinx.

    Returns:
        List of dicts with keys: name, install_path, launcher, emulator_type.
    """
    emulators: list[dict] = []
    appdata_roaming = Path(os.environ.get("APPDATA", ""))
    appdata_local = get_appdata_local()
    documents = get_documents_dir()

    emulator_checks = [
        ("RetroArch", appdata_roaming / "RetroArch", "retroarch"),
        ("Dolphin Emulator", documents / "Dolphin Emulator", "dolphin"),
        ("PCSX2", appdata_local / "PCSX2", "pcsx2"),
        ("RPCS3", appdata_roaming / "RPCS3", "rpcs3"),
        ("Cemu", appdata_local / "Cemu", "cemu"),
        ("Yuzu", appdata_roaming / "yuzu", "yuzu"),
        ("Ryujinx", appdata_roaming / "Ryujinx", "ryujinx"),
    ]

    for name, path, emu_type in emulator_checks:
        if path.exists():
            emulators.append({
                "name": name,
                "install_path": str(path),
                "launcher": "emulator",
                "emulator_type": emu_type,
            })
            logger.info("Found emulator: %s at %s", name, path)

    return emulators


def scan_all_platforms() -> list[dict]:
    """
    Scan all supported platforms for installed games.

    Returns:
        Combined list of discovered games from Steam, Epic, and emulators.
    """
    all_games: list[dict] = []
    all_games.extend(scan_steam_library())
    all_games.extend(scan_epic_games())
    all_games.extend(scan_emulators())
    logger.info("Total discovered across all platforms: %d", len(all_games))
    return all_games
