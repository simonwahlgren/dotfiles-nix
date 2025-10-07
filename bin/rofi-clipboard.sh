#!/usr/bin/env bash
set -euo pipefail

PREVIEW_WIDTH="${PREVIEW_WIDTH:-1000}"

ROFI_MSG="Enter = copy   •   Alt-e = edit"
selection="$(
  cliphist -preview-width="$PREVIEW_WIDTH" list \
    | rofi -dmenu -i -p "Clipboard" -mesg "$ROFI_MSG" -kb-custom-1 "Alt-e"
)"
status=$?

# user canceled
[[ $status -eq 1 || -z "${selection}" ]] && exit 0

# the `cliphist list` format is: "<ID>\t<preview>"
id="$(printf '%s' "$selection" | awk -F '\t' '{print $1}')"
[[ -z "$id" ]] && exit 0

if [[ $status -eq 0 ]]; then
  # ENTER: copy as text (to both clipboard and primary)
  cliphist decode "$id" | tee >(wl-copy --primary) | wl-copy --type text/plain
  exit 0
fi

if [[ $status -eq 10 ]]; then
  # Alt-e: edit in a temp file via neovim, then copy result
  tmp="$(mktemp --suffix=.txt)"
  trap 'rm -f "$tmp"' EXIT

  # populate file with full decoded entry
  cliphist decode "$id" >"$tmp"

  # open alacritty -> run nvim -> copy result -> exit
  alacritty -e bash -lc "nvim \"$tmp\"; wl-copy --type text/plain < \"$tmp\"; wl-copy --primary < \"$tmp\""
  exit 0
fi
