#!/usr/bin/env bash
scrDir=$(dirname "$(realpath "$0")")
source "$scrDir/globalcontrol.sh"
hyprctl switchxkblayout current next
layMain=$(hyprctl -j devices | jq '.keyboards' | jq '.[] | select (.main == true)' | awk -F '"' '{if ($2=="active_keymap") print $4}')
notify-send -a "HyDE Alert" -h string:x-canonical-private-synchronous:hyde.keyboard -t 800 -i "$ICONS_DIR/Wallbash-Icon/keyboard.svg" "$layMain"
