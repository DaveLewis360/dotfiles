#!/bin/bash

ZEN_BIN="zen-browser"
PROFILES_DIR="$HOME/.zen"
DEFAULT_SHORTCUTS="$PROFILES_DIR/hangkafo.Default (release)/zen-keyboard-shortcuts.json"

create_simple_wrapper() {
    local app_name=$1
    local url=$2
    local profile_name="${app_name}Wrapper"
    local profile_path="$PROFILES_DIR/$profile_name"

    echo "-> $app_name profil előkészítése..."

    # 1. Add to profiles.ini
    if ! grep -q "Name=$profile_name" "$PROFILES_DIR/profiles.ini"; then
        NEXT_ID=$(grep -c "^\[Profile" "$PROFILES_DIR/profiles.ini" || echo "0")
        echo -e "\n[Profile$NEXT_ID]\nName=$profile_name\nIsRelative=1\nPath=$profile_name" >> "$PROFILES_DIR/profiles.ini"
    fi

    # 2. Create Profile Directory
    mkdir -p "$profile_path/chrome"

    # 3. Create user.js (Simplified & Stable)
    cat > "$profile_path/user.js" <<EOF
user_pref("browser.aboutwelcome.enabled", false);
user_pref("zen.welcome-screen.seen", true);
user_pref("zen.view.compact.enable-at-startup", true);
user_pref("zen.view.compact.hide-toolbar", true);
user_pref("zen.view.compact.show-sidebar-and-toolbar-on-hover", false);
user_pref("zen.view.sidebar-expanded", false);
user_pref("zen.view.use-single-toolbar", false);
user_pref("zen.theme.content-element-separation", 0);

// Persistence & Cache (Mod beállítások megőrzése)
user_pref("browser.cache.disk.enable", true);
user_pref("privacy.clearOnShutdown.cookies", false);
user_pref("privacy.sanitize.sanitizeOnShutdown", false);
user_pref("dom.storage.enabled", true);
user_pref("extensions.webextensions.ExtensionStorageIDB.enabled", true);

// Single Tab Policy
user_pref("browser.startup.page", 1);
user_pref("browser.startup.homepage", "$url");
user_pref("browser.link.open_newwindow", 1);
user_pref("browser.sessionstore.enabled", false);
// Interaction Restrictions
user_pref("browser.urlbar.shortcutFocus", false);
user_pref("accessibility.typeaheadfind", false);
user_pref("ui.key.menuAccessKey", 0);

// --- EXTREME RESOURCE OPTIMIZATION (RAM & CPU) ---
user_pref("fission.autostart", false);
user_pref("dom.ipc.processCount", 1);
user_pref("dom.ipc.processCount.webIsolated", 1);
user_pref("dom.ipc.processPrelaunch.enabled", false);
user_pref("dom.ipc.forkserver.enable", false);
user_pref("browser.tabs.remote.separatePrivilegedContentProcess", false);
user_pref("extensions.webextensions.remote", false); // Extensions in main process
user_pref("network.process.enabled", false);         // Network in main process
user_pref("layers.gpu-process.enabled", false);
user_pref("webgl.disabled", true);
user_pref("media.utility-process.enabled", false);
user_pref("media.utility-process.audio", false);
user_pref("media.utility-process.video", false);
user_pref("media.rdd-process.enabled", false);
user_pref("browser.sessionhistory.max_entries", 1);
user_pref("browser.sessionhistory.max_total_viewers", 0);
user_pref("browser.tabs.max_tabs_undo", 0);
user_pref("image.mem.surfacecache_max_size_kb", 16384); // 16MB image cache
user_pref("browser.cache.memory.capacity", 65536);      // 64MB memory cache
user_pref("javascript.options.mem.max_tree_cache_entries", 20);
user_pref("accessibility.force_disabled", 1);           // Huge RAM saver
user_pref("browser.safebrowsing.malware.enabled", false);
user_pref("browser.safebrowsing.phishing.enabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("reader.parse-on-load.enabled", false);
EOF
user_pref("browser.sessionhistory.max_total_viewers", 0);
user_pref("browser.tabs.max_tabs_undo", 0);
user_pref("image.mem.surfacecache_max_size_kb", 16384); // 16MB image cache
user_pref("browser.cache.memory.capacity", 65536);      // 64MB memory cache
user_pref("javascript.options.mem.max_tree_cache_entries", 20);
user_pref("accessibility.force_disabled", 1);           // Huge RAM saver
user_pref("browser.safebrowsing.malware.enabled", false);
user_pref("browser.safebrowsing.phishing.enabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("reader.parse-on-load.enabled", false);
EOF

    # 4. Create userChrome.css (Safe UI hiding)
    cat > "$profile_path/chrome/userChrome.css" <<'EOF'
#nav-bar, #TabsToolbar, #PersonalToolbar { visibility: collapse !important; }
#sidebar-box { visibility: collapse !important; min-width: 0 !important; width: 0 !important; }
#navigator-toolbox { border: none !important; }
.zen-sidebar-box, #zen-sidebar-icons-wrapper, #zen-sidebar-toggle-button, #zen-sidebar-hover-trigger { display: none !important; }
EOF

    # 5. Shortcuts (Fully disabled except Reload)
    if [ -f "$DEFAULT_SHORTCUTS" ]; then
        jq '.shortcuts |= map(. + {disabled: true})' "$DEFAULT_SHORTCUTS" > "$profile_path/zen-keyboard-shortcuts.json"
    fi

    # 6. Simple Desktop Launcher
    mkdir -p "$HOME/.local/share/applications"
    cat > "$HOME/.local/share/applications/$app_name-wrapper.desktop" <<EOF
[Desktop Entry]
Name=$(tr '[:lower:]' '[:upper:]' <<< ${app_name:0:1})${app_name:1} (Zen Wrapper)
Exec=$ZEN_BIN --new-instance --name ${profile_name} --class ${profile_name} -P ${profile_name} $url
Terminal=false
Type=Application
Icon=$app_name
StartupWMClass=${profile_name}
EOF
    chmod +x "$HOME/.local/share/applications/$app_name-wrapper.desktop"
}

# Mindkét app létrehozása
create_simple_wrapper "spotify" "https://open.spotify.com"
create_simple_wrapper "messenger" "https://www.messenger.com"

# Takarítás
rm -f "$HOME/.dotfiles/zen-wrappers/launcher.sh"

echo "Kész! Spotify és Messenger wrapperek telepítve (egyszerű, stabil mód)."
