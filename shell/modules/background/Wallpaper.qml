pragma ComponentBehavior: Bound

import qs.components
import qs.components.images
import qs.components.filedialog
import qs.services
import qs.config
import qs.utils
import QtQuick

Item {
    id: root

    property string source: Wallpapers.current
    property Image current: one

    anchors.fill: parent

    // Helper to detect if the source is a video (which we don't render natively)
    function isVideo(path: string): bool {
        const ext = path.split('.').pop().toLowerCase();
        return ["mp4", "webm", "mkv", "mov", "avi", "gif"].includes(ext);
    }

    onSourceChanged: {
        if (!source)
            current = null;
        else if (current === one)
            two.update();
        else
            one.update();
    }

    Component.onCompleted: {
        if (source)
            Qt.callLater(() => one.update());
    }

    Loader {
        anchors.fill: parent

        active: !root.source

        sourceComponent: StyledRect {
            color: Colours.tPalette.m3surfaceContainer

            Row {
                anchors.centerIn: parent
                spacing: Appearance.spacing.large

                MaterialIcon {
                    text: "sentiment_stressed"
                    color: Colours.palette.m3onSurfaceVariant
                    font.pointSize: Appearance.font.size.extraLarge * 5
                }

                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Appearance.spacing.small

                    StyledText {
                        text: qsTr("Wallpaper missing?")
                        color: Colours.palette.m3onSurfaceVariant
                        font.pointSize: Appearance.font.size.extraLarge * 2
                        font.bold: true
                    }

                    StyledRect {
                        implicitWidth: selectWallText.implicitWidth + Appearance.padding.large * 2
                        implicitHeight: selectWallText.implicitHeight + Appearance.padding.small * 2

                        radius: Appearance.rounding.full
                        color: Colours.palette.m3primary

                        FileDialog {
                            id: dialog

                            title: qsTr("Select a wallpaper")
                            filterLabel: qsTr("Media files")
                            // We allow selecting videos, but handle them externally
                            filters: ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.mp4", "*.webm", "*.mkv", "*.mov", "*.gif"]
                            onAccepted: path => Wallpapers.setWallpaper(path)
                        }

                        StateLayer {
                            radius: parent.radius
                            color: Colours.palette.m3onPrimary

                            function onClicked(): void {
                                dialog.open();
                            }
                        }

                        StyledText {
                            id: selectWallText

                            anchors.centerIn: parent

                            text: qsTr("Set it now!")
                            color: Colours.palette.m3onPrimary
                            font.pointSize: Appearance.font.size.large
                        }
                    }
                }
            }
        }
    }

    Img {
        id: one
    }

    Img {
        id: two
    }

    component Img: CachingImage {
        id: img

        property bool isVideoSource: false

        function update(): void {
            // Check video status first
            isVideoSource = root.isVideo(root.source);
            
            // Only set path if it's NOT a video, otherwise clear it to prevent errors
            if (!isVideoSource) {
                path = root.source;
            } else {
                path = "";
            }
            
            if (path === root.source || isVideoSource)
                root.current = this;
        }

        anchors.fill: parent

        // Direct binding for opacity and scale instead of states
        // This is more robust for switching between image and video modes
        opacity: (root.current === img && !img.isVideoSource) ? 1 : 0
        scale: (root.current === img) ? 1 : (Wallpapers.showPreview ? 1 : 0.8)

        onStatusChanged: {
            if (status === Image.Ready)
                root.current = this;
        }
        
        // If it's a video, consider it "ready" immediately
        onIsVideoSourceChanged: {
            if (isVideoSource)
                root.current = this;
        }

        transitions: Transition {
            Anim {
                target: img
                properties: "opacity,scale"
            }
        }
    }
}
