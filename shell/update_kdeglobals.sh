#!/bin/bash

# Configuration
SCHEME_FILE="$HOME/.local/state/caelestia/scheme.json"
KDE_GLOBALS="$HOME/.config/kdeglobals"
LOG_FILE="/tmp/kde_sync.log"

# Function to convert hex to comma-separated RGB
hex_to_rgb() {
    local hex=$1
    # Remove # if present
    hex=${hex#\#}
    printf "%d,%d,%d" "0x${hex:0:2}" "0x${hex:2:2}" "0x${hex:4:2}"
}

update_kde() {
    echo "$(date): Updating KDE theme from $SCHEME_FILE" >> "$LOG_FILE"
    if [ ! -f "$SCHEME_FILE" ]; then
        echo "$(date): Scheme file not found" >> "$LOG_FILE"
        return
    fi

    # Read colors from scheme.json
    BG_HEX=$(jq -r '.colours.surfaceContainerHigh' "$SCHEME_FILE")
    VIEW_HEX=$(jq -r '.colours.surface' "$SCHEME_FILE")
    BTN_HEX=$(jq -r '.colours.surfaceContainerHighest' "$SCHEME_FILE")
    SEL_HEX=$(jq -r '.colours.primary' "$SCHEME_FILE")
    FG_HEX=$(jq -r '.colours.onSurface' "$SCHEME_FILE")
    SEL_FG_HEX=$(jq -r '.colours.onPrimary' "$SCHEME_FILE")

    # Convert to RGB
    BG_RGB=$(hex_to_rgb "$BG_HEX")
    VIEW_RGB=$(hex_to_rgb "$VIEW_HEX")
    BTN_RGB=$(hex_to_rgb "$BTN_HEX")
    SEL_RGB=$(hex_to_rgb "$SEL_HEX")
    FG_RGB=$(hex_to_rgb "$FG_HEX")
    SEL_FG_RGB=$(hex_to_rgb "$SEL_FG_HEX")

    # Write kdeglobals
    cat > "$KDE_GLOBALS" <<EOF
[General]
ColorScheme=Caelestia
Name=Caelestia
widgetStyle=Fusion

[Icons]
Theme=Papirus-Dark

[KDE]
widgetStyle=Fusion

[Colors:Window]
BackgroundNormal=$BG_RGB
ForegroundNormal=$FG_RGB

[Colors:View]
BackgroundNormal=$VIEW_RGB
ForegroundNormal=$FG_RGB

[Colors:Button]
BackgroundNormal=$BTN_RGB
ForegroundNormal=$FG_RGB

[Colors:Selection]
BackgroundNormal=$SEL_RGB
ForegroundNormal=$SEL_FG_RGB
EOF

    echo "$(date): kdeglobals updated" >> "$LOG_FILE"

    # Restart KDE Connect if it was running
    if pgrep -f "kdeconnect-app" > /dev/null; then
        echo "$(date): Restarting kdeconnect-app" >> "$LOG_FILE"
        pkill -f "kdeconnect-app"
        # Wait a bit for it to actually die
        while pgrep -f "kdeconnect-app" > /dev/null; do sleep 0.1; done
        kdeconnect-app >/dev/null 2>&1 &
    fi
}

# Initial update (ensure sync on start)
update_kde

# Watch for changes (using close_write which is more reliable for file overwrites)
while inotifywait -e close_write "$SCHEME_FILE"; do
    update_kde
done
