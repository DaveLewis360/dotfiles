pragma ComponentBehavior: Bound

import qs.components
import qs.services
import qs.config
import QtQuick
import QtQuick.Shapes

ShapePath {
    id: root

    required property var wrapper
    
    // Morphing properties
    property real w: 0
    property real h: 0
    property real targetRounding: Appearance.rounding.normal
    property bool isTopHanging: true // New flag for the top-attached look

    readonly property real roundingY: h < targetRounding * 2 ? h / 2 : targetRounding

    strokeWidth: -1
    fillColor: Colours.glassBackground

    // THE MORPHING SHAPE
    // Start at top-left
    
    // Top-left corner (Square if hanging, rounded if floating)
    PathArc {
        relativeX: root.targetRounding
        relativeY: root.isTopHanging ? 0 : root.roundingY
        radiusX: root.targetRounding
        radiusY: root.roundingY
        direction: PathArc.Clockwise
    }

    // Top line
    PathLine {
        relativeX: root.w - root.targetRounding * 2
        relativeY: 0
    }

    // Top-right corner
    PathArc {
        relativeX: root.targetRounding
        relativeY: root.isTopHanging ? 0 : -root.roundingY
        radiusX: root.targetRounding
        radiusY: root.roundingY
        direction: PathArc.Clockwise
    }

    // Right side
    PathLine {
        relativeX: 0
        relativeY: root.h - (root.isTopHanging ? root.roundingY : root.roundingY * 2)
    }

    // Bottom-right corner (Always rounded)
    PathArc {
        relativeX: -root.targetRounding
        relativeY: root.roundingY
        radiusX: root.targetRounding
        radiusY: root.roundingY
        direction: PathArc.Clockwise
    }

    // Bottom line
    PathLine {
        relativeX: -(root.w - root.targetRounding * 2)
        relativeY: 0
    }

    // Bottom-left corner (Always rounded)
    PathArc {
        relativeX: -root.targetRounding
        relativeY: -root.roundingY
        radiusX: root.targetRounding
        radiusY: root.roundingY
        direction: PathArc.Clockwise
    }

    // Left side (Closing back to top-left)
    PathLine {
        relativeX: 0
        relativeY: -(root.h - (root.isTopHanging ? root.roundingY : root.roundingY * 2))
    }

    Behavior on fillColor { CAnim {} }
    
    // Smooth transitions for dimensions
    Behavior on w { Anim { duration: Appearance.anim.durations.expressiveDefaultSpatial; easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial } }
    Behavior on h { Anim { duration: Appearance.anim.durations.expressiveDefaultSpatial; easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial } }
}