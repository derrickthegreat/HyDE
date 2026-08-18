#!/usr/bin/env bash

show_help() {
    cat <<EOF
Usage: $(basename "$0") --[options|flags] [parameters]
options:
    -j, --json                List wallpapers in JSON format to STDOUT
    -S, --select              Select wallpaper using rofi
    -n, --next                Set next wallpaper
    -p, --previous            Set previous wallpaper
    -r, --random              Set random wallpaper
    -s, --set <file>          Set specified wallpaper
        --start               Start/apply current wallpaper to backend
    -g, --get                 Get current wallpaper of specified backend
    -o, --output <file>       Copy current wallpaper to specified file
        --multi-select        Enable multi-selection in select mode (Works for --output only)
        --link                Resolved the linked wallpaper according to the theme
    -t  --filetypes <types>   Specify file types to override (colon-separated ':')
        --cache <mode> [arg]  Build wallpaper cache
                              modes: current, wall <file>, theme <name>, full
        --fit <mode>          Pin how this wallpaper is fitted to the screen
                              modes: auto, ambient[:budget], crop, fit, stretch, no
    -h, --help                Display this help message

flags:
    -b, --backend <backend>   Set wallpaper backend to use (awww, hyprpaper, etc.)
    -G, --global              Set wallpaper as global


notes:
       --backend <backend> is also use to cache wallpapers/background images e.g. hyprlock
           when '--backend hyprlock' is used, the wallpaper will be cached in
           ~/.cache/hyde/wallpapers/hyprlock.png

       --global flag is used to set the wallpaper as global, this means all
         thumbnails will be updated to reflect the new wallpaper

       --output <path> is used to copy the current wallpaper to the specified path
            We can use this to have a copy of the wallpaper to '/var/tmp' where sddm or
            any systemwide application can access it

       --fit <mode> pins the current wallpaper to one fit mode, overriding the
            automatic choice for that image only. 'ambient' fits it over a blurred
            copy of itself; append a budget to say how much of it may be cropped
            away first, e.g. '--fit ambient:0' to keep every pixel. 'auto' removes
            the pin. Overrides live in ~/.local/state/hyde/wallpaper.fit, keyed by
            image content, so they survive renaming or moving the file
EOF
    exit 0
}
