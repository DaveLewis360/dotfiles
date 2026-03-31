const { app, BrowserWindow, session } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

let targetUrl = process.argv[2] || 'https://www.messenger.com';
let appId = process.argv[3] || 'caelestia-messenger';
let cssPath = path.join(os.homedir(), '.config/caelestia/web-apps', `${appId}.css`);

function createWindow() {
    const win = new BrowserWindow({
        width: 1280,
        height: 800,
        title: "Messenger",
        transparent: true,
        frame: true, // Megtartjuk a keretet, de a tartalom átlátszó lesz
        backgroundColor: '#00000000',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            devTools: true
        }
    });

    win.setMenuBarVisibility(false); // Eltünteti a File/Edit/stb menüt

    // Felhasználói ügynök (User Agent) a hívásokhoz
    win.webContents.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36");

    // CSS Injekció funkció
    const injectCSS = () => {
        if (fs.existsSync(cssPath)) {
            const css = fs.readFileSync(cssPath, 'utf8');
            win.webContents.insertCSS(css);
        }
    };

    win.webContents.on('did-finish-load', injectCSS);
    win.webContents.on('did-navigate', injectCSS);

    // Automatikus CSS frissítés (Hot Reload)
    fs.watch(path.dirname(cssPath), (eventType, filename) => {
        if (filename === `${appId}.css`) {
            injectCSS();
        }
    });

    // Kamera/Mikrofon engedélyezése automatikusan
    session.defaultSession.setPermissionCheckHandler((webContents, permission) => {
        return true;
    });
    session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
        callback(true);
    });

    win.loadURL(targetUrl);
}

// GPU hackek az átlátszósághoz
app.commandLine.appendSwitch('enable-transparent-visuals');
app.commandLine.appendSwitch('disable-gpu-compositing');

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});
