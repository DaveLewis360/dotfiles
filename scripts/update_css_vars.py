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
ghostty_config_path = user_home / "dotfiles/apps/ghostty/config"

# Vesktop themes
vesktop_themes = [
    user_home / ".config/vesktop/themes/GhosttyZen.theme.css",
    user_home / ".config/vesktop/themes/MidnightGlass.theme.css",
    user_home / ".config/vesktop/themes/ZenTransparency.theme.css",
    user_home / ".config/vesktop/themes/ZenCaelestia.theme.css",
    user_home / ".config/vesktop/themes/CaelestiaGlassCard.theme.css"
]

def hex_to_osc(code, hex_val):
    """Convert hex to OSC sequence: \x1b]{code};rgb:{rr}/{gg}/{bb}\x1b\\"""
    h = hex_val.lstrip('#')
    if len(h) != 6: return ""
    return f"\x1b]{code};rgb:{h[0:2]}/{h[2:4]}/{h[4:6]}\x1b\\"

def main():
    if not scheme_path.exists(): return
    try:
        with open(scheme_path, "r") as f:
            scheme_data = json.load(f)
            dynamic_colors = scheme_data.get("colours", {})
    except: return

    # 2. Load User Preferences (From shell.json)
    app_bg = "#000000"
    app_opacity = 0.5
    layer_opacity = 0.3
    if shell_config_path.exists():
        try:
            with open(shell_config_path, "r") as f:
                shell_data = json.load(f)
                trans = shell_data.get("appearance", {}).get("transparency", {})
                app_bg = trans.get("appBackground", "#000000")
                app_opacity = trans.get("base", 0.5)
                layer_opacity = trans.get("layers", 0.3)
        except: pass

    # --- UPDATE GHOSTTY CONFIG FILE ---
    if ghostty_theme_path.exists():
        lines = []
        
        mapping = {
            "background": "surface_container_lowest",
            "foreground": "on_background",
            "cursor-color": "primary",
            "selection-background": "primary_container",
            "selection-foreground": "on_primary_container"
        }
        for ghost_key, m3_key in mapping.items():
            val = dynamic_colors.get(m3_key, "000000" if ghost_key == "background" else "ffffff")
            if not val.startswith("#"): val = f"#{val}"
            lines.append(f"{ghost_key} = {val}\n")
            
        ansi_mapping = {
            0: "surface_container_lowest", 1: "red", 2: "green", 3: "yellow",
            4: "blue", 5: "mauve", 6: "teal", 7: "text",
            8: "surface_variant", 9: "red", 10: "green", 11: "yellow",
            12: "blue", 13: "mauve", 14: "teal", 15: "on_background",
            16: "primary", 17: "secondary", 18: "tertiary"
        }
        for i in range(19):
            scheme_key = ansi_mapping.get(i, "text")
            val = dynamic_colors.get(scheme_key, "ffffff")
            if not val.startswith("#"): val = f"#{val}"
            lines.append(f"palette = {i}={val}\n")
        ghostty_theme_path.write_text("".join(lines))

    # --- LIVE REFRESH TERMINALS (PTS Injection) ---
    sequences = hex_to_osc(10, dynamic_colors.get("on_background", "ffffff"))
    sequences += hex_to_osc(11, dynamic_colors.get("surface_container_lowest", "000000"))
    sequences += hex_to_osc(12, dynamic_colors.get("primary", "ffffff"))
    for i in range(1, 16):
        sequences += hex_to_osc(f"4;{i}", dynamic_colors.get(ansi_mapping.get(i), "ffffff"))
    
    # Extended 16-18
    for i in range(16, 19):
        sequences += hex_to_osc(f"4;{i}", dynamic_colors.get(ansi_mapping.get(i), "ffffff"))

    # Save to sequences.txt for new shells / ZSH hooks
    try:
        sequences_path.write_text(sequences)
    except: pass

    pts_path = Path("/dev/pts")
    if pts_path.exists():
        for pt in pts_path.iterdir():
            if pt.name.isdigit():
                try:
                    with pt.open("a") as f: f.write(sequences)
                except: pass

    # --- UPDATE DISCORD/VESKTOP ---
    css_vars = "\n/* BEGIN CAELESTIA COLORS */\n:root {\n"
    css_vars += f"  --app-background: {app_bg};\n"
    css_vars += f"  --app-opacity: {app_opacity};\n"
    css_vars += f"  --app-layer: rgba(0, 0, 0, {layer_opacity});\n"
    for name, hex_code in dynamic_colors.items():
        if not hex_code.startswith("#"): hex_code = f"#{hex_code}"
        css_vars += f"  --{name.replace('_', '-')}: {hex_code};\n"
        css_vars += f"  --{re.sub(r'_([a-z])', lambda m: m.group(1).upper(), name)}: {hex_code};\n"
    css_vars += "}\n/* END CAELESTIA COLORS */\n"

    for theme_path in vesktop_themes:
        if theme_path.exists():
            content = theme_path.read_text()
            pattern = r"/\* BEGIN CAELESTIA COLORS \*/.*?/\* END CAELESTIA COLORS \*/"
            if re.search(pattern, content, re.DOTALL):
                new_content = re.sub(pattern, css_vars, content, flags=re.DOTALL)
            else:
                imports = re.findall(r"@import url\(.*?\);", content)
                if imports:
                    last_import = imports[-1]
                    new_content = content.replace(last_import, last_import + css_vars)
                else:
                    new_content = css_vars + content
            theme_path.write_text(new_content)

    # --- RELOAD HYPRLAND ---
    subprocess.run(["hyprctl", "reload"], stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()
