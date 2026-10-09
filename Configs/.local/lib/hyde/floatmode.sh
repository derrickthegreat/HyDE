#!/usr/bin/env bash
# Float mode: floats every open window, and while it is on the window.open hook
# in events.lua floats new ones too. Windows it floats get the hyde_floatmode
# tag, so switching it off re-tiles only those; dialogs and windows you floated
# yourself stay floating.
STATE_FILE="${XDG_RUNTIME_DIR}/hyde/floatmode"
TAG="hyde_floatmode"

notify() {
    notify-send -a "HyDE Notify" -h string:x-canonical-private-synchronous:hyde.floatmode -t 800 -i window-new "$@"
}

# Sets the floating state and tag of the given windows in one eval
set_windows() {
    local action=$1 tag=$2
    shift 2
    [ $# -eq 0 ] && return 0
    local lua="" addr
    for addr in "$@"; do
        lua+="hl.dispatch(hl.dsp.window.float({ window = \"address:$addr\", action = \"$action\" })) "
        lua+="hl.dispatch(hl.dsp.window.tag({ window = \"address:$addr\", tag = \"$tag\" })) "
    done
    hyprctl eval "$lua" >/dev/null
}

if [ -f "$STATE_FILE" ]; then
    rm -f "$STATE_FILE"
    mapfile -t windows < <(hyprctl clients -j | jq -r --arg tag "$TAG" '.[] | select(any(.tags[]; startswith($tag))) | .address')
    set_windows disable "-$TAG" "${windows[@]}"
    notify "Float mode: OFF"
else
    mkdir -p "${STATE_FILE%/*}"
    touch "$STATE_FILE"
    # Fullscreen windows (a video, a game) are left as they are
    mapfile -t windows < <(hyprctl clients -j | jq -r '.[] | select(.mapped and (.floating | not) and .fullscreen == 0) | .address')
    set_windows enable "+$TAG" "${windows[@]}"
    notify "Float mode: ON"
fi
