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
  windowrules  — közös ablakszabályok, minden profilban ugyanazok
  cliToggles   — a 'caelestia toggle <név>' app-definíciói; NEM hypr config,
                 ezért a ~/.config/caelestia/cli.json-ba olvad be (--cli-target)

Minden bind elé UNBIND kerül. Hyprlandban két bind ugyanazon a gombon
ÖSSZEADÓDIK, nem felülírja egymást — két toggle így kioltaná önmagát. Az unbind
nélkül a közös réteg nem felülírná a rice sajátját, hanem duplikálná.

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
import pathlib
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
            lines.append(f"unbind = {keys}")
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
        lines.append(f'hl.unbind("{combo}")')
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

def merge_cli_toggles(data: dict, cli_path: str) -> str | None:
    """A cliToggles beolvasztása a caelestia CLI cli.json-jába.

    Ez nem hypr config, hanem a `caelestia toggle <név>` app-definíciói. Azért
    kell külön kezelni, mert JSON, és mert a felhasználó egyéb kulcsait
    (wallpaper, theme, record) NEM szabad elveszíteni.
    """
    toggles = {k: v for k, v in data.get("cliToggles", {}).items()
               if k not in IGNORED_KEYS}
    if not toggles:
        return None

    path = pathlib.Path(cli_path)
    try:
        current = json.loads(path.read_text())
        if not isinstance(current, dict):
            return f"{cli_path} nem JSON objektum — kihagyva"
    except FileNotFoundError:
        current = {}
    except json.JSONDecodeError as e:
        return f"{cli_path} hibás JSON ({e}) — kihagyva"

    before = json.dumps(current.get("toggles"), sort_keys=True)
    current["toggles"] = toggles
    if json.dumps(current["toggles"], sort_keys=True) == before:
        return None

    path.parent.mkdir(parents=True, exist_ok=True)
    # A symlinket követjük: a profil saját cli.json-ját írjuk, nem cseréljük le.
    path.write_text(json.dumps(current, indent=4, ensure_ascii=False) + "\n")
    return f"cliToggles → {cli_path} ({', '.join(sorted(toggles))})"


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
    args = sys.argv[1:]
    cli_target = None
    if "--cli-target" in args:
        i = args.index("--cli-target")
        try:
            cli_target = args[i + 1]
        except IndexError:
            print("apply_overlay: --cli-target érték nélkül", file=sys.stderr)
            return 2
        del args[i:i + 2]

    if len(args) != 3:
        print("usage: apply_overlay.py <common.json|--strip> <target> <lua|conf|conf-hl>\n"
              "                        [--cli-target <cli.json>]", file=sys.stderr)
        return 2
    first, target, fmt = args[0], args[1], args[2]

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

    if not strip_only and cli_target:
        note = merge_cli_toggles(data, cli_target)
        if note:
            print(f"apply_overlay: {note}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
