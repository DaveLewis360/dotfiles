pragma ComponentBehavior: Bound

import qs.components
import qs.services
import qs.config
import Quickshell.Services.SystemTray
import QtQuick

StyledRect {
    id: root

    readonly property alias layout: layout
    readonly property alias items: items
    readonly property alias expandIcon: expandIcon

    readonly property int padding: Config.bar.tray.background ? Appearance.padding.normal : Appearance.padding.small
    readonly property int spacing: Config.bar.tray.background ? Appearance.spacing.small : 0

    property bool expanded

    readonly property real nonAnimWidth: {
        if (!Config.bar.tray.compact)
            return layout.implicitWidth + padding * 2;
        return (expanded ? expandIcon.implicitWidth + layout.implicitWidth + spacing : expandIcon.implicitWidth) + padding * 2;
    }

    clip: true
    visible: width > 0

    implicitHeight: Config.bar.sizes.innerWidth
    implicitWidth: nonAnimWidth

    color: Qt.alpha(Colours.glassBackground, (Config.bar.tray.background && items.count > 0) ? Colours.glassBackground.a : 0)
    radius: Appearance.rounding.full

    Row {
        id: layout

        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: root.padding
        spacing: Appearance.spacing.small

        opacity: root.expanded || !Config.bar.tray.compact ? 1 : 0

        add: Transition {
            Anim {
                properties: "scale"
                from: 0
                to: 1
                easing.bezierCurve: Appearance.anim.curves.standardDecel
            }
        }

        move: Transition {
            Anim {
                properties: "scale"
                to: 1
                easing.bezierCurve: Appearance.anim.curves.standardDecel
            }
            Anim {
                properties: "x,y"
            }
        }

        Repeater {
            id: items

            model: SystemTray.items

            TrayItem {}
        }

        Behavior on opacity {
            Anim {}
        }
    }

    Loader {
        id: expandIcon

        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left

        active: Config.bar.tray.compact

        sourceComponent: Item {
            implicitHeight: expandIconInner.implicitHeight
            implicitWidth: expandIconInner.implicitWidth - Appearance.padding.small * 2

            MaterialIcon {
                id: expandIconInner

                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: Config.bar.tray.background ? Appearance.padding.small : -Appearance.padding.small
                text: "chevron_left"
                font.pointSize: Appearance.font.size.large
                rotation: root.expanded ? 180 : 0

                Behavior on rotation {
                    Anim {}
                }

                Behavior on anchors.leftMargin {
                    Anim {}
                }
            }
        }
    }

    Behavior on implicitWidth {
        Anim {
            duration: Appearance.anim.durations.expressiveDefaultSpatial
            easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
        }
    }
}
