import qs.components
import qs.components.effects
import qs.services
import qs.config
import QtQuick

StyledRect {
    id: root

    anchors.verticalCenter: parent.verticalCenter

    required property int activeWsId
    required property Repeater workspaces
    required property Item mask

    readonly property int currentWsIdx: {
        let i = activeWsId - 1;
        while (i < 0)
            i += Config.bar.workspaces.shown;
        return i % Config.bar.workspaces.shown;
    }

    // X-based positioning (converted from Y for horizontal bar)
    // Use fixed size for indicator (circle)
    readonly property real indicatorSize: Config.bar.sizes.innerWidth - Appearance.padding.small * 2
    property real leading: workspaces.count > 0 ? workspaces.itemAt(currentWsIdx)?.x ?? 0 : 0
    property real trailing: workspaces.count > 0 ? workspaces.itemAt(currentWsIdx)?.x ?? 0 : 0
    property real currentSize: indicatorSize
    property real offset: Math.min(leading, trailing)
    property real size: {
        const s = Math.abs(leading - trailing) + currentSize;
        if (Config.bar.workspaces.activeTrail && lastWs > currentWsIdx) {
            const ws = workspaces.itemAt(lastWs);
            return ws ? Math.min(ws.x + ws.size - offset, s) : 0;
        }
        return s;
    }

    property int cWs
    property int lastWs

    onCurrentWsIdxChanged: {
        lastWs = cWs;
        cWs = currentWsIdx;
    }

    clip: true
    // Loader is anchored to layout.left, so we only need the item's x position within the layout
    x: offset
    implicitHeight: Config.bar.sizes.innerWidth - Appearance.padding.small * 2
    implicitWidth: size
    radius: Appearance.rounding.full
    color: Colours.palette.m3primary

    Colouriser {
        source: root.mask
        sourceColor: Colours.palette.m3onSurface
        colorizationColor: Colours.palette.m3onPrimary

        x: -parent.offset
        y: 0
        implicitWidth: root.mask.implicitWidth
        implicitHeight: root.mask.implicitHeight

        anchors.verticalCenter: parent.verticalCenter
    }

    Behavior on leading {
        enabled: Config.bar.workspaces.activeTrail

        EAnim {}
    }

    Behavior on trailing {
        enabled: Config.bar.workspaces.activeTrail

        EAnim {
            duration: Appearance.anim.durations.normal * 2
        }
    }

    Behavior on currentSize {
        enabled: Config.bar.workspaces.activeTrail

        EAnim {}
    }

    Behavior on offset {
        enabled: !Config.bar.workspaces.activeTrail

        EAnim {}
    }

    Behavior on size {
        enabled: !Config.bar.workspaces.activeTrail

        EAnim {}
    }

    component EAnim: Anim {
        easing.bezierCurve: Appearance.anim.curves.emphasized
    }
}
