import qs.services
import qs.config
import qs.modules.osd as Osd
import qs.modules.notifications as Notifications
import qs.modules.session as Session
import qs.modules.launcher as Launcher
import qs.modules.dashboard as Dashboard
import qs.modules.bar.popouts as BarPopouts
import qs.modules.utilities as Utilities
import qs.modules.sidebar as Sidebar
import QtQuick
import QtQuick.Shapes

Shape {
    id: root

    required property Panels panels
    required property Item bar

    anchors.fill: parent
    anchors.margins: Config.border.thickness
    // topMargin handles global offset, but we handle Dashboard manually
    anchors.topMargin: bar.implicitHeight
    preferredRendererType: Shape.CurveRenderer

    Osd.Background {
        wrapper: root.panels.osd

        startX: root.width - root.panels.session.width - root.panels.sidebar.width + 4
        startY: (root.height - wrapper.height) / 2 - rounding
    }

    Notifications.Background {
        wrapper: root.panels.notifications
        sidebar: sidebar

        startX: root.width
        startY: 0
    }

    Session.Background {
        wrapper: root.panels.session

        startX: root.width - root.panels.sidebar.width
        startY: (root.height - wrapper.height) / 2 - rounding
    }

    Launcher.Background {
        wrapper: root.panels.launcher

        startX: (root.width - wrapper.width) / 2 - rounding
        startY: root.height
    }

    // THE MORPHING DASHBOARD BACKGROUND
    Dashboard.Background {
        id: dashBg
        wrapper: root.panels.dashboard
        
        // Find MiniDash reference through the bar structure
        // bar is BarWrapper -> content is Loader -> item is Bar
        readonly property Item barItem: root.bar.contentItem?.item ?? null
        
        readonly property bool isExpanded: wrapper.implicitHeight > 0
        
        // Dynamic target values for morphing
        // Use nonAnim properties to avoid double animation lag
        w: isExpanded ? wrapper.nonAnimWidth : (barItem ? barItem.pillWidth : 400)
        h: isExpanded ? wrapper.nonAnimHeight : bar.implicitHeight
        
        // Start position (Horizontal center)
        startX: (root.width - w) / 2
        // Always start from the screen top (-bar.implicitHeight relative to the topMargin)
        // to avoid hanging artifacts below the bar.
        startY: -bar.implicitHeight
        
        isTopHanging: true
    }

    BarPopouts.Background {
        wrapper: root.panels.popouts

        startX: wrapper.x
        startY: wrapper.y + rounding
    }

    Utilities.Background {
        wrapper: root.panels.utilities
        sidebar: sidebar

        startX: root.width + 6
        startY: root.height + 4
    }

    Sidebar.Background {
        id: sidebar

        wrapper: root.panels.sidebar
        panels: root.panels

        startX: root.width
        startY: root.panels.notifications.height
    }
}