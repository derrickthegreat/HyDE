#!/usr/bin/env bash

#! A fallback script. Incase user explcitly set swww as wallpaper backend
notify-send "DEPRECATION NOTICE: swww backend is deprecated, please switch to awww or other supported backends. See 'hyde-shell wallpaper --help' for more info."

selected_wall="${1:-"$$HYDE_CACHE_HOME/wall.set"}"
scrDir="$(dirname "$(realpath "$0")")"
source "$scrDir/globalcontrol.sh"
wallpaper_acquire_lock 15
trap 'flock -u "$WALLPAPER_LOCK_FD"' EXIT
case "$WALLPAPER_SET_FLAG" in
    p)
        xtrans=$WALLPAPER_SWWW_TRANSITION_PREV
        xtrans="${xtrans:-"outer"}"
        ;;
    n)
        xtrans=$WALLPAPER_SWWW_TRANSITION_NEXT
        xtrans="${xtrans:-"grow"}"
        ;;
esac
selected_wall="$1"
[ -z "$selected_wall" ] && echo "No input wallpaper" && exit 1
selected_wall="$(readlink -f "$selected_wall")"
if ! timeout 15 swww query &> /dev/null; then
    swww-daemon --format xrgb &
    disown
    timeout 15 swww query && timeout 15 swww restore
fi
is_video=$(file --mime-type -b "$selected_wall" | grep -c '^video/')
if [ "$is_video" -eq 1 ]; then
    print_log -sec "wallpaper" -stat "converting video" "$selected_wall"
    mkdir -p "$HYDE_CACHE_HOME/wallpapers/thumbnails"
    cached_thumb="$HYDE_CACHE_HOME/wallpapers/$(${hashMech:-sha1sum} "$selected_wall" | cut -d' ' -f1).png"
    extract_thumbnail "$selected_wall" "$cached_thumb"
    selected_wall="$cached_thumb"
fi
xtrans=$WALLPAPER_SWWW_TRANSITION_DEFAULT
[ -z "$xtrans" ] && xtrans="grow"
[ -z "$wallFramerate" ] && wallFramerate=60
[ -z "$wallTransDuration" ] && wallTransDuration=0.4
# Fit by default: cropping to a 32:9 screen eats most of a 16:9 wallpaper. See
# get_wallpaper_fill_color for what pads the leftover sides. Set
# WALLPAPER_SWWW_RESIZE=crop to get the upstream fill-and-crop behaviour back,
# and WALLPAPER_SWWW_CROP_GRAVITY to choose which part of it survives.
wall_resize="${WALLPAPER_SWWW_RESIZE:-${WALLPAPER_RESIZE:-fit}}"
wall_fill="$(get_wallpaper_fill_color "$selected_wall")"
resize_args=(--resize "$wall_resize" --fill-color "$wall_fill")
if [ "$wall_resize" == "crop" ] && [ -n "${WALLPAPER_SWWW_CROP_GRAVITY:-$WALLPAPER_CROP_GRAVITY}" ]; then
    resize_args+=(--crop-gravity "${WALLPAPER_SWWW_CROP_GRAVITY:-$WALLPAPER_CROP_GRAVITY}")
fi
print_log -sec "wallpaper" -stat "apply" "$selected_wall"
timeout 30 swww img "$(readlink -f "$selected_wall")" "${resize_args[@]}" --transition-bezier .43,1.19,1,.4 --transition-type "$xtrans" --transition-duration "$wallTransDuration" --transition-fps "$wallFramerate" --invert-y --transition-pos "$(hyprctl cursorpos | grep -E '^[0-9]' || echo "0,0")"
