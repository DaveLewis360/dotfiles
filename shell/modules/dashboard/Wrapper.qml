pragma ComponentBehavior: Bound

import qs.components
import qs.components.filedialog
import qs.config
import qs.utils
import Caelestia
import Quickshell
import QtQuick

Item {
    id: root

    required property PersistentProperties visibilities
    readonly property PersistentProperties dashState: PersistentProperties {
        property int currentTab
        property date currentDate: new Date()

        reloadableId: "dashboardState"
    }
    readonly property FileDialog facePicker: FileDialog {
        title: qsTr("Select a profile picture")
        filterLabel: qsTr("Image files")
        filters: Images.validImageExtensions
        onAccepted: path => {
            if (CUtils.copyFile(Qt.resolvedUrl(path), Qt.resolvedUrl(`${Paths.home}/.face`)))
                Quickshell.execDetached(["notify-send", "-a", "caelestia-shell", "-u", "low", "-h", `STRING:image-path:${path}`, "Profile picture changed", `Profile picture changed to ${Paths.shortenHome(path)}`]);
            else
                Quickshell.execDetached(["notify-send", "-a", "caelestia-shell", "-u", "critical", "Unable to change profile picture", `Failed to change profile picture to ${Paths.shortenHome(path)}`]);
        }
    }

    readonly property real nonAnimHeight: state === "visible" ? (content.item?.nonAnimHeight ?? 0) : 0
    readonly property real nonAnimWidth: state === "visible" ? (content.item?.nonAnimWidth ?? 0) : 0

    visible: height > 0
    implicitHeight: 0
    implicitWidth: content.implicitWidth

    onStateChanged: {
        if (state === "visible" && timer.running) {
            timer.triggered();
            timer.stop();
        }
    }

    states: State {
        name: "visible"
        when: root.visibilities.dashboard && Config.dashboard.enabled

        PropertyChanges {
            root.implicitHeight: content.implicitHeight
        }
    }

    // MODIFIED TRANSITIONS FOR MORPHING EFFECT
    transitions: [
        Transition {
            from: ""
            to: "visible"

            // Instead of animating height (curtain effect), we snap the height 
            // and animate the content's opacity and scale to match the background morph.
            
            // Snap height immediately so space is reserved
            PropertyAction {
                target: root
                property: "implicitHeight"
            }
            
            // Animate content appearance
            ParallelAnimation {
                Anim {
                    target: content
                    property: "opacity"
                    from: 0
                    to: 1
                    duration: Appearance.anim.durations.expressiveDefaultSpatial
                    easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
                }
                Anim {
                    target: content
                    property: "scale"
                    from: 0.8
                    to: 1
                    duration: Appearance.anim.durations.expressiveDefaultSpatial
                    easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
                }
            }
        },
        Transition {
            from: "visible"
            to: ""

            // On close, we can still animate height or do a reverse fade
            // Keeping the original height animation for closing might look good combined with the background shrinking
            Anim {
                target: root
                property: "implicitHeight"
                duration: Appearance.anim.durations.expressiveDefaultSpatial
                easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
            }
            
            // Fade out content slightly faster than the background shrink
            Anim {
                target: content
                property: "opacity"
                to: 0
                duration: Appearance.anim.durations.expressiveDefaultSpatial
            }
        }
    ]

    Timer {
        id: timer

        running: true
        interval: Appearance.anim.durations.extraLarge
        onTriggered: {
            content.active = Qt.binding(() => (root.visibilities.dashboard && Config.dashboard.enabled) || root.visible);
            content.visible = true;
        }
    }

    Loader {
        id: content

        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        
        // Ensure the content grows from the top (where the bar is)
        transformOrigin: Item.Top

        visible: false
        active: true

        sourceComponent: Content {
            visibilities: root.visibilities
            state: root.dashState
            facePicker: root.facePicker
        }
    }
}