const { app, BrowserWindow, session, globalShortcut } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

// --- PATHS ---
const appId = 'caelestia-spotify';
const configCssPath = path.join(os.homedir(), '.config/caelestia/web-apps', `${appId}.css`);
const userDataPath = path.join(os.homedir(), '.config/caelestia/spotify-profile');
const widevineDir = path.join(os.homedir(), '.config/caelestia/widevine');
const widevinePath = path.join(widevineDir, 'libwidevinecdm.so');
const widevineVersion = '4.10.2934.0';

// --- DRM (Widevine) SETUP ---
// We set these switches BEFORE app is ready
app.commandLine.appendSwitch('widevine-cdm-path', widevinePath);
app.commandLine.appendSwitch('widevine-cdm-version', widevineVersion);
app.commandLine.appendSwitch('enable-widevine-cdm');

// --- PERFORMANCE & RICE HACKS ---
app.commandLine.appendSwitch('enable-transparent-visuals');
app.commandLine.appendSwitch('disable-gpu-compositing');
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

// Force profile path
app.setPath('userData', userDataPath);

function createWindow() {
    const spotifySession = session.defaultSession;

    const win = new BrowserWindow({
        width: 1400,
        height: 900,
        title: "Spotify (Caelestia)",
        transparent: true,
        backgroundColor: '#00000000',
        autoHideMenuBar: true,
        webPreferences: {
            session: spotifySession,
            nodeIntegration: false,
            contextIsolation: true,
            webSecurity: true, // MUST BE TRUE for Widevine
            sandbox: false, // Sometimes needed for Widevine initialization on Linux
            autoplayPolicy: 'no-user-gesture-required'
        }
    });

    // Use a very trusted UA (Edge on Windows is great for Spotify Web)
    const trustedUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0";
    win.webContents.setUserAgent(trustedUA);

    const injectCSS = () => {
        if (fs.existsSync(configCssPath)) {
            const css = fs.readFileSync(configCssPath, 'utf8');
            const cssClean = css.replace(/@-moz-document domain\("spotify.com"\) \{/, "").replace(/\}$/, "");
            win.webContents.insertCSS(cssClean, { cssOrigin: 'user' });
            
            // Force JS transparency
            win.webContents.executeJavaScript(`
                document.documentElement.style.background = 'transparent';
                document.body.style.background = 'transparent';
            `);
        }
    };

    win.webContents.on('did-finish-load', injectCSS);
    win.webContents.on('did-navigate', injectCSS);

    // --- MEDIA KEYS ---
    const registerMediaKeys = () => {
        const keyMap = {
            'MediaPlayPause': "document.querySelector('[data-testid=\"control-button-playpause\"]').click()",
            'MediaNextTrack': "document.querySelector('[data-testid=\"control-button-skip-forward\"]').click()",
            'MediaPreviousTrack': "document.querySelector('[data-testid=\"control-button-skip-back\"]').click()"
        };
        Object.keys(keyMap).forEach(key => {
            globalShortcut.register(key, () => {
                win.webContents.executeJavaScript(keyMap[key]).catch(() => {});
            });
        });
    };
    registerMediaKeys();

    // DRM Permission Handling
    spotifySession.setPermissionCheckHandler(() => true);
    spotifySession.setPermissionRequestHandler((webContents, permission, callback) => {
        if (permission === 'mediaKeySystem') {
            callback(true);
        } else {
            callback(true);
        }
    });

    win.loadURL('https://open.spotify.com');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    globalShortcut.unregisterAll();
    if (process.platform !== 'darwin') app.quit();
});
