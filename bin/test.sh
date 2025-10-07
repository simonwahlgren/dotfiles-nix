pick_clipboard_item() {
  command -v cliphist >/dev/null || return 1

  # Build "id<TAB>preview" rows so we can reliably extract the id with a tab split.
  # We truncate the preview to keep the menu fast and readable.
  local choice id
  choice="$(
    cliphist list | head -n 50 \
    | awk '{
        id=$1; $1="";
        sub(/^[ \t]+/, "", $0);          # trim leading spaces
        gsub(/\t/, " ", $0);              # sanitize tabs in preview
        preview=$0;
        if (length(preview) > 160) preview=substr(preview,1,160) "…";
        print id "\t" preview
      }' \
    | wofi --dmenu -i -p "Choose from history" 2>/dev/null \
    || true
  )"

  # User hit Esc or nothing selected
  [ -n "${choice:-}" ] || return 1

  # Extract id (tab-delimited) and decode it
  id="${choice%%$'\t'*}"
  [ -n "$id" ] || return 1

  cliphist decode "$id"
}

