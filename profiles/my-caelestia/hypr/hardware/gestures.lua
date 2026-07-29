hl.on("hyprland.start", function() hl.exec_cmd("hyprctl keyword gesture \"4, horizontal, workspace\"") end)
hl.on("hyprland.start", function() hl.exec_cmd("hyprctl keyword gesture \"3, up, special, special\"") end)
hl.on("hyprland.start", function() hl.exec_cmd("hyprctl keyword gesture \"3, down, dispatcher, exec, caelestia toggle specialws\"") end)
hl.on("hyprland.start", function() hl.exec_cmd("hyprctl keyword gesture \"4, down, dispatcher, exec, systemctl suspend-then-hibernate\"") end)
hl.config({
    gestures = {
        workspace_swipe_distance = 700,
        workspace_swipe_cancel_ratio = "0.15",
        workspace_swipe_min_speed_to_force = 5,
        workspace_swipe_direction_lock = true,
        workspace_swipe_direction_lock_threshold = 10,
        workspace_swipe_create_new = true,
    },
})