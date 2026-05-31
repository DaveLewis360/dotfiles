pragma ComponentBehavior: Bound

import qs.components
import qs.components.effects
import qs.services
import qs.config
import Quickshell
import Caelestia.Services
import Quickshell.Services.Mpris
import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes
import QtQuick.Controls
import QtQml.Models

Item {
    id: root
    objectName: "miniDash"

    required property PersistentProperties visibilities
    
    readonly property bool hasMedia: !!Players.active && Players.active.trackTitle.length > 0
    readonly property bool isPlaying: Players.active?.isPlaying ?? false
    
    readonly property int barPadding: Math.max(Appearance.padding.smaller, Config.border.thickness)
    
    // Dynamic width calculation based on the widest content
    // This ensures the capsule is compact but accommodates both pages
    readonly property real systemWidth: systemLayout.implicitWidth
    readonly property real mediaWidth: mediaLayout.implicitWidth
    readonly property real pillWidth: Math.max(systemWidth, mediaWidth) + Appearance.padding.large * 2
    
    implicitWidth: pillWidth
    height: parent.height

    Component.onCompleted: SystemUsage.refCount++
    Component.onDestruction: SystemUsage.refCount--

    ServiceRef {
        service: Audio.cava
    }

    // Auto-switch to media page when music starts playing
    onIsPlayingChanged: {
        if (isPlaying && hasMedia) {
            view.currentIndex = 1; // Media page
        }
    }

    StyledRect {
        id: bg
        anchors.fill: parent
        anchors.topMargin: -root.barPadding
        anchors.bottomMargin: 0
        
        color: "transparent" // Let external background handle the visual
        
        topLeftRadius: 0
        topRightRadius: 0
        bottomLeftRadius: Appearance.rounding.normal
        bottomRightRadius: Appearance.rounding.normal

        // Swipe View for Pages
        ListView {
            id: view
            anchors.fill: parent
            
            orientation: ListView.Horizontal
            snapMode: ListView.SnapOneItem
            highlightRangeMode: ListView.StrictlyEnforceRange
            clip: true
            
            boundsBehavior: Flickable.StopAtBounds

            model: ObjectModel {
                // PAGE 1: SYSTEM INFO
                Item {
                    width: view.width
                    height: view.height
                    
                    RowLayout {
                        id: systemLayout // ID for width calculation
                        anchors.centerIn: parent
                        spacing: Appearance.spacing.large

                        // CPU
                        Row {
                            spacing: Appearance.spacing.small
                            Layout.alignment: Qt.AlignVCenter
                            MaterialIcon { text: "memory"; color: Colours.palette.m3primary; font.pointSize: 18 }
                            Column {
                                spacing: -4
                                StyledText { text: Math.round(SystemUsage.cpuPerc * 100) + "%"; font.pointSize: 12; font.bold: true }
                                StyledText { text: Math.round(SystemUsage.cpuTemp) + "°C"; font.pointSize: 10; color: SystemUsage.cpuTemp > 75 ? Colours.palette.m3error : Colours.palette.m3onSurfaceVariant }
                            }
                        }

                        Rectangle { width: 1; height: 20; color: Colours.palette.m3outlineVariant; opacity: 0.2 }

                        // RAM
                        Row {
                            spacing: Appearance.spacing.small
                            Layout.alignment: Qt.AlignVCenter
                            MaterialIcon { text: "memory_alt"; color: Colours.palette.m3secondary; font.pointSize: 18 }
                            Column {
                                spacing: -4
                                StyledText { text: Math.round(SystemUsage.memPerc * 100) + "%"; font.pointSize: 12; font.bold: true }
                                StyledText { text: (SystemUsage.memUsed / 1024 / 1024).toFixed(1) + "G"; font.pointSize: 10; color: Colours.palette.m3onSurfaceVariant }
                            }
                        }

                        Rectangle { width: 1; height: 20; color: Colours.palette.m3outlineVariant; opacity: 0.2 }

                        // Disk
                        Row {
                            spacing: Appearance.spacing.small
                            Layout.alignment: Qt.AlignVCenter
                            MaterialIcon { text: "hard_drive"; color: Colours.palette.m3tertiary; font.pointSize: 18 }
                            Column {
                                spacing: -4
                                StyledText { text: Math.round(SystemUsage.storagePerc * 100) + "%"; font.pointSize: 12; font.bold: true }
                                StyledText { text: "DISK"; font.pointSize: 10; color: Colours.palette.m3onSurfaceVariant }
                            }
                        }

                        // GPU
                        Row {
                            spacing: Appearance.spacing.small
                            visible: SystemUsage.gpuPerc >= 0
                            Layout.alignment: Qt.AlignVCenter
                            
                            Rectangle { width: 1; height: 20; color: Colours.palette.m3outlineVariant; opacity: 0.2; visible: parent.visible; }
                            // Spacer
                            Item { width: 8; height: 1; visible: SystemUsage.gpuPerc >= 0 }

                            MaterialIcon { text: "videogame_asset"; color: Colours.palette.m3primary; font.pointSize: 18 }
                            Column {
                                spacing: -4
                                StyledText { text: Math.round(SystemUsage.gpuPerc * 100) + "%"; font.pointSize: 12; font.bold: true }
                                StyledText { text: Math.round(SystemUsage.gpuTemp) + "°C"; font.pointSize: 10; color: SystemUsage.gpuTemp > 75 ? Colours.palette.m3error : Colours.palette.m3onSurfaceVariant }
                            }
                        }
                    }
                }

                // PAGE 2: MEDIA INFO
                Item {
                    width: view.width
                    height: view.height
                    
                    StyledText {
                        anchors.centerIn: parent
                        text: qsTr("No media playing")
                        visible: !root.hasMedia
                        color: Colours.palette.m3onSurfaceVariant
                        font.italic: true
                    }

                    RowLayout {
                        id: mediaLayout // ID for width calculation
                        anchors.centerIn: parent
                        spacing: Appearance.spacing.normal
                        visible: root.hasMedia

                        Item {
                            implicitWidth: 46; implicitHeight: 46
                            Shape {
                                id: visualiser
                                anchors.fill: parent; anchors.margins: -4 
                                readonly property real centerX: width / 2; readonly property real centerY: height / 2; readonly property real innerR: cover.width / 2 + 2
                                preferredRendererType: Shape.CurveRenderer
                                data: visualiserBars.instances
                            }
                            Variants {
                                id: visualiserBars
                                model: Array.from({ length: Config.services.visualiserBars }, (_, i) => i)
                                ShapePath {
                                    id: visualiserBar
                                    required property int modelData
                                    readonly property real value: Math.max(0.1, Math.min(1, Audio.cava.values[modelData] || 0))
                                    readonly property real angle: modelData * 2 * Math.PI / Config.services.visualiserBars
                                    readonly property real magnitude: value * 8 
                                    readonly property real cos: Math.cos(angle); readonly property real sin: Math.sin(angle)
                                    strokeWidth: 2.2; strokeColor: Colours.palette.m3primary; capStyle: ShapePath.RoundCap; fillColor: "transparent"
                                    startX: visualiser.centerX + visualiser.innerR * cos; startY: visualiser.centerY + visualiser.innerR * sin
                                    PathLine { x: visualiser.centerX + (visualiser.innerR + visualiserBar.magnitude) * visualiserBar.cos; y: visualiser.centerY + (visualiser.innerR + visualiserBar.magnitude) * visualiserBar.sin }
                                    Behavior on strokeColor { CAnim {} }
                                }
                            }
                            StyledClippingRect {
                                id: cover; anchors.centerIn: parent; width: 34; height: 34; radius: 17; color: Colours.palette.m3surfaceContainer
                                MaterialIcon {
                                    anchors.centerIn: parent
                                    text: "music_note"
                                    font.pointSize: 14
                                    color: Colours.palette.m3onSurfaceVariant
                                    visible: image.status != Image.Ready
                                }
                                Image { id: image; anchors.fill: parent; source: (Players.active?.trackArtUrl || Players.lastArtUrl) ?? ""; fillMode: Image.PreserveAspectCrop }
                            }
                        }

                        Column {
                            Layout.alignment: Qt.AlignVCenter; Layout.preferredWidth: 160; spacing: -2
                            StyledText { width: parent.width; text: (Players.active?.trackTitle || ""); font.pointSize: 13; font.weight: 600; elide: Text.ElideRight; color: Colours.palette.m3primary }
                            StyledText { width: parent.width; text: (Players.active?.trackArtist || ""); font.pointSize: 11; elide: Text.ElideRight; color: Colours.palette.m3onSurfaceVariant; visible: text.length > 0 }
                        }

                        Row {
                            spacing: 4; Layout.alignment: Qt.AlignVCenter
                            // Disable buttons when dashboard is open
                            ControlBtn { icon: "skip_previous"; onClicked: Players.active?.previous(); enabled: (Players.active?.canGoPrevious ?? false) && !root.visibilities.dashboard }
                            ControlBtn { icon: root.isPlaying ? "pause" : "play_arrow"; onClicked: Players.active?.togglePlaying(); enabled: (Players.active?.canTogglePlaying ?? false) && !root.visibilities.dashboard }
                            ControlBtn { icon: "skip_next"; onClicked: Players.active?.next(); enabled: (Players.active?.canGoNext ?? false) && !root.visibilities.dashboard }
                        }
                    }
                }
            }
        }
    }

    component ControlBtn: Item {
        id: btn; required property string icon; signal clicked()
        implicitWidth: 38; implicitHeight: 38
        opacity: enabled ? 1 : 0.3
        StateLayer { anchors.fill: parent; radius: width / 2; onClicked: btn.clicked() }
        MaterialIcon { anchors.centerIn: parent; text: btn.icon; font.pointSize: 20; color: Colours.palette.m3onSurface }
    }
    
    // Fixed animations for open/close
    readonly property bool dashOpen: root.visibilities.dashboard
    enabled: !dashOpen
    opacity: dashOpen ? 0 : 1
    scale: dashOpen ? 0.85 : 1
    transform: Translate { y: dashOpen ? -15 : 0; Behavior on y { Anim { duration: Appearance.anim.durations.expressiveDefaultSpatial; easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial } } }
    Behavior on opacity { Anim { duration: Appearance.anim.durations.expressiveDefaultSpatial } }
    Behavior on scale { Anim { duration: Appearance.anim.durations.expressiveDefaultSpatial; easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial } }
}
