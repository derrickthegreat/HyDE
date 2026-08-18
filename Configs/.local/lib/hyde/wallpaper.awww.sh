#!/usr/bin/env bash
selected_wall="${1:-"$$HYDE_CACHE_HOME/wall.set"}"
scrDir="$(dirname "$(realpath "$0")")"
source "$scrDir/globalcontrol.sh"
wallpaper_acquire_lock 15
trap 'flock -u "$WALLPAPER_LOCK_FD"' EXIT
case "$WALLPAPER_SET_FLAG" in
    p)
        xtrans=$WALLPAPER_AWWW_TRANSITION_PREV
        xtrans="${xtrans:-"outer"}"
        ;;
    n)
        xtrans=$WALLPAPER_AWWW_TRANSITION_NEXT
        xtrans="${xtrans:-"grow"}"
        ;;
esac
selected_wall="$1"
[ -z "$selected_wall" ] && echo "No input wallpaper" && exit 1
selected_wall="$(readlink -f "$selected_wall")"
if ! timeout 15 awww query &> /dev/null; then
    awww-daemon --format xrgb &
    disown
    timeout 15 awww query && timeout 15 awww restore
fi
is_video=$(file --mime-type -b "$selected_wall" | grep -c '^video/')
if [ "$is_video" -eq 1 ]; then
    print_log -sec "wallpaper" -stat "converting video" "$selected_wall"
    mkdir -p "$HYDE_CACHE_HOME/wallpapers/thumbnails"
    cached_thumb="$HYDE_CACHE_HOME/wallpapers/$(${hashMech:-sha1sum} "$selected_wall" | cut -d' ' -f1).png"
    extract_thumbnail "$selected_wall" "$cached_thumb"
    selected_wall="$cached_thumb"
fi
xtrans=$WALLPAPER_AWWW_TRANSITION_DEFAULT
[ -z "$xtrans" ] && xtrans="grow"
[ -z "$wallFramerate" ] && wallFramerate=60
[ -z "$wallTransDuration" ] && wallTransDuration=0.4
# "ambient" fits the whole image over a blurred copy of itself; see
# fit_wallpaper. WALLPAPER_AWWW_FIT (or WALLPAPER_FIT) also takes swww's own
# crop / fit / stretch / no, in which case the image is passed through
# untouched and only the resize flag changes.
wall_fit="${WALLPAPER_AWWW_FIT:-${WALLPAPER_FIT:-ambient}}"
IFS=$'\t' read -r wall_resize selected_wall < <(fit_wallpaper "$selected_wall" "$wall_fit")
resize_args=(--resize "$wall_resize")
[ "$wall_fit" == "fit" ] && resize_args+=(--fill-color "$(get_wallpaper_fill_color "$selected_wall")")
if [ "$wall_resize" == "crop" ] && [ -n "${WALLPAPER_AWWW_CROP_GRAVITY:-$WALLPAPER_CROP_GRAVITY}" ]; then
    resize_args+=(--crop-gravity "${WALLPAPER_AWWW_CROP_GRAVITY:-$WALLPAPER_CROP_GRAVITY}")
fi
print_log -sec "wallpaper" -stat "apply" "$selected_wall"
timeout 30 awww img "$(readlink -f "$selected_wall")" "${resize_args[@]}" --transition-bezier .43,1.19,1,.4 --transition-type "$xtrans" --transition-duration "$wallTransDuration" --transition-fps "$wallFramerate" --invert-y --transition-pos "$(hyprctl cursorpos | grep -E '^[0-9]' || echo "0,0")"
