#!/usr/bin/env python3
"""
Merged catalog for gamelauncher: combine Steam, Lutris and Heroic entries into one JSON/rofi stream.

Outputs:
  --json : prints array of {backend, id, name, display_name, header, install_dir}
  --rofi-string : prints rofi-ready lines: display_name\0icon\u001f<header>\x1e<backend>:<id>

The script probes for Lutris (flatpak or native) and calls the existing
`gamelauncher/steam.py --json` to get Steam entries.
"""

import json
import subprocess
import os
import sys
from collections import defaultdict


def fetch_entries(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching entries with {command}: {e}", file=sys.stderr)
        return []


def merge_entries(entries_by_backend):
    merged = []
    name_map = defaultdict(list)

    for backend, entries in entries_by_backend.items():
        for entry in entries:
            entry["backend"] = backend
            name_map[entry["name"].lower()].append(entry)

    for name, entries in name_map.items():
        for entry in entries:
            if len(entries) > 1:
                entry["display_name"] = (
                    f"{entry['name']} <sub><span size='medium' foreground='gray'>{entry['backend']}</span></sub>"
                )
            else:
                entry["display_name"] = entry["name"]
            merged.append(entry)

    return merged


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Output merged JSON")
    parser.add_argument("--rofi-string", action="store_true", help="Output merged rofi strings")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    merged = merge_entries({
        backend: fetch_entries(["python", os.path.join(script_dir, f"{backend}.py"), "--json"])
        for backend in ("steam", "lutris", "heroic")
    })

    if args.json:
        print(json.dumps(merged, indent=4))
        return

    if args.rofi_string:
        for entry in merged:
            rofi_string = f"{entry['display_name']}\t{entry['run_command']}"
            if entry.get("cover"):
                rofi_string += f"\t\x00icon\x1f{entry['cover']}"
            elif entry.get("icon"):
                rofi_string += f"\t\x00icon\x1f{entry['icon']}"
            elif entry.get("header"):
                rofi_string += f"\t\x00icon\x1f{entry['header']}"
            print(rofi_string)


if __name__ == "__main__":
    main()
