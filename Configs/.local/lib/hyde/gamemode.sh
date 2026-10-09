#!/usr/bin/env bash
LOCK_FILE="${XDG_RUNTIME_DIR}/hyde/gamemode.lck"

# Trades the compositor's expensive effects for performance, as the old
# workflows/gaming.conf did. `hyprctl keyword` no longer works with the Lua
# config, so the settings are applied through `hyprctl eval`.
GAMEMODE_CONFIG='hl.config({
    decoration = {
        shadow = { enabled = false },
        blur = { enabled = false },
        rounding = 0,
        active_opacity = 1,
        inactive_opacity = 1,
        fullscreen_opacity = 1,
    },
    general = { gaps_in = 0, gaps_out = 0, border_size = 1 },
    animations = { enabled = false },
})'

notify() {
    notify-send -a "HyDE Notify" -h string:x-canonical-private-synchronous:hyde.gamemode -t 800 -i input-gaming "$@"
}

if [ -f "$LOCK_FILE" ]; then
    # Gamemode is ON → turn it OFF
    hyprctl reload config-only -q
    rm -f "$LOCK_FILE"
    notify "Game Mode: OFF"
else
    # Gamemode is OFF → turn it ON
    mkdir -p "${XDG_RUNTIME_DIR}/hyde"
    result=$(hyprctl eval "$GAMEMODE_CONFIG" 2>&1)
    if [ "$result" != "ok" ]; then
        notify-send -a "HyDE Alert" -h string:x-canonical-private-synchronous:hyde.gamemode -i input-gaming \
            "Game mode couldn't start" "$result"
        exit 1
    fi
    touch "$LOCK_FILE"
    notify "Game Mode: ON"
fi
