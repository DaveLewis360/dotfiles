pragma ComponentBehavior: Bound

import qs.components
import qs.components.filedialog
import qs.config
import Quickshell
import Quickshell.Widgets
import QtQuick
import QtQuick.Layouts

Item {
    id: root

    required property PersistentProperties visibilities
    required property PersistentProperties state
    required property FileDialog facePicker
    readonly property real nonAnimWidth: view.implicitWidth + viewWrapper.anchors.leftMargin + viewWrapper.anchors.rightMargin
    readonly property real nonAnimHeight: tabs.implicitHeight + tabs.anchors.topMargin + view.implicitHeight + viewWrapper.anchors.topMargin + viewWrapper.anchors.bottomMargin

    implicitWidth: nonAnimWidth
    implicitHeight: nonAnimHeight

    Tabs {
        id: tabs

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        // Add bar height to top margin to push content below the "MiniDash" area
        // Subtract 30px to close the visual gap
        anchors.topMargin: Config.bar.sizes.innerWidth - 30
        anchors.margins: Appearance.padding.large

        nonAnimWidth: root.nonAnimWidth - anchors.margins * 2
        state: root.state
    }

    ClippingRectangle {
        id: viewWrapper

        anchors.top: tabs.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: Appearance.padding.large
        anchors.rightMargin: Appearance.padding.large
        anchors.topMargin: Appearance.padding.large
        anchors.bottomMargin: Appearance.padding.large

        radius: Appearance.rounding.normal
        color: "transparent"

        Flickable {
            id: view

            readonly property int currentIndex: root.state.currentTab
            readonly property Item currentItem: row.children[currentIndex]

            anchors.fill: parent

            flickableDirection: Flickable.HorizontalFlick

            implicitWidth: currentItem.implicitWidth
            implicitHeight: currentItem.implicitHeight

            contentX: currentItem.x
            contentWidth: row.implicitWidth
            contentHeight: row.implicitHeight

            onContentXChanged: {
                if (!moving)
                    return;

                const x = contentX - currentItem.x;
                if (x > currentItem.implicitWidth / 2)
                    root.state.currentTab = Math.min(root.state.currentTab + 1, tabs.count - 1);
                else if (x < -currentItem.implicitWidth / 2)
                    root.state.currentTab = Math.max(root.state.currentTab - 1, 0);
            }

            onDragEnded: {
                const x = contentX - currentItem.x;
                if (x > currentItem.implicitWidth / 10)
                    root.state.currentTab = Math.min(root.state.currentTab + 1, tabs.count - 1);
                else if (x < -currentItem.implicitWidth / 10)
                    root.state.currentTab = Math.max(root.state.currentTab - 1, 0);
                else
                    contentX = Qt.binding(() => currentItem.x);
            }

            RowLayout {
                id: row

                Pane {
                    index: 0
                    sourceComponent: Dash {
                        visibilities: root.visibilities
                        state: root.state
                        facePicker: root.facePicker
                    }
                }

                Pane {
                    index: 1
                    sourceComponent: Media {
                        visibilities: root.visibilities
                    }
                }

                Pane {
                    index: 2
                    sourceComponent: Performance {}
                }

                Pane {
                    index: 3
                    sourceComponent: Weather {}
                }
            }

            Behavior on contentX {
                Anim {}
            }
        }
    }

    Behavior on implicitWidth {
        Anim {
            duration: Appearance.anim.durations.expressiveDefaultSpatial
            easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
        }
    }

    Behavior on implicitHeight {
        Anim {
            duration: Appearance.anim.durations.expressiveDefaultSpatial
            easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
        }
    }

    component Pane: Loader {
        id: pane

        required property int index

        Layout.alignment: Qt.AlignTop

        Component.onCompleted: active = Qt.binding(() => {
            // Always keep current tab loaded
            if (pane.index === view.currentIndex)
                return true;
            const vx = Math.floor(view.visibleArea.xPosition * view.contentWidth);
            const vex = Math.floor(vx + view.visibleArea.widthRatio * view.contentWidth);
            return (vx >= x && vx <= x + implicitWidth) || (vex >= x && vex <= x + implicitWidth);
        })
    }
}
