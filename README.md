# 🌌 Caelestia Dynamic Dotfiles

This repository contains my personalized, dynamically changing Arch Linux setup. The system is built upon the **Caelestia** ecosystem, enhanced with custom automation scripts for a unified visual experience.

## 🚀 How it Works (The "Engine")

The core of the system is wallpaper-based color generation. The process flows as follows:

1.  **Color Generation:** Caelestia extracts colors from the current wallpaper and saves them to `~/.local/state/caelestia/scheme.json`.
2.  **GTK Sync:** The Caelestia core automatically updates GTK 3/4 themes and KDE globals.
3.  **Post-Hook Automation:** The `shell/cli.json` configuration triggers the `scripts/update_css_vars.py` script after every change.
4.  **App-Specific Updates:** `update_css_vars.py` updates the following:
    *   **Vesktop (Discord):** Updates CSS variables for the glass effect.
    *   **Ghostty:** Generates the current theme and adjusts background opacity.
    *   **Spotify:** Injects colors via Spicetify bridge.
    *   **ZSH:** Updates `sequences.txt` for instant terminal color synchronization.

## 📁 Structure

*   `hypr/`: Hyprland window manager configurations (modular structure).
*   `shell/`: Caelestia Shell (Quickshell) QML files and settings.
*   `scripts/`: Python and Bash scripts for synchronization.
*   `apps/`: Application-specific configs (Ghostty, nwg-look, etc.).
*   `themes/`: Custom CSS templates and stylesheets.

## 🛠️ Essential Commands

*   `~/Reference/switch_shell.sh mine`: Switch back to your stable custom setup.
*   `~/Reference/switch_shell.sh caelestia`: Run the official Caelestia reference shell.
*   `~/Reference/switch_shell.sh noctalia`: Run the official Noctalia reference shell.

## 📋 Dependencies

*   `quickshell-git`: The UI engine.
*   `python3`: For running synchronization scripts.
*   `inotify-tools`: For monitoring file changes.
*   `grim / slurp`: For screenshots and visual verification.
