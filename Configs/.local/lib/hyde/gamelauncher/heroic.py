#!/usr/bin/env python3
"""
Heroic Games Launcher inspector for gamelauncher.sh

- Reads Heroic's install records for Epic (legendary), GOG, Amazon (nile) and
  sideloaded games, from the native or flatpak config directory
- Lists only games whose install folder still exists
- Takes titles and covers from Heroic's store cache; covers are files in
  images-cache named by the sha256 of the image URL
- CLI:
    --detect      -> print the Heroic config directories found (JSON)
    --json        -> print JSON list of installed games
    --rofi-string -> print rofi-formatted lines
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# gamelauncher.sh runs run_command with `eval exec`, so only ids shaped like the
# ones the stores issue (Epic names, GOG numbers, Amazon amzn1.adg... ids) are
# embedded in the launch URL; anything else is skipped rather than quoted.
_SAFE_ID = re.compile(r"[A-Za-z0-9._-]+")

CONFIG_DIRS = [
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "heroic",
    Path.home() / ".var" / "app" / "com.heroicgameslauncher.hgl" / "config" / "heroic",
]

# Store cache file and the key holding its list, per runner
STORE_CACHE = {
    "legendary": ("legendary_library.json", "library"),
    "gog": ("gog_library.json", "games"),
    "nile": ("nile_library.json", "library"),
}


def read_json(path: Path):
    try:
        return json.loads(path.read_text(errors="ignore"))
    except (OSError, ValueError):
        return None


def find_configs() -> List[Path]:
    return [d for d in CONFIG_DIRS if d.is_dir()]


def store_entries(config: Path, runner: str) -> Dict[str, Dict]:
    """Store cache entries for a runner, keyed by app name."""
    filename, key = STORE_CACHE[runner]
    data = read_json(config / "store_cache" / filename)
    entries = data.get(key, []) if isinstance(data, dict) else data if isinstance(data, list) else []
    return {e["app_name"]: e for e in entries if isinstance(e, dict) and e.get("app_name")}


def installed_records(config: Path) -> List[Dict]:
    """(runner, app name, install path, title) for every install record Heroic keeps."""
    records = []

    legendary = read_json(config / "legendaryConfig" / "legendary" / "installed.json")
    if isinstance(legendary, dict):
        for app, info in legendary.items():
            if isinstance(info, dict):
                records.append({"runner": "legendary", "app": app, "path": info.get("install_path"), "title": info.get("title")})

    gog = read_json(config / "gog_store" / "installed.json")
    for info in gog.get("installed", []) if isinstance(gog, dict) else []:
        if isinstance(info, dict) and not info.get("is_dlc"):
            records.append({"runner": "gog", "app": info.get("appName"), "path": info.get("install_path"), "title": None})

    nile = read_json(config / "nile_config" / "nile" / "installed.json")
    for info in nile if isinstance(nile, list) else []:
        if isinstance(info, dict):
            records.append({"runner": "nile", "app": info.get("id"), "path": info.get("path"), "title": None})

    # Sideloaded apps have no install folder of their own, only an executable
    sideload = read_json(config / "sideload_apps" / "library.json")
    for info in sideload.get("games", []) if isinstance(sideload, dict) else []:
        if isinstance(info, dict) and info.get("is_installed"):
            executable = (info.get("install") or {}).get("executable")
            records.append({
                "runner": "sideload",
                "app": info.get("app_name"),
                "path": str(Path(executable).parent) if executable else None,
                "title": info.get("title"),
                "art": [info.get("art_square"), info.get("art_cover")],
            })
    return records


def cached_cover(config: Path, urls: List[Optional[str]]) -> str:
    """First of the given image URLs that Heroic has already cached, portrait art first."""
    for url in urls:
        if url:
            path = config / "images-cache" / hashlib.sha256(url.encode()).hexdigest()
            if path.is_file():
                return str(path)
    return ""


def list_games(config: Path) -> List[Dict]:
    stores = {runner: store_entries(config, runner) for runner in STORE_CACHE}
    games = []
    for rec in installed_records(config):
        app, runner = rec["app"] or "", rec["runner"]
        if not _SAFE_ID.fullmatch(app):
            print(f"Skipping {app!r}: not a plain store id, refusing to embed it in a shell command", file=sys.stderr)
            continue
        # Heroic can keep a record after the files are gone, like Steam does with manifests
        if not rec["path"] or not Path(rec["path"]).is_dir():
            continue
        store = stores.get(runner, {}).get(app, {})
        name = rec.get("title") or store.get("title") or app
        if "\t" in name or "\n" in name:
            continue
        cover = cached_cover(config, rec.get("art") or [store.get("art_square"), store.get("art_cover")])
        run_command = f"xdg-open 'heroic://launch?appName={app}&runner={runner}'"
        games.append({
            "id": app,
            "name": name,
            "slug": app,
            "runner": runner,
            "path": rec["path"],
            "icon": cover,
            "cover": cover,
            "run_command": run_command,
            "rofi_string": f"{name}\t{run_command}\t\x00icon\x1f{cover}" if cover else f"{name}\t{run_command}",
        })
    return games


def main(argv=None):
    p = argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument("--detect", action="store_true", help="Print detected Heroic config directories")
    p.add_argument("--json", action="store_true", help="Print JSON list of installed games")
    p.add_argument("--rofi-string", action="store_true", help="Output rofi-formatted strings for games")
    p.add_argument("--config-dir", type=Path, help="Read this Heroic config directory instead")
    args = p.parse_args(argv)

    configs = [args.config_dir] if args.config_dir else find_configs()

    if args.detect:
        print(json.dumps([str(c) for c in configs]))
        return 0

    games = [g for config in configs for g in list_games(config)]

    if args.json:
        print(json.dumps(games, indent=4))
        return 0

    if args.rofi_string:
        for g in games:
            print(g["rofi_string"])
        return 0

    print("No valid arguments provided. Use --detect, --json, or --rofi-string.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
