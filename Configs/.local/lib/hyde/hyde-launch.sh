#!/usr/bin/env bash
[[ $HYDE_SHELL_INIT -ne 1 ]] && eval "$(hyde-shell init)"

notify-send -a "HyDE Alert" -i dialog-information "Deprecation notice" "hyde-launch.sh is deprecated. Please use hyde-shell open instead."

hyde-shell open "$@"
