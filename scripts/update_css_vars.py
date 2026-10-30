#!/usr/bin/env python3
import json
import os
import re
import subprocess
from pathlib import Path

# Paths
user_home = Path.home()
state_dir = user_home / ".local/state/caelestia"
scheme_path = state_dir / "scheme.json"
sequences_path = state_dir / "sequences.txt"
shell_config_path = user_home / ".config/caelestia/shell.json"

# App config paths
ghostty_theme_path = user_home / ".config/ghostty/current_theme.conf"
vesktop_theme_path = user_home / ".config/vesktop/themes/ZenCaelestia.theme.css"
vencord_theme_path = user_home / ".config/Vencord/themes/ZenCaelestia.theme.css"
vscode_settings_path = user_home / ".config/Code/User/settings.json"

ANSI_MAPPING = {
    0: "surfaceContainerLowest", 1: "red", 2: "green", 3: "yellow",
    4: "blue", 5: "mauve", 6: "teal", 7: "onSurface",
    8: "surfaceVariant", 9: "red", 10: "green", 11: "yellow",
    12: "blue", 13: "mauve", 14: "teal", 15: "onSurface",
    16: "primary", 17: "secondary", 18: "tertiary"
}

GHOSTTY_MAPPING = {
    "foreground": "onBackground",
    "cursor-color": "primary",
    "selection-background": "primaryContainer",
    "selection-foreground": "onPrimaryContainer"
}

# --- VS CODE (dynamic Caelestia theme) ---
# Written into settings.json as workbench.colorCustomizations /
# editor.tokenColorCustomizations / editor.semanticTokenColorCustomizations.
# VS Code applies these LIVE (no reload, no restart) and they override any
# active color theme. Values are scheme keys or (schemeKey, alphaHex) tuples.
VSCODE_COLORS = {
    # editor core
    "editor.background": "surface",
    "editor.foreground": "onSurface",
    "editorCursor.foreground": "primary",
    "editor.selectionBackground": ("primary", "4D"),
    "editor.inactiveSelectionBackground": ("primary", "33"),
    "editor.lineHighlightBackground": ("onSurface", "14"),
    "editorLineNumber.foreground": "outline",
    "editorLineNumber.activeForeground": "primary",
    "editorIndentGuide.background1": ("outline", "33"),
    "editorIndentGuide.activeBackground1": ("outline", "66"),
    "editorWhitespace.foreground": ("outline", "4D"),
    "editorWidget.background": "surfaceContainer",
    "editorWidget.border": "outlineVariant",
    "editorHoverWidget.background": "surfaceContainerHigh",
    "editorHoverWidget.border": "outlineVariant",
    "editorGutter.addedBackground": "term2",
    "editorGutter.modifiedBackground": "term3",
    "editorGutter.deletedBackground": "term1",
    # sideBar
    "sideBar.background": "surfaceContainerLow",
    "sideBar.foreground": "onSurface",
    "sideBar.border": "outlineVariant",
    "sideBarSectionHeader.background": "surfaceContainer",
    # activityBar
    "activityBar.background": "surfaceContainerLow",
    "activityBar.foreground": "primary",
    "activityBar.inactiveForeground": ("onSurface", "66"),
    "activityBar.border": "outlineVariant",
    "activityBar.activeBorder": "primary",
    "activityBarBadge.background": "primary",
    "activityBarBadge.foreground": "onPrimary",
    # statusBar
    "statusBar.background": "surfaceContainer",
    "statusBar.foreground": "onSurface",
    "statusBar.border": "outlineVariant",
    "statusBar.debuggingBackground": "errorContainer",
    # titleBar
    "titleBar.activeBackground": "surfaceContainerLow",
    "titleBar.activeForeground": "onSurface",
    "titleBar.border": "outlineVariant",
    # titleBar (inactive window: VS Code switches to these on focus loss)
    "titleBar.inactiveBackground": "surfaceContainer",
    "titleBar.inactiveForeground": "onSurfaceVariant",
    # tabs
    "tab.activeBackground": "surface",
    "tab.activeForeground": "onSurface",
    "tab.inactiveBackground": "surfaceContainerLow",
    "tab.inactiveForeground": ("onSurface", "99"),
    "tab.border": "outlineVariant",
    "tab.activeBorderTop": "primary",
    "tab.hoverBackground": ("onSurface", "14"),
    # tabs (unfocused window: VS Code switches to these on focus loss)
    "tab.unfocusedActiveBackground": "surface",
    "tab.unfocusedActiveForeground": "onSurface",
    "tab.unfocusedInactiveBackground": "surfaceContainerLow",
    "tab.unfocusedInactiveForeground": ("onSurface", "99"),
    "tab.unfocusedHoverBackground": ("onSurface", "14"),
    "tab.unfocusedActiveBorderTop": "primary",
    # editorGroup
    "editorGroup.border": "outlineVariant",
    "editorGroup.emptyBackground": "surface",
    "editorGroupHeader.tabsBackground": "surfaceContainerLow",
    # list
    "list.activeSelectionBackground": ("primary", "4D"),
    "list.activeSelectionForeground": "onSurface",
    "list.hoverBackground": ("onSurface", "14"),
    "list.inactiveSelectionBackground": ("primary", "26"),
    "list.highlightForeground": "primary",
    # input
    "input.background": "surfaceContainerHigh",
    "input.foreground": "onSurface",
    "input.border": "outlineVariant",
    "input.placeholderForeground": ("onSurface", "80"),
    # button
    "button.background": "primary",
    "button.foreground": "onPrimary",
    "button.hoverBackground": "primaryDim",
    # focus + selection
    "focusBorder": "primary",
    "selection.background": ("primary", "4D"),
    # scrollbar
    "scrollbarSlider.background": ("onSurface", "29"),
    "scrollbarSlider.hoverBackground": ("onSurface", "4D"),
    "scrollbarSlider.activeBackground": ("onSurface", "66"),
    # panel
    "panel.background": "surfaceContainerLow",
    "panel.border": "outlineVariant",
    # breadcrumb
    "breadcrumb.foreground": ("onSurface", "99"),
    "breadcrumb.focusForeground": "primary",
    # notifications
    "notifications.background": "surfaceContainerHigh",
    "notifications.border": "outlineVariant",
    # minimap
    "minimap.background": ("surfaceContainerLow", "B3"),
    "minimap.selectionHighlight": ("primary", "4D"),
    "minimap.errorHighlight": "term1",
    "minimap.findMatchHighlight": "term3",
    # overviewRuler
    "editorOverviewRuler.border": "outlineVariant",
    # gitDecoration
    "gitDecoration.addedResourceForeground": "term2",
    "gitDecoration.modifiedResourceForeground": "term3",
    "gitDecoration.deletedResourceForeground": "term1",
    "gitDecoration.untrackedResourceForeground": "term2",
    "gitDecoration.ignoredResourceForeground": ("onSurface", "66"),
    "gitDecoration.conflictingResourceForeground": "term5",
    # diffEditor
    "diffEditor.insertedTextBackground": ("term2", "33"),
    "diffEditor.removedTextBackground": ("term1", "33"),
    # error/warning/info
    "editorError.foreground": "error",
    "editorWarning.foreground": "term3",
    "editorInfo.foreground": "term4",
    "errorForeground": "error",
    # progress
    "progressBar.background": "primary",
    # terminal core + straight ANSI passthrough (NOT M3 accents:
    # terminal apps expect ANSI semantics)
    "terminal.background": "surfaceContainerLow",
    "terminal.foreground": "onSurface",
    "terminalCursor.foreground": "primary",
    "terminal.ansiBlack": "term0",
    "terminal.ansiRed": "term1",
    "terminal.ansiGreen": "term2",
    "terminal.ansiYellow": "term3",
    "terminal.ansiBlue": "term4",
    "terminal.ansiMagenta": "term5",
    "terminal.ansiCyan": "term6",
    "terminal.ansiWhite": "term7",
    "terminal.ansiBrightBlack": "term8",
    "terminal.ansiBrightRed": "term9",
    "terminal.ansiBrightGreen": "term10",
    "terminal.ansiBrightYellow": "term11",
    "terminal.ansiBrightBlue": "term12",
    "terminal.ansiBrightMagenta": "term13",
    "terminal.ansiBrightCyan": "term14",
    "terminal.ansiBrightWhite": "term15",
}

# fg/bg are (schemeKey, alphaOrNone) tuples. Variables deliberately use
# onSurface (calm code); hues come from the bright ANSI ramp.
VSCODE_TEXTMATE_RULES = [
    {"scope": "comment, punctuation.definition.comment", "fg": ("term8", None), "fontStyle": "italic"},
    {"scope": "keyword, storage, keyword.operator.new", "fg": ("term5", None)},
    {"scope": "string, punctuation.definition.string", "fg": ("term2", None)},
    {"scope": "constant.numeric, constant.language.boolean", "fg": ("term3", None)},
    {"scope": "entity.name.function, support.function", "fg": ("term4", None)},
    {"scope": "variable, variable.other, entity.name.variable", "fg": ("onSurface", None)},
    {"scope": "entity.name.type, entity.name.class, support.class, support.type", "fg": ("term6", None)},
    {"scope": "constant, constant.language, variable.other.constant", "fg": ("term3", None)},
    {"scope": "keyword.operator", "fg": ("term1", None)},
    {"scope": "punctuation", "fg": ("onSurfaceVariant", None)},
    {"scope": "invalid, invalid.illegal", "fg": ("onPrimary", None), "bg": ("error", None)},
    {"scope": "markup.heading, markup.list, markup.raw", "fg": ("primary", None)},
]

VSCODE_SEMANTIC_RULES = {
    "parameter": ("term3", None),
    "property.declaration": ("term6", None),
    "function.declaration": ("term4", None),
    "variable.readonly": ("term5", None),
    "type": ("term6", None),
}


def _vscode_color(colors, spec):
    if isinstance(spec, tuple):
        key, alpha = spec
        base = get_color(colors, key).lstrip("#")
        return f"#{base}{alpha}" if alpha else f"#{base}"
    return get_color(colors, spec)


def _scan_json_string(text, i):
    # text[i] == '"'; return index AFTER closing quote
    i += 1
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            return i + 1
        i += 1
    return n


def _skip_json_ws_comments(text, i):
    n = len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i + 2)
            i = n if j == -1 else j + 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
        else:
            break
    return i


def _match_json_brace(text, i):
    # text[i] == '{'; return index AFTER matching '}'
    depth = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i = _scan_json_string(text, i)
            continue
        if c == "/" and i + 1 < n and text[i + 1] in "/*":
            i = _skip_json_ws_comments(text, i)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced braces in settings.json")


def _match_json_bracket(text, i):
    # text[i] == '['; return index AFTER matching ']'
    depth = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i = _scan_json_string(text, i)
            continue
        if c == "/" and i + 1 < n and text[i + 1] in "/*":
            i = _skip_json_ws_comments(text, i)
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced brackets in settings.json")


def _json_value_end(text, i):
    # text[i] starts a JSON value; return index AFTER it
    i = _skip_json_ws_comments(text, i)
    c = text[i]
    if c == '"':
        return _scan_json_string(text, i)
    if c == "{":
        return _match_json_brace(text, i)
    if c == "[":
        return _match_json_bracket(text, i)
    n = len(text)
    while i < n and text[i] not in ",}]":
        if text[i] == '"':
            i = _scan_json_string(text, i)
            continue
        i += 1
    return i


def _find_top_level_value(text, key):
    # Find the value span of top-level "key". Returns (start, end) or None.
    # String/comment aware: only matches at brace depth 1.
    target = json.dumps(key)
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = _scan_json_string(text, i)
            if depth == 1 and text[i:j] == target:
                k = _skip_json_ws_comments(text, j)
                if k < n and text[k] == ":":
                    v = _skip_json_ws_comments(text, k + 1)
                    return (v, _json_value_end(text, v))
            i = j
            continue
        if c == "/" and i + 1 < n and text[i + 1] in "/*":
            i = _skip_json_ws_comments(text, i)
            continue
        if c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
        i += 1
    return None


def _strip_jsonc(text):
    # Remove // and /* */ comments + trailing commas for validation only.
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = _scan_json_string(text, i)
            out.append(text[i:j])
            i = j
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i + 2)
            i = n if j == -1 else j
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        out.append(c)
        i += 1
    return re.sub(r",\s*([}\]])", r"\1", "".join(out))


def _set_top_level_block(text, key, obj):
    # Replace (or insert) a top-level "key": {...} block, preserving every
    # other byte of the file (user settings, comments). Returns new text.
    rendered = json.dumps(obj, indent=2).split("\n")
    rendered = rendered[0] + "".join("\n  " + line for line in rendered[1:])
    span = _find_top_level_value(text, key)
    if span:
        start, end = span
        return text[:start] + rendered + text[end:]
    stripped = text.strip()
    if stripped in ("", "{}"):
        return '{\n  "%s": %s\n}\n' % (key, rendered)
    # Insert before the final "}". Watch out for: trailing comma before it
    # (would make ",,"), (effectively) empty object (no comma needed), and a
    # trailing // comment (the comma must go on its own line, not inside it).
    # Comment-stripped code decides; the original head text is kept as-is.
    idx = text.rfind("}")
    head = text[:idx].rstrip()
    code = _strip_jsonc(head).rstrip()
    if code.endswith("{") or code == "":
        prefix = "\n  "
    elif code.endswith(","):
        prefix = "\n  "
    elif head.split("\n")[-1].strip().startswith("//"):
        prefix = "\n,\n  "
    else:
        prefix = ",\n  "
    return head + prefix + '"%s": %s\n' % (key, rendered) + text[idx:]


def update_vscode(dynamic_colors):
    color_custom = {k: _vscode_color(dynamic_colors, v) for k, v in VSCODE_COLORS.items()}
    textmate_rules = []
    for rule in VSCODE_TEXTMATE_RULES:
        settings = {"foreground": _vscode_color(dynamic_colors, rule["fg"])}
        if rule.get("bg"):
            settings["background"] = _vscode_color(dynamic_colors, rule["bg"])
        if rule.get("fontStyle"):
            settings["fontStyle"] = rule["fontStyle"]
        textmate_rules.append({"scope": rule["scope"], "settings": settings})
    semantic_rules = {k: _vscode_color(dynamic_colors, v) for k, v in VSCODE_SEMANTIC_RULES.items()}

    vscode_settings_path.parent.mkdir(parents=True, exist_ok=True)
    if vscode_settings_path.exists():
        text = vscode_settings_path.read_text()
        vscode_settings_path.with_suffix(".json.bak").write_text(text)
    else:
        text = "{}\n"

    text = _set_top_level_block(text, "workbench.colorCustomizations", color_custom)
    text = _set_top_level_block(text, "editor.tokenColorCustomizations", {"textMateRules": textmate_rules})
    text = _set_top_level_block(text, "editor.semanticTokenColorCustomizations", {"rules": semantic_rules})

    # Validate before writing: must stay parseable (JSONC-tolerant check)
    json.loads(_strip_jsonc(text))

    tmp = vscode_settings_path.with_suffix(".json.tmp")
    tmp.write_text(text)
    os.replace(tmp, vscode_settings_path)
    print(f"VS Code: {len(color_custom)} colors + {len(textmate_rules)} textMate rules + {len(semantic_rules)} semantic rules")


def hex_to_osc(code, hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"\033]{code};rgb:{r:02x}/{g:02x}/{b:02x}\007"


def get_color(colors, key):
    val = colors.get(key)
    if val:
        return f"#{val}" if not val.startswith("#") else val
    camel = re.sub(r'_([a-z])', lambda m: m.group(1).upper(), key)
    val = colors.get(camel)
    if val:
        return f"#{val}" if not val.startswith("#") else val
    return "#ffffff"


def update_css_var(content, key, val):
    if not val.startswith("#"):
        val = f"#{val}"
    escaped = re.escape(key)
    pattern = re.compile(f'--{escaped}: #[0-9a-fA-F]+;', re.IGNORECASE)
    return pattern.sub(f'--{key}: {val};', content)


def main():
    if not scheme_path.exists():
        print(f"Error: {scheme_path} not found")
        return

    with open(scheme_path, 'r') as f:
        scheme_data = json.load(f)
    dynamic_colors = scheme_data.get("colours", {})

    # Load shell config for transparency
    app_opacity = 0.7
    if shell_config_path.exists():
        try:
            with open(shell_config_path, 'r') as f:
                shell_config = json.load(f)
            app_opacity = shell_config.get("appearance", {}).get("transparency", {}).get("base", 0.7)
        except:
            pass

    # --- UPDATE GHOSTTY ---
    # Always (re)write the theme: create it when missing so the
    # `config-file` include in the universal ghostty config never dangles
    # (e.g. under git/end4 profiles where the file doesn't exist yet).
    ghostty_theme_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["background = #000000\n"]

    for ghost_key, m3_key in GHOSTTY_MAPPING.items():
        lines.append(f"{ghost_key} = {get_color(dynamic_colors, m3_key)}\n")

    for i, m3_key in ANSI_MAPPING.items():
        lines.append(f"palette = {i}={get_color(dynamic_colors, m3_key)}\n")

    ghostty_theme_path.write_text("".join(lines))

    # --- UPDATE DISCORD CSS ---
    discord_themes = [vesktop_theme_path, vencord_theme_path]
    for theme_path in discord_themes:
        if theme_path.exists():
            content = theme_path.read_text()

            content = re.sub(r'--app-opacity: [0-9.]+;', f'--app-opacity: {app_opacity};', content)

            for m3_key, val in dynamic_colors.items():
                content = update_css_var(content, m3_key, val)

            theme_path.write_text(content)

    # --- UPDATE VS CODE (instant: settings.json applies live, no reload) ---
    try:
        update_vscode(dynamic_colors)
    except Exception as e:
        print(f"VS Code: skipped ({e})")

    # --- LIVE REFRESH TERMINALS ---
    sequences = hex_to_osc(10, get_color(dynamic_colors, "onBackground"))
    sequences += hex_to_osc(11, "000000")
    sequences += hex_to_osc(12, get_color(dynamic_colors, "primary"))
    for i in range(1, 16):
        sequences += hex_to_osc(f"4;{i}", get_color(dynamic_colors, ANSI_MAPPING.get(i, "")))
    for i in range(16, 19):
        sequences += hex_to_osc(f"4;{i}", get_color(dynamic_colors, ANSI_MAPPING.get(i, "")))

    try:
        sequences_path.write_text(sequences)
    except:
        pass

    pts_path = Path("/dev/pts")
    if pts_path.exists():
        for pt in pts_path.iterdir():
            if pt.name.isdigit():
                try:
                    with open(pt, 'w') as f:
                        f.write(sequences)
                except:
                    pass

    # --- RELOAD GTK THEME (long-lived GTK apps + the xdg portal backend
    # cache gtk.css at startup; rewriting the value to itself emits no change
    # signal, so toggle away and back to force a re-read) ---
    try:
        cur = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"], capture_output=True, text=True).stdout.strip().strip("'")
        tmp = "Adwaita-dark" if cur == "Adwaita" else "Adwaita"
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", tmp], stderr=subprocess.DEVNULL)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", cur or "adw-gtk3-dark"], stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # --- RESTART PORTAL GTK BACKEND (file choosers keep the CSS loaded from
    # backend start; the toggle above does not reach them) ---
    try:
        subprocess.run(["systemctl", "--user", "restart", "xdg-desktop-portal-gtk.service"], stderr=subprocess.DEVNULL, timeout=30)
    except Exception:
        pass

    # --- RELOAD HYPRLAND (skip on first run to avoid disrupting startup) ---
    if os.environ.get("CAELESTIA_WATCHER") == "1":
        subprocess.run(["hyprctl", "reload"], stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
