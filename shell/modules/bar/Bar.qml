pragma ComponentBehavior: Bound

import qs.services
import qs.config
import qs.components
import "popouts" as BarPopouts
import "components"
import "components/workspaces"
import Quickshell
import QtQuick
import QtQuick.Layouts

Item {
    id: root

    required property ShellScreen screen
    required property PersistentProperties visibilities
    required property BarPopouts.Wrapper popouts
    readonly property int hPadding: Appearance.padding.large
    property real trayX: 0
    
    // Export MiniDash width for the background morphing logic
    property alias pillWidth: miniDash.pillWidth

    implicitWidth: layout.implicitWidth
    implicitHeight: layout.implicitHeight

    function closeTray(): void {
        if (!Config.bar.tray.compact)
            return;

        for (let i = 0; i < repeater.count; i++) {
            const item = repeater.itemAt(i);
            if (item?.enabled && item.id === "tray") {
                item.item.expanded = false;
            }
        }
    }

    function checkPopout(x: real): void {
        const ch = layout.childAt(x, layout.height / 2) as WrappedLoader;

        if (ch?.id !== "tray")
            closeTray();

        if (!ch) {
            popouts.hasCurrent = false;
            return;
        }

        const id = ch.id;
        const left = ch.x;
        const item = ch.item;
        const itemWidth = item.implicitWidth;

        if (id === "statusIcons" && Config.bar.popouts.statusIcons) {
            const items = item.items;
            const icon = items.childAt(items.mapFromItem(root, x, 0).x, items.height / 2);
            if (icon) {
                popouts.currentName = icon.name;
                popouts.currentCenter = Qt.binding(() => icon.mapToItem(root, icon.implicitWidth / 2, 0).x);
                popouts.hasCurrent = true;
            }
        } else if (id === "tray" && Config.bar.popouts.tray) {
            const layout = item.layout;
            const localX = layout.mapFromItem(root, x, 0).x;
            if (!Config.bar.tray.compact || (item.expanded && !item.expandIcon.contains(item.expandIcon.mapFromItem(root, x, root.height / 2)))) {
                const trayItem = layout.childAt(localX, layout.height / 2);
                if (trayItem) {
                    // Find index of the tray item in the repeater
                    let index = -1;
                    for (let i = 0; i < item.items.count; i++) {
                        if (item.items.itemAt(i) === trayItem) {
                            index = i;
                            break;
                        }
                    }

                    if (index !== -1) {
                        popouts.currentName = `traymenu${index}`;
                        popouts.currentCenter = Qt.binding(() => trayItem.mapToItem(root, trayItem.implicitWidth / 2, 0).x);
                        popouts.hasCurrent = true;
                    } else {
                        popouts.hasCurrent = false;
                    }
                } else {
                    popouts.hasCurrent = false;
                }
            } else {
                popouts.hasCurrent = false;
                item.expanded = true;
            }
        } else if (id === "activeWindow" && Config.bar.popouts.activeWindow) {
            popouts.currentName = id.toLowerCase();
            popouts.currentCenter = item.mapToItem(root, itemWidth / 2, 0).x;
            popouts.hasCurrent = true;
        }
    }

    function handleWheel(x: real, angleDelta: point): void {
        const ch = layout.childAt(x, layout.height / 2) as WrappedLoader;
        if (ch?.id === "workspaces" && Config.bar.scrollActions.workspaces) {
            // Workspace scroll
            const mon = (Config.bar.workspaces.perMonitorWorkspaces ? Hypr.monitorFor(screen) : Hypr.focusedMonitor);
            const specialWs = mon?.lastIpcObject.specialWorkspace.name;
            if (specialWs?.length > 0)
                Hypr.dispatch(`togglespecialworkspace ${specialWs.slice(8)}`);
            else if (angleDelta.y < 0 || (Config.bar.workspaces.perMonitorWorkspaces ? mon.activeWorkspace?.id : Hypr.activeWsId) > 1)
                Hypr.dispatch(`workspace r${angleDelta.y > 0 ? "-" : "+"}1`);
        } else if (y < screen.height / 2 && Config.bar.scrollActions.volume) {
            // Volume scroll on top half
            if (angleDelta.y > 0)
                Audio.incrementVolume();
            else if (angleDelta.y < 0)
                Audio.decrementVolume();
        } else if (Config.bar.scrollActions.brightness) {
            // Brightness scroll on bottom half
            const monitor = Brightness.getMonitorForScreen(screen);
            if (angleDelta.y > 0)
                monitor.setBrightness(monitor.brightness + Config.services.brightnessIncrement);
            else if (angleDelta.y < 0)
                monitor.setBrightness(monitor.brightness - Config.services.brightnessIncrement);
        }
    }

    StyledRect {
        z: -1
        x: Math.max(0, root.trayX - layout.spacing)
        width: root.width - x
        height: root.height
        color: Colours.glassBackground
        radius: Config.border.rounding
    }

    RowLayout {
        id: layout
        anchors.fill: parent
        spacing: Appearance.spacing.normal
        property int hPadding: root.hPadding

        Repeater {
            id: repeater

            model: Config.bar.entries

            DelegateChooser {
                role: "id"

                DelegateChoice {
                    roleValue: "spacer"
                    delegate: WrappedLoader {
                        Layout.fillWidth: enabled
                    }
                }
                DelegateChoice {
                    roleValue: "logo"
                    delegate: WrappedLoader {
                        sourceComponent: OsIcon {}
                    }
                }
                DelegateChoice {
                    roleValue: "workspaces"
                    delegate: WrappedLoader {
                        sourceComponent: Workspaces {
                            screen: root.screen
                        }
                    }
                }
                DelegateChoice {
                    roleValue: "activeWindow"
                    delegate: WrappedLoader {
                        sourceComponent: ActiveWindow {
                            bar: layout
                            monitor: Brightness.getMonitorForScreen(root.screen)
                        }
                    }
                }
                DelegateChoice {
                    roleValue: "tray"
                    delegate: WrappedLoader {
                        sourceComponent: Tray {}
                    }
                }
                DelegateChoice {
                    roleValue: "clock"
                    delegate: WrappedLoader {
                        sourceComponent: Clock {}
                    }
                }
                DelegateChoice {
                    roleValue: "statusIcons"
                    delegate: WrappedLoader {
                        sourceComponent: StatusIcons {}
                    }
                }
                DelegateChoice {
                    roleValue: "power"
                    delegate: WrappedLoader {
                        sourceComponent: Power {
                            visibilities: root.visibilities
                        }
                    }
                }
            }
        }
    }

    // Perfectly centered Mini Dashboard Pill, anchored to the top
    MiniDash {
        id: miniDash
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        visibilities: root.visibilities
    }

    component WrappedLoader: Loader {
        required property bool enabled
        required property string id
        required property int index

        function findFirstEnabled(): Item {
            const count = repeater.count;
            for (let i = 0; i < count; i++) {
                const item = repeater.itemAt(i);
                if (item?.enabled)
                    return item;
            }
            return null;
        }

        function findLastEnabled(): Item {
            for (let i = repeater.count - 1; i >= 0; i--) {
                const item = repeater.itemAt(i);
                if (item?.enabled)
                    return item;
            }
            return null;
        }

        Layout.alignment: Qt.AlignVCenter

        // Cursed ahh thing to add padding to first and last enabled components
        Layout.leftMargin: findFirstEnabled() === this ? root.hPadding : 0
        Layout.rightMargin: findLastEnabled() === this ? root.hPadding : 0

        visible: enabled
        active: enabled

        onXChanged: if (id === "tray") root.trayX = x
        Component.onCompleted: if (id === "tray") root.trayX = x
    }
}
