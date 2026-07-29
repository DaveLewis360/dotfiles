import os
import sys
import glob
import re

def parse_hyprland_conf(lines, known_vars):
    root_config = {}
    lua_lines = []
    stack = [root_config]
    has_make_combo = False
    
    i = 0
    while i < len(lines):
        line = lines[i].split('#')[0].strip()
        i += 1
        
        if not line:
            continue
            
        if line.endswith('{'):
            block_name = line[:-1].strip()
            new_dict = {}
            if block_name not in stack[-1]:
                stack[-1][block_name] = new_dict
            else:
                new_dict = stack[-1][block_name]
            stack.append(new_dict)
            continue
            
        if line == '}':
            if len(stack) > 1:
                stack.pop()
            continue
            
        if '=' in line:
            parts = line.split('=', 1)
            k = parts[0].strip()
            v = parts[1].strip()
            if v.startswith('\"') and v.endswith('\"'): v = v[1:-1]
            
            if k == "submap":
                lua_lines.append(f'-- Submap {v} omitted as it is unsupported in hl.config')
                continue

            if k == "gesture":
                # Plugins might use 'gesture', which hyprland-lua hl.config doesn't understand natively.
                lua_lines.append(f'hl.on("hyprland.start", function() hl.exec_cmd("hyprctl keyword gesture \\"{v}\\"") end)')
                continue

            def replacer(match):
                full_match = match.group(1)
                for kv in known_vars:
                    if full_match.startswith(kv):
                        remainder = full_match[len(kv):]
                        return f'" .. (_G["{kv}"] or "") .. "{remainder}'
                return f'" .. (_G["{full_match}"] or "") .. "'
            
            v_concat = re.sub(r'\$([a-zA-Z_\-]+)', replacer, v.replace('"', '\\"'))
            v_concat = f'"{v_concat}"'.replace('"" .. ', '').replace(' .. ""', '')

            if k.startswith('$'):
                var_name = k[1:]
                lua_lines.append(f'_G["{var_name}"] = {v_concat}')
                continue
            
            # These can be anywhere in the tree and should be translated to hl.functions
            if k == "bezier":
                vals = [x.strip() for x in v.split(',')]
                name = vals[0]
                x1, y1, x2, y2 = vals[1], vals[2], vals[3], vals[4]
                lua_lines.append(f'hl.curve("{name}", {{ type = "bezier", points = {{ {{ {x1}, {y1} }}, {{ {x2}, {y2} }} }} }})')
                continue
            elif k == "animation":
                vals = [x.strip() for x in v.split(',')]
                name = vals[0]
                enabled = "true" if vals[1] == "1" else "false"
                speed = vals[2] if len(vals) > 2 else "1"
                bezier = vals[3] if len(vals) > 3 else "default"
                style = vals[4] if len(vals) > 4 else ""
                if style:
                    lua_lines.append(f'hl.animation({{ leaf = "{name}", enabled = {enabled}, speed = {speed}, bezier = "{bezier}", style = "{style}" }})')
                else:
                    lua_lines.append(f'hl.animation({{ leaf = "{name}", enabled = {enabled}, speed = {speed}, bezier = "{bezier}" }})')
                continue

            if len(stack) == 1:
                if k == "monitor":
                    vals = [x.strip() for x in v.split(',')]
                    out = vals[0]
                    res = vals[1] if len(vals) > 1 else ""
                    pos = vals[2] if len(vals) > 2 else ""
                    scale = vals[3] if len(vals) > 3 else "1"
                    lua_lines.append(f'hl.monitor({{ output = "{out}", mode = "{res}", position = "{pos}", scale = {scale} }})')
                    continue
                elif k == "workspace":
                    name = v.split(',')[0].strip()
                    gaps = v.split('gapsout:')[1].strip() if 'gapsout:' in v else ""
                    if gaps:
                        gaps = re.sub(r'\$([a-zA-Z_\-]+)', replacer, gaps.replace('"', '\\"'))
                        gaps = f'"{gaps}"'.replace('"" .. ', '').replace(' .. ""', '')
                        lua_lines.append(f'hl.workspace_rule({{ workspace = "{name}", gaps_out = {gaps} }})')
                    continue
                elif k.startswith("exec-once"):
                    lua_lines.append(f'hl.on("hyprland.start", function() hl.exec_cmd({v_concat}) end)')
                    continue
                elif k.startswith("exec"):
                    lua_lines.append(f'hl.exec_cmd({v_concat})')
                    continue
                elif k == "env":
                    vals = [x.strip() for x in v.split(',')]
                    key = vals[0]
                    val = vals[1] if len(vals) > 1 else ""
                    lua_lines.append(f'hl.env("{key}", "{val}")')
                    continue
                elif k.startswith("bind"):
                    if not has_make_combo:
                        lua_lines.insert(0, '''local function make_combo(str)
    local res = str:gsub(",%s*", " + "):gsub("^%s*%+%s*", ""):gsub("%s*%+%s*$", "")
    res = res:gsub("Super", "SUPER"):gsub("Ctrl", "CTRL"):gsub("Alt", "ALT"):gsub("Shift", "SHIFT")
    return res
end''')
                        has_make_combo = True
                    
                    parts = [p.strip() for p in v.split(',')]
                    
                    if len(parts) >= 2 and parts[-1] == "":
                        arg = ""
                        disp = parts[-2]
                        keys = parts[:-2]
                    else:
                        known_no_arg_dispatchers = {"killactive", "togglefloating", "pin", "centerwindow", "movewindow", "resizewindow", "togglegroup", "moveoutofgroup", "cyclenext"}
                        if parts[-1] in known_no_arg_dispatchers:
                            arg = ""
                            disp = parts[-1]
                            keys = parts[:-1]
                        else:
                            arg = parts[-1]
                            disp = parts[-2]
                            keys = parts[:-2]

                        mods = parts[0].replace("+", " + ")

                    keys_str = ", ".join(keys).replace("+", " + ")
                    keys_eval = re.sub(r'\$([a-zA-Z_\-]+)', replacer, keys_str.replace('"', '\\"'))
                    keys_eval = f'"{keys_eval}"'.replace('"" .. ', '').replace(' .. ""', '')
                    
                    combo_eval = f'make_combo({keys_eval})'

                    arg_eval = re.sub(r'\$([a-zA-Z_\-]+)', replacer, arg.replace('"', '\\"'))
                    arg_eval = f'"{arg_eval}"'.replace('"" .. ', '').replace(' .. ""', '')

                    if disp == "exec":
                        disp_call = f'hl.dsp.exec_cmd({arg_eval})'
                    elif disp == "global":
                        disp_call = f'hl.dsp.global({arg_eval})'
                    elif disp == "movefocus":
                        disp_call = f'hl.dsp.focus({{ direction = {arg_eval} }})'
                    elif disp == "movewindow":
                        if not arg:
                            disp_call = f'hl.dsp.window.drag()'
                        else:
                            disp_call = f'hl.dsp.window.move({{ direction = {arg_eval} }})'
                    elif disp == "resizewindow":
                        disp_call = f'hl.dsp.window.resize()'
                    elif disp == "killactive":
                        disp_call = f'hl.dsp.window.close()'
                    elif disp == "togglefloating":
                        disp_call = f'hl.dsp.window.float({{ action = "toggle" }})'
                    elif disp == "fullscreen":
                        disp_call = f'hl.dsp.window.fullscreen({{ mode = ({arg_eval} == "0" and "fullscreen" or "maximized"), action = "toggle" }})'
                    elif disp == "workspace":
                        disp_call = f'hl.dsp.focus({{ workspace = {arg_eval} }})'
                    elif disp == "movetoworkspace":
                        disp_call = f'hl.dsp.window.move({{ workspace = {arg_eval} }})'
                    elif disp == "cyclenext":
                        disp_call = f'hl.dsp.window.cycle_next()'
                    elif disp == "changegroupactive":
                        if arg_eval in ('"f"', "'f'"):
                            disp_call = f'hl.dsp.group.next()'
                        elif arg_eval in ('"b"', "'b'"):
                            disp_call = f'hl.dsp.group.prev()'
                        else:
                            disp_call = f'hl.dsp.group.next()'
                    elif disp == "togglegroup":
                        disp_call = f'hl.dsp.group.toggle()'
                    elif disp == "moveoutofgroup":
                        disp_call = f'hl.dsp.window.move({{ out_of_group = true }})'
                    elif disp == "lockactivegroup":
                        disp_call = f'hl.dsp.group.lock_active()'
                    elif disp == "centerwindow":
                        disp_call = f'hl.dsp.window.center()'
                    elif disp == "pin":
                        disp_call = f'hl.dsp.window.pin()'
                    elif disp == "resizeactive":
                        # Simplistic fallback for resizeactive exact
                        if "exact" in arg_eval:
                            disp_call = f'hl.dsp.window.resize({{ x = 800, y = 600, relative = false }})'
                        else:
                            disp_call = f'hl.dsp.window.resize({{ x = 0, y = 0, relative = true }})'
                    elif disp == "fullscreenstate":
                        fs_args = arg.replace(',', ' ').split()
                        internal_val = fs_args[0] if len(fs_args) > 0 else "0"
                        client_val = fs_args[1] if len(fs_args) > 1 else "2"
                        disp_call = f'hl.dsp.window.fullscreen_state({{ internal = {internal_val}, client = {client_val}, action = "toggle" }})'
                    else:
                        disp_call = f'hl.dsp.exec_cmd("echo unknown dispatch " .. "{disp}")'

                    options = []
                    if "l" in k: options.append('locked = true')
                    if "e" in k: options.append('repeating = true')
                    if "m" in k: options.append('mouse = true')
                    if "r" in k: options.append('release = true')
                    
                    if len(options) > 0:
                        opt_str = ', {' + ', '.join(options) + '}'
                    else:
                        opt_str = ''

                    lua_lines.append(f'hl.bind(make_combo({keys_eval}), {disp_call}{opt_str})')
                    continue
                elif k.startswith("windowrule") or k == "layerrule":
                    hl_func = "window_rule" if k.startswith("windowrule") else "layer_rule"
                    parts = v.split(", match:")
                    rule_part = parts[0].strip()
                    if " " in rule_part:
                        r_key, r_val = rule_part.split(" ", 1)
                        if r_val in ("true", "false") or r_val.isdigit():
                            pass
                        else:
                            r_val = re.sub(r'\$([a-zA-Z_\-]+)', replacer, r_val.replace('"', '\\"'))
                            r_val = f'"{r_val}"'.replace('"" .. ', '').replace(' .. ""', '')
                    else:
                        r_key, r_val = rule_part, "true"
                        
                    matches = []
                    for m in parts[1:]:
                        m = m.strip()
                        if " " in m:
                            m_key, m_val = m.split(" ", 1)
                            m_val = m_val.replace("\\", "\\\\").replace('"', '\\"')
                            matches.append(f'{m_key} = "{m_val}"')
                        else:
                            matches.append(f'{m} = true')
                            
                    match_str = ", ".join(matches)
                    if match_str:
                        lua_lines.append(f'hl.{hl_func}({{ match = {{ {match_str} }}, {r_key} = {r_val} }})')
                    else:
                        lua_lines.append(f'hl.{hl_func}({{ {r_key} = {r_val} }})')
                    continue
                elif k == "source":
                    if "hypr/" in v:
                        rel_path = v.split("hypr/")[-1].replace(".conf", "")
                        module_name = rel_path.replace("/", ".")
                        lua_lines.append(f'package.loaded["{module_name}"] = nil')
                        lua_lines.append(f'local _mod = require("{module_name}")')
                        lua_lines.append(f'if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end')
                    else:
                        import os
                        module_name = os.path.basename(v).replace(".conf", "")
                        lua_lines.append(f'package.loaded["{module_name}"] = nil')
                        lua_lines.append(f'local _mod = require("{module_name}")')
                        lua_lines.append(f'if type(_mod) == "table" then for k, v in pairs(_mod) do _G[k] = v end end')
                    continue
            
            if v in ("true", "false", "1.0", "0.0"):
                stack[-1][k] = v
            elif v == "1" and k in ("enabled", "xray", "special", "popups", "input_methods", "natural_scroll", "disable_while_typing"):
                stack[-1][k] = "true"
            elif v == "0" and k in ("enabled", "xray", "special", "popups", "input_methods", "natural_scroll", "disable_while_typing"):
                stack[-1][k] = "false"
            elif v.isdigit():
                stack[-1][k] = v
            else:
                stack[-1][k] = v_concat
                
    def dict_to_lua(d, indent=1):
        lines = []
        for k, v in d.items():
            pad = "    " * indent
            if isinstance(v, dict):
                if not k.replace("_", "").isalnum() or k[0].isdigit():
                    lines.append(f'{pad}["{k}"] = {{')
                else:
                    lines.append(f"{pad}{k} = {{")
                lines.extend(dict_to_lua(v, indent + 1))
                lines.append(f"{pad}}},")
            elif isinstance(v, list):
                lines.append(f"{pad}{k} = {{")
                for item in v:
                    lines.append(f"{pad}    {item},")
                lines.append(f"{pad}}},")
            else:
                if not k.replace("_", "").isalnum() or k[0].isdigit():
                    lines.append(f'{pad}["{k}"] = {v},')
                else:
                    lines.append(f'{pad}{k} = {v},')
        return lines

    if root_config:
        lua_lines.append("hl.config({")
        lua_lines.extend(dict_to_lua(root_config, 1))
        lua_lines.append("})")
        
    return "\n".join(lua_lines)

if len(sys.argv) < 2:
    print("Usage: translate_hypr_lua.py <hypr_dir>")
    sys.exit(1)

hypr_dir = sys.argv[1]

known_vars = set()
conf_files = glob.glob(f"{hypr_dir}/**/*.conf", recursive=True)
for conf_file in conf_files:
    with open(conf_file, "r") as f:
        for line in f:
            line = line.split('#')[0].strip()
            if line.startswith('$') and '=' in line:
                var_name = line.split('=', 1)[0].strip()[1:]
                known_vars.add(var_name)

known_vars = sorted(list(known_vars), key=len, reverse=True)

for conf_file in conf_files:
    lua_file = conf_file[:-5] + ".lua"
    with open(conf_file, "r") as f:
        lines = f.readlines()
    lua_content = parse_hyprland_conf(lines, known_vars)
    with open(lua_file, "w") as f:
        f.write(lua_content)
    print(f"Generated {lua_file}")
