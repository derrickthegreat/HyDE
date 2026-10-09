#!/usr/bin/python3

import html
import subprocess
import json
import sys

MAX_SHOWN = 10
MAX_LINE = 60
# HyDE's own notifications use these app names for dunst styling; show them as one name
HYDE_APP_NAMES = {"HyDE Alert": "HyDE", "HyDE Notify": "HyDE"}


def get_dunst_history():
    result = subprocess.run(["dunstctl", "history"], stdout=subprocess.PIPE, check=True)
    history = json.loads(result.stdout.decode("utf-8"))
    return history


def _field(notification, key):
    return notification.get(key, {}).get("data", "")


def format_line(notification):
    """One tooltip line: the app in bold, then the summary and body on a single truncated line."""
    app = _field(notification, "appname")
    app = HYDE_APP_NAMES.get(app, app)
    text = " · ".join(part for part in (_field(notification, "summary"), _field(notification, "body")) if part)
    text = " ".join(text.split())
    if len(text) > MAX_LINE:
        text = text[: MAX_LINE - 1] + "…"
    return f"<b>{html.escape(app)}</b> {html.escape(text)}"


def format_history(history):
    notifications = history["data"][0]
    count = len(notifications)
    alt = "none"
    if count > 0:
        # dunstctl lists the newest first, so the badge follows the latest notification
        category = _field(notifications[0], "category")
        alt = f"{category}-notification" if category else "notification"

    isDND = subprocess.run(["dunstctl", "get-pause-level"], stdout=subprocess.PIPE, check=True)
    isDND = isDND.stdout.decode("utf-8").strip()
    if isDND != "0":
        alt = "dnd"

    tooltip = [f"<b>󰎟 {count} notification{'' if count == 1 else 's'}</b>"]
    if isDND != "0":
        tooltip.append("<i>Do not disturb is on</i>")
    tooltip.extend(format_line(n) for n in notifications[:MAX_SHOWN])
    if count > MAX_SHOWN:
        tooltip.append(f"<i>…and {count - MAX_SHOWN} more</i>")
    tooltip.append(
        "<span size='x-small'>"
        "\n󰳽 scroll down: history pop"
        "\n󰳽 click: toggle do not disturb"
        "\n󰳽 middle click: clear history"
        "\n󰳽 right click: menu"
        "</span>"
    )

    formatted_history = {
        "text": str(count),
        "alt": alt,
        "tooltip": "\n".join(tooltip),
        "class": alt,
    }
    return formatted_history


def main():
    history = get_dunst_history()
    formatted_history = format_history(history)
    sys.stdout.write(json.dumps(formatted_history) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
