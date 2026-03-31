pragma ComponentBehavior: Bound

import qs.components
import qs.services
import qs.config
import QtQuick
import QtQuick.Shapes

ShapePath {
    id: root

    required property Item wrapper
    
    // Use the same rounding as the rest of the UI
    readonly property real rounding: Appearance.rounding.normal
    
    // Smoothly transition the alpha based on whether the popout is active
    // This ensures it fades out nicely instead of leaving artifacts
    readonly property real activeAlpha: wrapper.hasCurrent ? 1.0 : 0.0
    
    strokeWidth: -1
    fillColor: Qt.rgba(Colours.glassBackground.r, Colours.glassBackground.g, Colours.glassBackground.b, activeAlpha)

    // Start at top-left corner (after rounding)
    // We use a small epsilon to avoid math errors at zero width/height
    readonly property real w: Math.max(root.rounding * 2, wrapper.width)
    readonly property real h: Math.max(root.rounding * 2, wrapper.height)

    PathArc {
        relativeX: root.rounding
        relativeY: -root.rounding
        radiusX: root.rounding
        radiusY: root.rounding
        direction: PathArc.Clockwise
    }
    
    PathLine {
        relativeX: root.w - root.rounding * 2
        relativeY: 0
    }
    
    PathArc {
        relativeX: root.rounding
        relativeY: root.rounding
        radiusX: root.rounding
        radiusY: root.rounding
        direction: PathArc.Clockwise
    }
    
    PathLine {
        relativeX: 0
        relativeY: root.h - root.rounding * 2
    }
    
    PathArc {
        relativeX: -root.rounding
        relativeY: root.rounding
        radiusX: root.rounding
        radiusY: root.rounding
        direction: PathArc.Clockwise
    }
    
    PathLine {
        relativeX: -(root.w - root.rounding * 2)
        relativeY: 0
    }
    
    PathArc {
        relativeX: -root.rounding
        relativeY: -root.rounding
        radiusX: root.rounding
        radiusY: root.rounding
        direction: PathArc.Clockwise
    }
    
    PathLine {
        relativeX: 0
        relativeY: -(root.h - root.rounding * 2)
    }

    Behavior on fillColor {
        CAnim {
            // Match the popout closing duration for a perfectly synchronized fade
            duration: Appearance.anim.durations.small
        }
    }
}
