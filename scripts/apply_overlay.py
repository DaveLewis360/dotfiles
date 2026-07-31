#!/usr/bin/env python3
"""dotswitch overlay applier.

A közös (rice-független) beállításokat (~/dotfiles/shared/common.json) ráteszi a profil
user-override fájljára egy "managed block" formában, a profil natív formátumában:
  - lua      hl.config({ input = { ... } }) / hl.bind(...) / hl.config({ windowrule = ... })
  - conf     igazi Hyprland conf:               windowrule = RULE, class:^(...)$
  - conf-hl  a translate_hypr_lua.py bemenete:  windowrule = RULE, match:class ^(...)$

A conf-hl azért külön, mert ezt a fájlt nem a Hyprland olvassa, hanem a
translator, ami saját "match:" szintaxist vár. Így a közös overlay a .conf-ba
kerül (egyetlen igazságforrás), és a .lua-t abból generálja a translator.

Kezelt szekciók a common.json-ban:
  input        — beállítás-blokk (skalárok + egy szint mély alblokkok, pl. touchpad)
  binds        — közös keybindek, minden profilban ugyanazok
  windowrules  — közös ablakszabályok (megjelenés), minden profilban ugyanazok

Idempotens: minden futáskor eltávolítja a korábbi managed blokkot, majd újat ír.
A managed blokkon kívüli (felhasználói) tartalmat érintetlenül hagyja.

Használat:
  apply_overlay.py <common.json> <target> <lua|conf|conf-hl>
  apply_overlay.py --strip <target> <lua|conf|conf-hl>

A --strip csak ELTÁVOLÍTJA a managed blokkot, újat nem ír. Erre azért van
szükség, mert több profil overlay-célja ugyanaz a fájl lehet (pl. a caelestia
profilok mind a ~/.config/caelestia/hypr-user.lua-t használják), és ezt a fájlt
a my-caelestia profil is BETÖLTI. Ha egy korábbi profil managed blokkja
bennemarad, a bindok megduplázódnak — két egymást kioltó toggle.
"""
import json
import sys

# Ezek nem beállítások, hanem dokumentáció a common.json-ban.
IGNORED_KEYS = ("_comment",)


# ─────────────────────────────────────────────────────────────────────────────
#  input blokk
# ─────────────────────────────────────────────────────────────────────────────

def fmt_value(v, fmt: str) -> str:
    """Egy skalár érték a cél formátum szerint."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return f'"{v}"' if fmt == "lua" else str(v)


def emit(d: dict, fmt: str, indent: int) -> list[str]:
    """Rekurzívan (egy szint mélyen) kiírja a kulcs-érték párokat."""
    pad = " " * indent
    scalars, blocks = [], []

    for k, v in d.items():
        if k in IGNORED_KEYS:
            continue
        if isinstance(v, dict):
            blocks.append((k, v))
            continue
        # Az üres stringet szándékosan kihagyjuk (pl. kb_variant: "")
        if isinstance(v, str) and v == "":
            continue
        if fmt == "lua":
            scalars.append(f"{pad}{k} = {fmt_value(v, fmt)},")
        else:
            scalars.append(f"{pad}{k} = {fmt_value(v, fmt)}")

    lines = list(scalars)
    for name, sub in blocks:
        inner = emit(sub, fmt, indent + 4)
        if not inner:
            continue
        if fmt == "lua":
            lines.append(f"{pad}{name} = {{")
            lines.extend(inner)
            lines.append(f"{pad}}},")
        else:
            lines.append(f"{pad}{name} {{")
            lines.extend(inner)
            lines.append(f"{pad}}}")
    return lines


def build_input(inp: dict, fmt: str) -> list[str]:
    inner = emit(inp, fmt, 8 if fmt == "lua" else 4)
    if not inner:
        return []
    if fmt == "lua":
        return ["hl.config({", "    input = {", *inner, "    }", "})"]
    return ["input {", *inner, "}"]


# ─────────────────────────────────────────────────────────────────────────────
#  binds
# ─────────────────────────────────────────────────────────────────────────────
#
# A conf és a lua forma szerkezetileg más: a conf pozicionális
# ("bind = MODS, KEY, dispatcher, args"), a lua strukturált
# ("hl.bind('MODS + KEY', hl.dsp.<terület>.<művelet>({ ... }))").
#
# Ezért a common.json absztrakt formában írja le a bindot, és itt van a
# dispatcher → lua leképezés. Ha egy dispatcher nem szerepel a táblában, a
# bind kimarad és figyelmeztetés megy a stderr-re — csendben nem generálunk
# rossz kódot. Kézi felülbírálásra van "lua" és "conf" kulcs is.

def _lua_fullscreenstate(args: str) -> str:
    parts = args.replace(",", " ").split()
    internal = parts[0] if len(parts) > 0 else "0"
    client = parts[1] if len(parts) > 1 else "2"
    return (f'hl.dsp.window.fullscreen_state({{ internal = {internal}, '
            f'client = {client}, action = "toggle" }})')


def _lua_exec(args: str) -> str:
    escaped = args.replace("\\", "\\\\").replace('"', '\\"')
    return f'hl.dsp.exec_cmd("{escaped}")'


LUA_DISPATCHERS = {
    "fullscreenstate": _lua_fullscreenstate,
    "exec": _lua_exec,
    "killactive": lambda a: "hl.dsp.window.close()",
    "togglefloating": lambda a: "hl.dsp.window.toggle_floating()",
    "pin": lambda a: "hl.dsp.window.pin()",
    "centerwindow": lambda a: "hl.dsp.window.center()",
    "fullscreen": lambda a: (
        'hl.dsp.window.fullscreen_state({ internal = '
        + (a.strip() or "0") + ', client = 0, action = "toggle" })'),
}

# A conf bind-flagek (bindl, bindd, binde…) → lua opciók
LUA_BIND_OPTS = {"l": "locked = true", "e": "repeating = true",
                 "m": "mouse = true", "r": "release = true"}


def build_binds(binds: list, fmt: str) -> list[str]:
    lines: list[str] = []
    for b in binds:
        if not isinstance(b, dict) or b.get("enabled") is False:
            continue

        desc = b.get("description", "")
        override = b.get(fmt)
        if override:
            if desc:
                lines.append(("-- " if fmt == "lua" else "# ") + desc)
            lines.append(override)
            continue

        keys = b.get("keys", "").strip()          # pl. "SUPER, Y"
        disp = b.get("dispatcher", "").strip()
        args = str(b.get("args", "")).strip()
        flags = b.get("flags", "").strip()        # pl. "l" → bindl

        if not keys or not disp:
            print(f"apply_overlay: bind kihagyva (hiányzó keys/dispatcher): {b}",
                  file=sys.stderr)
            continue

        if desc:
            lines.append(("-- " if fmt == "lua" else "# ") + desc)

        if fmt in ("conf", "conf-hl"):
            tail = f", {args}" if args else ""
            lines.append(f"bind{flags} = {keys}, {disp}{tail}")
            continue

        # lua
        maker = LUA_DISPATCHERS.get(disp)
        if maker is None:
            print(f"apply_overlay: '{disp}' dispatcher nincs leképezve lua-ra "
                  f"(bind: {keys}). Adj meg explicit \"lua\" kulcsot a "
                  f"common.json-ban.", file=sys.stderr)
            if lines and lines[-1].startswith("--"):
                lines.pop()
            continue

        # "SUPER, Y" → "SUPER + Y"
        combo = " + ".join(p.strip() for p in keys.split(",") if p.strip())
        opts = [LUA_BIND_OPTS[c] for c in flags if c in LUA_BIND_OPTS]
        opt_str = (", { " + ", ".join(opts) + " }") if opts else ""
        lines.append(f'hl.bind("{combo}", {maker(args)}{opt_str})')

    return lines


# ─────────────────────────────────────────────────────────────────────────────
#  windowrules
# ─────────────────────────────────────────────────────────────────────────────
#
#   conf:  windowrule = opacity 1 1 override, class:^(foo)$
#   lua:   hl.config({ windowrule = { "opacity 1 1 override, class:^(foo)$" } })

def render_match(match, fmt: str) -> str:
    """A match-feltétel a cél formátum szerint.

    conf-hl:  "match:class ^(foo)$"   (a translator ezt várja)
    conf/lua: "class:^(foo)$"         (igazi Hyprland szintaxis)
    """
    if isinstance(match, str):
        return match.strip()
    parts = []
    for k, v in match.items():
        if k in IGNORED_KEYS:
            continue
        if fmt == "conf-hl":
            parts.append(f"match:{k} {v}")
        else:
            parts.append(f"{k}:{v}")
    return ", ".join(parts)


def build_windowrules(rules: list, fmt: str) -> list[str]:
    entries = []
    for r in rules:
        if isinstance(r, dict):
            if r.get("enabled") is False:
                continue
            rule = r.get("rule", "").strip()
            if not rule:
                continue
            match = render_match(r.get("match", ""), fmt)
            entries.append(f"{rule}, {match}" if match else rule)
        elif isinstance(r, str) and r.strip():
            entries.append(r.strip())

    if not entries:
        return []

    if fmt == "lua":
        body = [f'        "{e}",' for e in entries]
        return ["hl.config({", "    windowrule = {", *body, "    }", "})"]
    return [f"windowrule = {e}" for e in entries]


# ─────────────────────────────────────────────────────────────────────────────

def build_body(data: dict, fmt: str) -> str:
    sections: list[list[str]] = []

    inp = build_input(data.get("input", {}), fmt)
    if inp:
        sections.append(inp)

    binds = build_binds(data.get("binds", []), fmt)
    if binds:
        sections.append(binds)

    rules = build_windowrules(data.get("windowrules", []), fmt)
    if rules:
        sections.append(rules)

    return "\n\n".join("\n".join(s) for s in sections)


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: apply_overlay.py <common.json|--strip> <target> <lua|conf|conf-hl>",
              file=sys.stderr)
        return 2
    first, target, fmt = sys.argv[1], sys.argv[2], sys.argv[3]

    if fmt not in ("lua", "conf", "conf-hl"):
        print(f"apply_overlay: ismeretlen formátum: {fmt}", file=sys.stderr)
        return 2

    strip_only = first == "--strip"
    if strip_only:
        body = ""
    else:
        with open(first) as f:
            data = json.load(f)
        body = build_body(data, fmt)

    comment = "--" if fmt == "lua" else "#"
    begin = f"{comment} >>> dotswitch managed (common settings) >>>"
    end = f"{comment} <<< dotswitch managed <<<"

    try:
        with open(target) as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        lines = []

    # Strip any previous managed block (idempotent).
    out, skip = [], False
    for ln in lines:
        s = ln.strip()
        if s == begin:
            skip = True
            continue
        if skip and s == end:
            skip = False
            continue
        if not skip:
            out.append(ln)

    if body:
        while out and out[-1].strip() == "":
            out.pop()
        if out:
            out.append("")
        out.append(begin)
        out.extend(body.splitlines())
        out.append(end)

    with open(target, "w") as f:
        f.write("\n".join(out) + ("\n" if out else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
