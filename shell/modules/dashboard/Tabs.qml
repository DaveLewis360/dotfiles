pragma ComponentBehavior: Bound

import qs.components
import qs.components.controls
import qs.services
import qs.config
import Quickshell
import Quickshell.Widgets
import QtQuick
import QtQuick.Controls

Item {
    id: root

    required property real nonAnimWidth
    required property PersistentProperties state
    readonly property alias count: bar.count

    implicitHeight: bar.implicitHeight + indicator.implicitHeight + indicator.anchors.topMargin + separator.implicitHeight

    // More robust tab visibility logic
    TabBar {
        id: bar

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top

        currentIndex: root.state.currentTab
        background: null

        onCurrentIndexChanged: root.state.currentTab = currentIndex

        Tab {
            id: dashTab
            visible: Config.dashboard.showDashboard
            iconName: "dashboard"
            text: qsTr("Dashboard")
            width: visible ? (root.nonAnimWidth / bar.visibleCount) : 0
        }

        Tab {
            id: mediaTab
            visible: Config.dashboard.showMedia
            iconName: "queue_music"
            text: qsTr("Media")
            width: visible ? (root.nonAnimWidth / bar.visibleCount) : 0
        }

        Tab {
            id: perfTab
            visible: Config.dashboard.showPerformance
            iconName: "speed"
            text: qsTr("Performance")
            width: visible ? (root.nonAnimWidth / bar.visibleCount) : 0
        }

        Tab {
            id: weatherTab
            visible: Config.dashboard.showWeather
            iconName: "cloud"
            text: qsTr("Weather")
            width: visible ? (root.nonAnimWidth / bar.visibleCount) : 0
        }

        readonly property int visibleCount: (dashTab.visible ? 1 : 0) + (mediaTab.visible ? 1 : 0) + (perfTab.visible ? 1 : 0) + (weatherTab.visible ? 1 : 0)
    }

    Item {
        id: indicator

        anchors.top: bar.bottom
        anchors.topMargin: Config.dashboard.sizes.tabIndicatorSpacing

        implicitWidth: bar.currentItem ? bar.currentItem.implicitWidth : 0
        implicitHeight: Config.dashboard.sizes.tabIndicatorHeight

        // Correct X calculation based on visible items
        x: {
            if (!bar.currentItem) return 0;
            let offset = 0;
            for (let i = 0; i < bar.currentIndex; i++) {
                if (bar.contentModel.get(i).visible) {
                    offset += root.nonAnimWidth / bar.visibleCount;
                }
            }
            return offset + (root.nonAnimWidth / bar.visibleCount - bar.currentItem.implicitWidth) / 2;
        }

        clip: true

        StyledRect {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            implicitHeight: parent.implicitHeight * 2

            color: Colours.palette.m3primary
            radius: Appearance.rounding.full
        }

        Behavior on x {
            Anim {}
        }

        Behavior on implicitWidth {
            Anim {}
        }
    }

    StyledRect {
        id: separator

        anchors.top: indicator.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        implicitHeight: 1
        color: Colours.palette.m3outlineVariant
    }

    component Tab: TabButton {
        id: tab

        required property string iconName
        readonly property bool current: TabBar.tabBar.currentItem === this

        background: MouseArea {
            id: mouse
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor

            onPressed: event => {
                bar.currentIndex = tab.TabBar.index;
            }

            StyledClippingRect {
                id: bgWrapper

                anchors.fill: parent
                implicitHeight: parent.height + Config.dashboard.sizes.tabIndicatorSpacing * 2

                color: "transparent"
                radius: Appearance.rounding.normal

                StyledRect {
                    anchors.fill: parent
                    radius: parent.radius

                    color: tab.current ? Colours.palette.m3primary : Colours.palette.m3onSurface
                    opacity: mouse.pressed ? 0.1 : mouse.containsMouse ? 0.08 : 0

                    Behavior on opacity {
                        Anim {}
                    }
                }
            }
        }

        contentItem: Item {
            implicitWidth: Math.max(icon.width, label.width)
            implicitHeight: icon.height + label.height

            MaterialIcon {
                id: icon
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: label.top
                text: tab.iconName
                color: tab.current ? Colours.palette.m3primary : Colours.palette.m3onSurfaceVariant
                fill: tab.current ? 1 : 0
                font.pointSize: Appearance.font.size.large
                Behavior on fill { Anim {} }
            }

            StyledText {
                id: label
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                text: tab.text
                color: tab.current ? Colours.palette.m3primary : Colours.palette.m3onSurfaceVariant
            }
        }
    }
}
