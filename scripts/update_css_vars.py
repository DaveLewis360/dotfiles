#!/usr/bin/env python3
import json
import os
import re
import subprocess
from pathlib import Path

# Paths
user_home = Path.home()
state_dir = user_home / ".local/state/caelestia"
scheme_path = state_dir / "scheme.json"
sequences_path = state_dir / "sequences.txt"
shell_config_path = user_home / ".config/caelestia/shell.json"

# App config paths
ghostty_theme_path = user_home / ".config/ghostty/current_theme.conf"
vesktop_theme_path = user_home / ".config/vesktop/themes/ZenCaelestia.theme.css"
vencord_theme_path = user_home / ".config/Vencord/themes/ZenCaelestia.theme.css"

ANSI_MAPPING = {
    0: "surfaceContainerLowest", 1: "red", 2: "green", 3: "yellow",
    4: "blue", 5: "mauve", 6: "teal", 7: "onSurface",
    8: "surfaceVariant", 9: "red", 10: "green", 11: "yellow",
    12: "blue", 13: "mauve", 14: "teal", 15: "onSurface",
    16: "primary", 17: "secondary", 18: "tertiary"
}

GHOSTTY_MAPPING = {
    "foreground": "onBackground",
    "cursor-color": "primary",
    "selection-background": "primaryContainer",
    "selection-foreground": "onPrimaryContainer"
}


def hex_to_osc(code, hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"\033]{code};rgb:{r:02x}/{g:02x}/{b:02x}\007"


def get_color(colors, key):
    val = colors.get(key)
    if val:
        return f"#{val}" if not val.startswith("#") else val
    camel = re.sub(r'_([a-z])', lambda m: m.group(1).upper(), key)
    val = colors.get(camel)
    if val:
        return f"#{val}" if not val.startswith("#") else val
    return "#ffffff"


def update_css_var(content, key, val):
    if not val.startswith("#"):
        val = f"#{val}"
    escaped = re.escape(key)
    pattern = re.compile(f'--{escaped}: #[0-9a-fA-F]+;', re.IGNORECASE)
    return pattern.sub(f'--{key}: {val};', content)


def main():
    if not scheme_path.exists():
        print(f"Error: {scheme_path} not found")
        return

    with open(scheme_path, 'r') as f:
        scheme_data = json.load(f)
    dynamic_colors = scheme_data.get("colours", {})

    # Load shell config for transparency
    app_opacity = 0.7
    if shell_config_path.exists():
        try:
            with open(shell_config_path, 'r') as f:
                shell_config = json.load(f)
            app_opacity = shell_config.get("appearance", {}).get("transparency", {}).get("base", 0.7)
        except:
            pass

    # --- UPDATE GHOSTTY ---
    if ghostty_theme_path.exists():
        lines = ["background = #000000\n"]

        for ghost_key, m3_key in GHOSTTY_MAPPING.items():
            lines.append(f"{ghost_key} = {get_color(dynamic_colors, m3_key)}\n")

        for i, m3_key in ANSI_MAPPING.items():
            lines.append(f"palette = {i}={get_color(dynamic_colors, m3_key)}\n")

        ghostty_theme_path.write_text("".join(lines))

    # --- UPDATE DISCORD CSS ---
    discord_themes = [vesktop_theme_path, vencord_theme_path]
    for theme_path in discord_themes:
        if theme_path.exists():
            content = theme_path.read_text()

            content = re.sub(r'--app-opacity: [0-9.]+;', f'--app-opacity: {app_opacity};', content)

            for m3_key, val in dynamic_colors.items():
                content = update_css_var(content, m3_key, val)

            theme_path.write_text(content)

    # --- LIVE REFRESH TERMINALS ---
    sequences = hex_to_osc(10, get_color(dynamic_colors, "onBackground"))
    sequences += hex_to_osc(11, "000000")
    sequences += hex_to_osc(12, get_color(dynamic_colors, "primary"))
    for i in range(1, 16):
        sequences += hex_to_osc(f"4;{i}", get_color(dynamic_colors, ANSI_MAPPING.get(i, "")))
    for i in range(16, 19):
        sequences += hex_to_osc(f"4;{i}", get_color(dynamic_colors, ANSI_MAPPING.get(i, "")))

    try:
        sequences_path.write_text(sequences)
    except:
        pass

    pts_path = Path("/dev/pts")
    if pts_path.exists():
        for pt in pts_path.iterdir():
            if pt.name.isdigit():
                try:
                    with open(pt, 'w') as f:
                        f.write(sequences)
                except:
                    pass

    # --- RELOAD HYPRLAND (skip on first run to avoid disrupting startup) ---
    if os.environ.get("CAELESTIA_WATCHER") == "1":
        subprocess.run(["hyprctl", "reload"], stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
