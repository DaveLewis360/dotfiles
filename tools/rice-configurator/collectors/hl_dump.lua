-- hl_dump.lua — a Hyprland Lua config hl.* hívásainak felvétele, futtatás nélkül.
--
-- Használat: lua hl_dump.lua <hypr könyvtár>
-- Kimenet (stdout): soronként egy JSON objektum:
--   {"fn": "config", "path": "general.border_size", "value": 0, "src": "...", "line": 12, "event": null}
--   {"fn": "bind", "args": [...], "src": ..., "line": ..., "event": null}
-- A hl.dsp.* hívások leíróként jönnek vissza: {"dsp": "window.close", "args": [...]}.
-- Semmit nem hajt végre (hl.exec_cmd is csak felvétel), a fájlokat csak olvassa.

local dir = arg[1]
package.path = dir .. "/?.lua;" .. package.path

local function esc(s)
    return (s:gsub('[%c"\\]', function(c)
        local m = { ['"'] = '\\"', ['\\'] = '\\\\', ['\n'] = '\\n', ['\t'] = '\\t', ['\r'] = '\\r' }
        return m[c] or string.format("\\u%04x", c:byte())
    end))
end

local function is_array(t)
    local n = 0
    for k in pairs(t) do
        if type(k) ~= "number" then return false end
        n = n + 1
    end
    return n == #t
end

local function enc(v, seen)
    local t = type(v)
    if t == "nil" then return "null" end
    if t == "boolean" then return tostring(v) end
    if t == "number" then
        if v ~= v or v == math.huge or v == -math.huge then return "null" end
        if math.type and math.type(v) == "integer" then return tostring(v) end
        return string.format("%.10g", v)
    end
    if t == "string" then return '"' .. esc(v) .. '"' end
    if t == "function" then return '"<function>"' end
    if t == "table" then
        seen = seen or {}
        if seen[v] then return '"<cycle>"' end
        seen[v] = true
        local parts = {}
        if rawget(v, "__dsp") then
            local a = {}
            for i, x in ipairs(v.__args) do a[i] = enc(x, seen) end
            return '{"dsp":"' .. esc(v.__dsp) .. '","args":[' .. table.concat(a, ",") .. ']}'
        end
        if next(v) ~= nil and is_array(v) then
            for i, x in ipairs(v) do parts[i] = enc(x, seen) end
            return "[" .. table.concat(parts, ",") .. "]"
        end
        local keys = {}
        for k in pairs(v) do keys[#keys + 1] = k end
        table.sort(keys, function(a, b) return tostring(a) < tostring(b) end)
        for _, k in ipairs(keys) do
            parts[#parts + 1] = '"' .. esc(tostring(k)) .. '":' .. enc(v[k], seen)
        end
        return "{" .. table.concat(parts, ",") .. "}"
    end
    return '"<' .. t .. '>"'
end

local event = nil

-- A hívó helye: az első olyan veremszint, ami már nem ebben a fájlban van.
-- (A short_src csonkol, ezért a teljes `source`-t használjuk.)
local self_src = debug.getinfo(1, "S").source
local function where()
    for level = 2, 20 do
        local info = debug.getinfo(level, "Sl")
        if not info then break end
        if info.source ~= self_src and info.what ~= "C" then
            return (info.source:gsub("^@", "")), info.currentline or 0
        end
    end
    return "?", 0
end

local function emit(fields)
    local src, line = where()
    fields.src, fields.line, fields.event = src, line, event
    local parts = {}
    for _, k in ipairs({ "fn", "path", "value", "args", "src", "line", "event" }) do
        if fields[k] ~= nil then parts[#parts + 1] = '"' .. k .. '":' .. enc(fields[k]) end
    end
    io.write("{" .. table.concat(parts, ",") .. "}\n")
end

local function flatten(prefix, t, src, line)
    for k, v in pairs(t) do
        local p = prefix == "" and tostring(k) or (prefix .. "." .. tostring(k))
        if type(v) == "table" and not rawget(v, "__dsp") and not is_array(v) and next(v) ~= nil then
            flatten(p, v, src, line)
        else
            local parts = { '"fn":"config"', '"path":' .. enc(p), '"value":' .. enc(v),
                '"src":' .. enc(src), '"line":' .. enc(line), '"event":' .. enc(event) }
            io.write("{" .. table.concat(parts, ",") .. "}\n")
        end
    end
end

local function dsp_proxy(path)
    return setmetatable({}, {
        __index = function(_, k) return dsp_proxy(path == "" and k or (path .. "." .. k)) end,
        __call = function(_, ...) return { __dsp = path, __args = { ... } } end,
    })
end

hl = setmetatable({
    dsp = dsp_proxy(""),
    config = function(t)
        local src, line = where()
        flatten("", t, src, line)
    end,
    on = function(ev, fn)
        emit({ fn = "on", args = { ev } })
        local saved = event
        event = tostring(ev)
        local ok, err = pcall(fn)
        if not ok then emit({ fn = "error", args = { tostring(err) } }) end
        event = saved
    end,
}, {
    __index = function(_, k)
        return function(...) emit({ fn = k, args = { ... } }) end
    end,
})

local before = {}
for k in pairs(_G) do before[k] = true end

local ok, err = pcall(dofile, dir .. "/hyprland.lua")
if not ok then
    io.write('{"fn":"error","args":[' .. enc(tostring(err)) .. ']}\n')
end

-- A config által definiált globális változók (core/definitions.lua: _G["terminal"] = ...).
local names = {}
for k, v in pairs(_G) do
    local t = type(v)
    if not before[k] and type(k) == "string" and (t == "string" or t == "number" or t == "boolean") then
        names[#names + 1] = k
    end
end
table.sort(names)
for _, k in ipairs(names) do
    io.write('{"fn":"var","path":' .. enc(k) .. ',"value":' .. enc(_G[k]) .. '}\n')
end
