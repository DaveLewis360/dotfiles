pragma Singleton

import Caelestia.Config
import Caelestia.Models
import Quickshell
import Quickshell.Io
import QtQuick

Searcher {
    id: root

    readonly property string currentNamePath: `${Paths.state}/wallpaper/path.txt`
    readonly property list<string> smartArg: GlobalConfig.services.smartScheme ? [] : ["--no-smart"]

    property bool showPreview: false
    readonly property string current: showPreview ? previewPath : actualCurrent
    property string previewPath
    property string actualCurrent
    property bool previewColourLock
    readonly property bool currentIsVideo: isVideo(actualCurrent)
    property string activeMonitor: ""

    readonly property list<string> videoExtensions: ["mp4", "webm", "mkv", "mov", "gif"]

    function isVideo(path: string): bool {
        const ext = path.split('.').pop().toLowerCase();
        return videoExtensions.includes(ext);
    }

    function setWallpaper(path: string): void {
        actualCurrent = path;

        Quickshell.execDetached(["bash", "-c", `echo -n "${path}" > ${currentNamePath}`]);

        if (isVideo(path)) {
            Quickshell.execDetached(["bash", "-c", `pkill mpvpaper; nohup mpvpaper -o "no-audio --loop --video-zoom=0.2" "${activeMonitor}" "${path}" >/dev/null 2>&1 &`]);

            const thumbPath = "/tmp/video_thumb.jpg";
            const cmd = `ffmpeg -y -i "${path}" -vframes 1 "${thumbPath}" && caelestia wallpaper -f "${thumbPath}" ${smartArg.join(" ")} && echo -n "${path}" > ${currentNamePath}`;

            Quickshell.execDetached(["bash", "-c", cmd]);
        } else {
            Quickshell.execDetached(["pkill", "mpvpaper"]);
            Quickshell.execDetached(["caelestia", "wallpaper", "-f", path, ...smartArg]);
        }
    }

    function preview(path: string): void {
        previewPath = path;
        showPreview = true;

        if (Colours.scheme === "dynamic")
            getPreviewColoursProc.running = true;
    }

    function stopPreview(): void {
        showPreview = false;
        if (!previewColourLock)
            Colours.showPreview = false;
    }

    list: wallpapers.entries
    key: "relativePath"
    useFuzzy: GlobalConfig.launcher.useFuzzy.wallpapers
    extraOpts: useFuzzy ? ({}) : ({
            forward: false
        })

    IpcHandler {
        function get(): string {
            return root.actualCurrent;
        }

        function set(path: string): void {
            root.setWallpaper(path);
        }

        function list(): string {
            return root.list.map(w => w.path).join("\n");
        }

        target: "wallpaper"
    }

    FileView {
        path: root.currentNamePath
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            root.actualCurrent = text().trim();
            root.previewColourLock = false;
            if (isVideo(root.actualCurrent))
                root.setWallpaper(root.actualCurrent);
        }
    }

    FileSystemModel {
        id: wallpapers

        recursive: true
        path: Paths.wallsdir
        filter: FileSystemModel.Images
    }

    Process {
        id: getMonitorProc

        command: ["hyprctl", "activeworkspace", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    root.activeMonitor = data.monitor;
                } catch (e) {}
            }
        }
    }

    Process {
        id: getPreviewColoursProc

        command: ["caelestia", "wallpaper", "-p", root.previewPath, ...root.smartArg]
        stdout: StdioCollector {
            onStreamFinished: {
                Colours.load(text, true);
                Colours.showPreview = true;
            }
        }
    }
}
