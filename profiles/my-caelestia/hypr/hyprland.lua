package.loaded["hardware.monitors"] = nil
local _mod = require("hardware.monitors")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["hardware.host-specific"] = nil
local _mod = require("hardware.host-specific")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["hardware.input"] = nil
local _mod = require("hardware.input")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
hl.on("hyprland.start", function() hl.exec_cmd("cp -L --no-preserve=mode --update=none ~/.config/hypr/scheme/default.conf ~/.config/hypr/scheme/current.conf") end)
package.loaded["scheme.current"] = nil
local _mod = require("scheme.current")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["core.definitions"] = nil
local _mod = require("core.definitions")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["core.env"] = nil
local _mod = require("core.env")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["core.execs"] = nil
local _mod = require("core.execs")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["core.rules"] = nil
local _mod = require("core.rules")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["core.binds"] = nil
local _mod = require("core.binds")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["appearance.theme"] = nil
local _mod = require("appearance.theme")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["appearance.animations"] = nil
local _mod = require("appearance.animations")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["appearance.window_mods"] = nil
local _mod = require("appearance.window_mods")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end
package.loaded["hardware.gestures"] = nil
local _mod = require("hardware.gestures")
if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end