pragma Singleton

import qs.config
import qs.utils
import Caelestia.Models
import Quickshell
import Quickshell.Io
import QtQuick

Searcher {
    id: root

    readonly property string currentNamePath: `${Paths.state}/wallpaper/path.txt`
    readonly property list<string> smartArg: Config.services.smartScheme ? [] : ["--no-smart"]

    property bool showPreview: false
    readonly property string current: showPreview ? previewPath : actualCurrent
    property string previewPath
    property string actualCurrent
    property bool previewColourLock

    function setWallpaper(path: string): void {
        actualCurrent = path;
        
        const isVideo = path.endsWith(".mp4") || path.endsWith(".webm") || path.endsWith(".mkv") || path.endsWith(".mov") || path.endsWith(".gif");

        // Update the state file so Caelestia knows what's selected (and can hide the image layer if video)
        Quickshell.execDetached(["bash", "-c", `echo -n "${path}" > ${root.currentNamePath}`]);

        if (isVideo) {
            // It's a video: Launch mpvpaper
            // We kill any existing instance first, then start new one
            // Using nohup to ensure it survives shell closure if needed, though & should work
            Quickshell.execDetached(["bash", "-c", `pkill mpvpaper; nohup mpvpaper -o "no-audio --loop --video-zoom=0.2" eDP-1 "${path}" >/dev/null 2>&1 &`]);
            
            // Generate color scheme from video thumbnail
            // Use /tmp to ensure write access and avoid path issues
            const thumbPath = "/tmp/video_thumb.jpg";
            // Extract the first frame
            // Then run 'wallpaper -f' on the thumbnail to generate colors correctly (this overwrites path.txt)
            // Then IMMEDIATELY overwrite path.txt back to the video path so the UI knows it's a video
            const cmd = `ffmpeg -y -i "${path}" -vframes 1 "${thumbPath}" && caelestia wallpaper -f "${thumbPath}" ${root.smartArg.join(" ")} && echo -n "${path}" > ${root.currentNamePath}`;
            
            Quickshell.execDetached(["bash", "-c", cmd]);
        } else {
            // It's an image: Kill mpvpaper
            Quickshell.execDetached(["pkill", "mpvpaper"]);
            
            // Just use the standard command for images
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
    useFuzzy: Config.launcher.useFuzzy.wallpapers
    extraOpts: useFuzzy ? ({}) : ({
            forward: false
        })

    IpcHandler {
        target: "wallpaper"

        function get(): string {
            return root.actualCurrent;
        }

        function set(path: string): void {
            root.setWallpaper(path);
        }

        function list(): string {
            return root.list.map(w => w.path).join("\n");
        }
    }

    FileView {
        path: root.currentNamePath
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            root.actualCurrent = text().trim();
            root.previewColourLock = false;
        }
    }

    FileSystemModel {
        id: wallpapers

        recursive: true
        path: Paths.wallsdir
        nameFilters: ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.mp4", "*.webm", "*.mkv", "*.mov", "*.gif"]
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
