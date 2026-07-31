#!/usr/bin/env bash
# =============================================================================
# smart-launch.sh — focus a Zen wrapper window if it runs, otherwise start it
# =============================================================================
#   smart-launch.sh <window-class> <zen-profile> <url>
#
# Why the wrapper .desktop files must go through this script instead of calling
# zen-browser directly:
#
#   `xdg-settings get default-web-browser` does not read mimeapps.list. It scans
#   .desktop files for one whose Exec matches $BROWSER (here: "zen-browser") and
#   returns the first match. The wrappers matched, so the Messenger wrapper was
#   reported as the system's default browser — and any app asking that way got a
#   single-site Messenger window instead of a normal browsing session.
#
#   Routing through this script keeps "zen-browser" out of the Exec line, so the
#   real zen.desktop wins again.
# =============================================================================

set -uo pipefail

CLASS="${1:?usage: smart-launch.sh <class> <profile> <url>}"
PROFILE="${2:?missing zen profile}"
URL="${3:-}"

# Resolve the browser binary without the literal string "zen-browser" appearing
# in a .desktop Exec line (see the note above).
BIN="$(command -v zen-browser || true)"
[[ -z "$BIN" ]] && BIN="/opt/zen-browser-bin/zen-bin"

focus_existing() {
    command -v hyprctl >/dev/null 2>&1 || return 1

    # Is a window of this class already open?
    hyprctl -j clients 2>/dev/null | python3 -c '
import json, sys
cls = sys.argv[1]
try:
    clients = json.load(sys.stdin)
except Exception:
    sys.exit(1)
sys.exit(0 if any(c.get("class") == cls for c in clients) else 1)
' "$CLASS" || return 1

    # Hyprland picks its config parser at startup. With a Lua config the plain
    # `hyprctl dispatch focuswindow ...` form is rejected:
    #   "dispatch in lua is a shorthand for hl.dispatch(...)"
    # so try the Lua form first and fall back to the legacy one.
    if hyprctl dispatch "hl.dsp.focus({ window = \"class:$CLASS\" })" 2>/dev/null | grep -q '^ok'; then
        return 0
    fi
    hyprctl dispatch focuswindow "class:^($CLASS)$" >/dev/null 2>&1
}

if focus_existing; then
    exit 0
fi

exec "$BIN" --new-instance --name "$CLASS" --class "$CLASS" -P "$PROFILE" "$URL"
