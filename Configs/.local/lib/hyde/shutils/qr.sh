#!/usr/bin/env bash

[[ ${HYDE_SHELL_INIT} -ne 1 ]] && eval "$(hyde-shell init)"

qr_extract() {

    image_path="$1"

    if ! pkg_installed "zbar"; then
        notify-send -a "HyDE Alert" -h string:x-canonical-private-synchronous:hyde.qr -e -i "dialog-error" "zbar package is not installed"
        return 1
    fi

    qr_output=$(
        zbarimg \
            --quiet \
            --oneshot \
            --raw \
            "${image_path}" \
            2> /dev/null
    )

    printf "%s" "$qr_output" | wl-copy
    notify-send -a "HyDE Alert" -h string:x-canonical-private-synchronous:hyde.qr -e -i "$image_path" "QR: successfully recognized"
}
