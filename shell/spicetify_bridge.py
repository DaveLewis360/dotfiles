#!/usr/bin/env python3
import json
import os
import time
import subprocess
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Paths
CAELESTIA_SCHEME = Path.home() / ".local/state/caelestia/scheme.json"
SPICETIFY_THEME_DIR = Path.home() / ".config/spicetify/Themes/CaelestiaGlass"
COLOR_INI = SPICETIFY_THEME_DIR / "color.ini"
WALLPAPER_DEST = SPICETIFY_THEME_DIR / "current_wallpaper.png"

current_data = {}

class ColorServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/colors':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(current_data).encode())
    def log_message(self, format, *args): return

def run_server():
    try:
        server = HTTPServer(('127.0.0.1', 5005), ColorServer)
        server.serve_forever()
    except Exception as e:
        print(f"Server error: {e}")

def get_current_wallpaper():
    cache_dir = Path.home() / ".cache/caelestia"
    if not cache_dir.exists(): return None
    imgs = list(cache_dir.glob("**/*.png")) + list(cache_dir.glob("**/*.jpg"))
    return max(imgs, key=os.path.getmtime) if imgs else None

def update_spicetify(scheme_data):
    try:
        colors = scheme_data.get("colours", {})
        if not colors: return

        # Mapping for color.ini
        mapping = {
            "main": "background",
            "sidebar": "surfaceContainer",
            "player": "surfaceContainerHigh",
            "card": "surfaceVariant",
            "shadow": "shadow",
            "selected-row": "surfaceContainerHighest",
            "button": "primary",
            "button-active": "primary",
            "button-disabled": "surfaceVariant",
            "tab-active": "primary",
            "notification": "surfaceContainer",
            "notification-error": "error",
            "text": "onSurface",
            "subtext": "onSurfaceVariant",
            "misc": "outline"
        }

        content = "[Caelestia]\n"
        for spice_key, cael_key in mapping.items():
            color_val = colors.get(cael_key, "ffffff").replace("#", "")
            content += f"{spice_key:<18} = {color_val}\n"

        with open(COLOR_INI, "w") as f:
            f.write(content)

        # Wallpaper sync
        wall = get_current_wallpaper()
        if wall:
            subprocess.run(["cp", str(wall), str(WALLPAPER_DEST)])

        print("Applying Caelestia colors to Spicetify...")
        subprocess.run(["spicetify", "update"], capture_output=True)
    except Exception as e:
        print(f"Error updating Spicetify: {e}")

def main():
    global current_data
    # Start server in separate thread
    threading.Thread(target=run_server, daemon=True).start()
    print("Caelestia Bridge running on http://127.0.0.1:5005")

    last_mtime = 0
    while True:
        if CAELESTIA_SCHEME.exists():
            try:
                mtime = os.path.getmtime(CAELESTIA_SCHEME)
                if mtime > last_mtime:
                    with open(CAELESTIA_SCHEME, "r") as f:
                        current_data = json.load(f)
                    current_data['wallpaper_timestamp'] = int(time.time())
                    
                    update_spicetify(current_data)
                    
                    last_mtime = mtime
                    print("Memory and files updated with new scheme.")
            except Exception as e:
                print(f"Error in main loop: {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()
