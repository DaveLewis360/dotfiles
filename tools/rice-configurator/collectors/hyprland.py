"""Hyprland: opciók, animációk, bindok, szabályok, autostart, env, monitorok.

Két forrásból dolgozik:
  1. hl_dump.lua: a profil .lua configjának hl.* hívásai (fájl:sor), futtatás
     nélkül, egy mock `hl` táblával;
  2. a futó Hyprland lekérdező parancsai: `hyprctl -i 0 descriptions -j`
     (minden opció leírással, alapértékkel, élő értékkel, határokkal) és
     `hyprctl -i 0 animations -j`. Ha a Hyprland nem érhető el, a legutóbbi
     sikeres lekérdezés gyorsítótárából (data/hypr-live.json) dolgozik.

Író hyprctl-parancsot (keyword, reload, dispatch) nem futtat.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from common import comment_above, entry, run, tilde, where

HERE = Path(__file__).resolve().parent

# opció-előtag → (kategória, csoport-felirat)
OPTION_CATS = [
    ("general.snap", "hypr.general"), ("general", "hypr.general"), ("layout", "hypr.general"),
    ("layers", "hypr.general"),
    ("decoration", "hypr.decoration"),
    ("animations", "hypr.animations"),
    ("input", "hypr.input"), ("input-capture", "hypr.input"),
    ("gestures", "hypr.gestures"),
    ("group", "hypr.group"),
    ("dwindle", "hypr.layouts"), ("master", "hypr.layouts"), ("scrolling", "hypr.layouts"),
    ("misc", "hypr.misc"), ("binds", "hypr.misc"), ("cursor", "hypr.misc"), ("xwayland", "hypr.misc"),
    ("ecosystem", "hypr.misc"), ("quirks", "hypr.misc"),
    ("render", "hypr.render"), ("opengl", "hypr.render"), ("experimental", "hypr.render"),
    ("debug", "hypr.render"),
]

CATEGORIES = [
    ("hypr.general", "Általános", "Rések, keret, elrendezés választása, ablak-snapping."),
    ("hypr.decoration", "Díszítés", "Lekerekítés, átlátszóság, blur, árnyék, glow, wobble."),
    ("hypr.animations", "Animációk", "Görbék (bezier), animáció-ágak (sebesség: 1 = 100 ms), stílusok."),
    ("hypr.input", "Bevitel", "Billentyűzet, egér, touchpad, tablet; eszközönkénti felülírások."),
    ("hypr.gestures", "Gesztusok", "Touchpad-gesztusok és a munkaterület-swipe beállításai."),
    ("hypr.group", "Csoportok (tabok)", "Ablakcsoportok keretszínei és a csoport-sáv."),
    ("hypr.layouts", "Elrendezések", "dwindle, master és scrolling elrendezés beállításai."),
    ("hypr.misc", "Egyéb", "misc, binds, cursor, xwayland, ecosystem, quirks."),
    ("hypr.render", "Renderelés és debug", "render, opengl, experimental, debug."),
    ("hypr.binds", "Billentyűparancsok", "A ténylegesen érvényes bindok (az overlay által felülírtak nélkül)."),
    ("hypr.rules", "Ablak- és rétegszabályok", "window_rule, layer_rule, workspace_rule."),
    ("hypr.exec", "Autostart és parancsok", "hl.exec_cmd: indításkor (hyprland.start) vagy minden config-betöltéskor."),
    ("hypr.env", "Környezeti változók", "hl.env: a Hyprland és a belőle indított appok környezete."),
    ("hypr.monitors", "Monitorok és eszközök", "hl.monitor és hl.device."),
    ("hypr.vars", "Config-változók", "A core/definitions.lua globális változói (alkalmazások, rések, modifierek)."),
]

# Az animációs fa (Hyprland wiki): ág → szülő. Az ismeretlen ág szülője a global.
ANIM_PARENT = {
    "windows": "global", "windowsIn": "windows", "windowsOut": "windows", "windowsMove": "windows",
    "layers": "global", "layersIn": "layers", "layersOut": "layers",
    "fade": "global", "fadeIn": "fade", "fadeOut": "fade", "fadeSwitch": "fade", "fadeShadow": "fade",
    "fadeDim": "fade", "fadeLayers": "fade", "fadeLayersIn": "fadeLayers", "fadeLayersOut": "fadeLayers",
    "fadePopups": "fade", "fadePopupsIn": "fadePopups", "fadePopupsOut": "fadePopups", "fadeDpms": "fade",
    "fadeGlow": "fade",
    "border": "global", "borderangle": "global", "glowangle": "global", "shadowangle": "global",
    "workspaces": "global", "workspacesIn": "workspaces", "workspacesOut": "workspaces",
    "specialWorkspace": "workspaces", "specialWorkspaceIn": "specialWorkspace",
    "specialWorkspaceOut": "specialWorkspace",
    "zoomFactor": "global", "monitorAdded": "global",
}
STYLES = {
    "windows": ["slide", "slide top", "slide bottom", "slide left", "slide right", "popin", "popin 80%", "gnomed"],
    "layers": ["slide", "slide top", "slide bottom", "slide left", "slide right", "popin", "popin 80%", "fade"],
    "fadePopups": ["slide", "popin", "fade"],
    "workspaces": ["slide", "slidevert", "fade", "slidefade", "slidefade 20%", "slidefadevert", "slidefadevert 20%"],
    "borderangle": ["once", "loop"],
}


def _style_family(leaf: str) -> str | None:
    cur = leaf
    while cur and cur != "global":
        if cur in STYLES:
            return cur
        cur = ANIM_PARENT.get(cur, "global")
    return None


def _norm(v):
    """Összehasonlításhoz: a config stringként adhat számot ("0.1696")."""
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, (int, float)):
        return round(float(v), 6)
    if isinstance(v, str):
        s = v.strip()
        if s == "[[EMPTY]]":
            return ""
        if s.lower() in ("true", "yes", "on"):
            return True
        if s.lower() in ("false", "no", "off"):
            return False
        try:
            return round(float(s), 6)
        except ValueError:
            return s
    if isinstance(v, list):
        return [_norm(x) for x in v]
    return v


def _canon(v):
    """Az élő (hyprctl) és a config-érték közös alakra: színek RRGGBBAA, "5 5 5 5" → 5."""
    if isinstance(v, str):
        s = v.strip().lower()
        s = re.sub(r"\s+0deg$", "", s)
        m = re.fullmatch(r"rgb\(([0-9a-f]{6})\)", s)
        if m:
            return m.group(1) + "ff"
        m = re.fullmatch(r"rgba\(([0-9a-f]{8})\)", s)
        if m:
            return m.group(1)
        m = re.fullmatch(r"0x([0-9a-f]{2})([0-9a-f]{6})", s)
        if m:
            return m.group(2) + m.group(1)
        m = re.fullmatch(r"([0-9a-f]{2})([0-9a-f]{6})", s)
        if m:
            return m.group(2) + m.group(1)
        parts = s.split()
        if len(parts) == 4 and len(set(parts)) == 1:
            return _norm(parts[0])
    return _norm(v)


def _clean(v):
    return "" if v == "[[EMPTY]]" else v


def _opt_cat(key: str) -> str:
    for prefix, cat in OPTION_CATS:
        if key == prefix or key.startswith(prefix + "."):
            return cat
    return "hypr.misc"


def _dsp_text(d) -> str:
    if isinstance(d, dict) and "dsp" in d:
        args = ", ".join(json.dumps(a, ensure_ascii=False) if not isinstance(a, str) else a for a in d["args"])
        return f"{d['dsp']}({args})" if args else d["dsp"]
    return json.dumps(d, ensure_ascii=False)


def _match_text(m) -> str:
    if not isinstance(m, dict):
        return str(m)
    return ", ".join(f"{k}: {v}" for k, v in sorted(m.items()))


def live_data(cache: Path) -> tuple[dict, str]:
    """(élő adat, forrás-megjegyzés) — hyprctl, vagy a gyorsítótár."""
    desc = run(["hyprctl", "-i", "0", "descriptions", "-j"], timeout=15)
    anims = run(["hyprctl", "-i", "0", "animations", "-j"], timeout=10)
    ver = run(["hyprctl", "-i", "0", "version", "-j"], timeout=5)
    try:
        data = {"descriptions": json.loads(desc), "animations": json.loads(anims)}
        try:
            v = json.loads(ver)
            data["version"] = v.get("version") or v.get("tag", "")
        except (TypeError, ValueError):
            data["version"] = ""
        data = tilde(data)
        cache.write_text(json.dumps(data, ensure_ascii=False, indent=0, sort_keys=True))
        return data, "élő (hyprctl)"
    except (TypeError, ValueError):
        if cache.exists():
            return json.loads(cache.read_text()), f"gyorsítótár ({cache.name}), mert a Hyprland nem volt elérhető"
        return {"descriptions": [], "animations": [[], []], "version": ""}, "nincs élő adat"


def _dump(hypr_dir: Path) -> list[dict]:
    out = run(["lua", str(HERE / "hl_dump.lua"), str(hypr_dir)], timeout=30)
    if out is None:
        raise RuntimeError("a hl_dump.lua nem futott le")
    return [json.loads(l) for l in out.splitlines() if l.strip()]


def _precise_line(src: str, leaf: str, line: int, files: dict) -> tuple[int, str]:
    """A hl.config({...}) blokkon belül a kulcs saját sora, és a használt séma-változó."""
    lines = files.get(src)
    if lines is None:
        try:
            lines = Path(src).read_text().split("\n")
        except OSError:
            lines = []
        files[src] = lines
    pat = re.compile(r'(^|[\s{,])(\["(?:col\.)?' + re.escape(leaf) + r'"\]|' + re.escape(leaf) + r')\s*=')
    for i in range(max(0, line - 1), len(lines)):
        if pat.search(lines[i]):
            m = re.search(r'_G\["(\w+)"\]', lines[i])
            return i + 1, (m.group(1) if m else "")
    return line, ""


def collect(hypr_dir: Path, cache: Path) -> dict:
    calls = _dump(hypr_dir)
    errors = [c for c in calls if c["fn"] == "error"]
    live, live_src = live_data(cache)
    entries: list[dict] = []
    files: dict = {}
    comments: dict = {}

    # ── opciók ────────────────────────────────────────────────────────────
    sets: dict[str, list[dict]] = {}
    for c in calls:
        if c["fn"] == "config":
            src = c["src"]
            leaf = c["path"].split(".")[-1]
            line, var = _precise_line(src, leaf, c["line"], files)
            sets.setdefault(c["path"], []).append({"value": c["value"], "file": where(src, line), "var": var})

    seen = set()
    for d in live.get("descriptions", []):
        key = d["name"].replace(":", ".")
        seen.add(key)
        default, live_v = _clean(d.get("default")), _clean(d.get("current"))
        s = sets.get(key, [])
        cur = s[-1]["value"] if s else live_v
        desc = d.get("description", "")
        options = None
        if d.get("map"):
            pairs = sorted(((list(m.values())[0], list(m.keys())[0]) for m in d["map"]), key=lambda p: p[0])
            options = [[v, l] for v, l in pairs]
        else:
            m = re.search(r"\[([^\]]*/[^\]]*)\]", desc)
            if m:
                options = [o.strip() for o in m.group(1).split("/") if o.strip()]
        leaf = key.split(".")[-1]
        if isinstance(default, bool):
            typ = "bool"
        elif ".col." in "." + key or leaf.startswith("col.") or "color" in leaf or leaf == "text_color":
            typ = "color"
        elif "font_family" in leaf or leaf == "font":
            typ = "font"
        elif options:
            typ = "enum"
        elif isinstance(default, float):
            typ = "float"
        elif isinstance(default, int):
            typ = "int"
        elif isinstance(default, list):
            typ = "list"
        else:
            typ = "string"
        note = []
        if len(s) > 1:
            note.append("Többször beállítva: " + " → ".join(x["file"].split("/")[-1] for x in s)
                        + " (az utolsó érvényes).")
        if s and s[-1]["var"]:
            note.append(f'Az értéket a színséma adja (_G["{s[-1]["var"]}"]); sémaváltáskor változik.')
        e = entry("hypr:" + key, _opt_cat(key), key, cur, desc=desc, type=typ, default=default,
                  options=options, vmin=d.get("min"), vmax=d.get("max"),
                  file=s[-1]["file"] if s else "", set=bool(s),
                  group=".".join(key.split(".")[:-1]) or key.split(".")[0], note=" ".join(note),
                  preview="color" if typ == "color" else ("font" if typ == "font" else ""))
        if s and _canon(cur) != _canon(live_v) and live_v is not None and live.get("descriptions"):
            e["live"] = live_v
        entries.append(e)

    for key, s in sets.items():
        if key in seen:
            continue
        note = "A futó Hyprland nem ismeri ezt a kulcsot (elavult, elírás, vagy nincs élő adat)." \
            if live.get("descriptions") else ""
        entries.append(entry("hypr:" + key, _opt_cat(key), key, s[-1]["value"], type="", default=None,
                             file=s[-1]["file"], set=True, group=".".join(key.split(".")[:-1]),
                             note=note, has_default=False))

    # ── animációk ─────────────────────────────────────────────────────────
    al = live.get("animations") or []
    anim_live = al[0] if len(al) > 0 else []
    bez_live = al[1] if len(al) > 1 else []
    curves_cfg = {}
    for c in calls:
        if c["fn"] == "curve":
            name, spec = c["args"][0], c["args"][1] if len(c["args"]) > 1 else {}
            curves_cfg[name] = {"points": spec.get("points"), "file": where(c["src"], c["line"])}
    curves = {}
    for b in bez_live:
        curves[b["name"]] = [[b["X0"], b["Y0"]], [b["X1"], b["Y1"]]]
    for name, cc in curves_cfg.items():
        curves[name] = cc["points"]
    curves.setdefault("default", [[0.0, 0.75], [0.15, 1.0]])
    for name, pts in sorted(curves.items()):
        cc = curves_cfg.get(name)
        desc = "Beépített görbe." if name == "default" and not cc else ""
        entries.append(entry("hypr-curve:" + name, "hypr.animations", name, pts, type="curve",
                             desc=desc, default=None, has_default=False, file=cc["file"] if cc else "",
                             set=bool(cc), group="Görbék (hl.curve)", preview="curve",
                             note="" if cc else ("Nincs a configban (élő adatból)." if name != "default" else "")))

    anim_cfg = {}
    for c in calls:
        if c["fn"] == "animation":
            a = c["args"][0]
            anim_cfg[a.get("leaf")] = {"spec": a, "file": where(c["src"], c["line"])}
    by_name = {a["name"]: a for a in anim_live if not a["name"].startswith("__")}
    for leaf in anim_cfg:
        by_name.setdefault(leaf, {"name": leaf, "overridden": True})

    def resolve(leaf):
        cur, seen_ = leaf, set()
        while cur and cur not in seen_:
            seen_.add(cur)
            if cur in anim_cfg:
                sp = anim_cfg[cur]["spec"]
                return {"bezier": sp.get("bezier", "default"), "speed": sp.get("speed"),
                        "style": sp.get("style", ""), "enabled": sp.get("enabled", True)}, cur
            a = by_name.get(cur)
            if a and a.get("overridden"):
                return {"bezier": a["bezier"], "speed": a["speed"], "style": a["style"],
                        "enabled": a["enabled"]}, cur
            if cur == "global":
                break
            cur = ANIM_PARENT.get(cur, "global")
        return {"bezier": "default", "speed": 8.0, "style": "", "enabled": True}, "global"

    order = list(dict.fromkeys(["global"] + [k for k in ANIM_PARENT] + sorted(by_name)))
    for leaf in order:
        if leaf not in by_name and leaf != "global":
            continue
        val, src_leaf = resolve(leaf)
        val["curve"] = curves.get(val["bezier"])
        fam = _style_family(leaf)
        own = leaf in anim_cfg
        note = "" if own or src_leaf == leaf else f"Öröklött érték: {src_leaf}."
        entries.append(entry("hypr-anim:" + leaf, "hypr.animations", leaf, val, type="animation",
                             desc=f"Szülő: {ANIM_PARENT.get(leaf, '—') if leaf != 'global' else '—'}.",
                             default=None, has_default=False,
                             options=STYLES.get(fam) if fam else None,
                             file=anim_cfg[leaf]["file"] if own else "", set=own,
                             group="Animáció-ágak (hl.animation)", preview="anim", note=note))

    # ── bindok ────────────────────────────────────────────────────────────
    effective: dict[str, list[dict]] = {}
    overridden = 0
    for c in calls:
        if c["fn"] == "unbind":
            combo = c["args"][0] if c["args"] else ""
            overridden += len(effective.pop(combo, []))
        elif c["fn"] == "bind":
            effective.setdefault(c["args"][0], []).append(c)
    for combo, binds in effective.items():
        for i, c in enumerate(binds):
            dsp = c["args"][1] if len(c["args"]) > 1 else None
            flags = c["args"][2] if len(c["args"]) > 2 and isinstance(c["args"][2], dict) else {}
            text = _dsp_text(dsp)
            name = dsp.get("dsp", "") if isinstance(dsp, dict) else ""
            argstr = " ".join(str(a) for a in (dsp.get("args", []) if isinstance(dsp, dict) else []))
            if "XF86" in combo or "mouse" in combo.lower():
                grp = "Média, hardvergombok, egér"
            elif name == "global":
                grp = "Caelestia shell"
            elif name.startswith("exec"):
                grp = "Programindítás és parancsok"
            elif "workspace" in name or "workspace" in argstr:
                grp = "Munkaterületek"
            elif name.startswith("window") or name.startswith("group") or name.startswith("layout"):
                grp = "Ablakok"
            else:
                grp = "Egyéb"
            desc = comment_above(Path(c["src"]), c["line"], comments)
            suffix = f"#{i + 1}" if len(binds) > 1 else ""
            entries.append(entry(f"hypr-bind:{combo}|{name}{suffix}", "hypr.binds", combo,
                                 text + ("  " + json.dumps(flags) if flags else ""), type="bind", desc=desc,
                                 default=None, has_default=False, file=where(c["src"], c["line"]), set=True,
                                 group=grp, preview="keys"))

    # ── szabályok ─────────────────────────────────────────────────────────
    counter: dict[str, int] = {}
    for c in calls:
        if c["fn"] not in ("window_rule", "layer_rule", "workspace_rule"):
            continue
        a = c["args"][0] if c["args"] else {}
        if c["fn"] == "workspace_rule":
            m = {"workspace": a.get("workspace")}
            props = {k: v for k, v in a.items() if k != "workspace"}
        else:
            m = a.get("match", {})
            props = {k: v for k, v in a.items() if k != "match"}
        mt = _match_text(m)
        base = f"hypr-{c['fn']}:{mt}|{','.join(sorted(props))}"
        counter[base] = counter.get(base, 0) + 1
        rid = base + (f"#{counter[base]}" if counter[base] > 1 else "")
        grp = {"window_rule": "Ablakszabályok", "layer_rule": "Rétegszabályok",
               "workspace_rule": "Munkaterület-szabályok"}[c["fn"]]
        entries.append(entry(rid, "hypr.rules", mt, props, type="rule",
                             desc=comment_above(Path(c["src"]), c["line"], comments),
                             default=None, has_default=False, file=where(c["src"], c["line"]), set=True,
                             group=grp))

    # ── exec, gesztus, env, monitor, eszköz, változó ─────────────────────
    gesture_n = 0
    for c in calls:
        fn = c["fn"]
        if fn == "exec_cmd":
            cmd = c["args"][0] if c["args"] else ""
            g = re.match(r'hyprctl keyword gesture "(.*)"$', cmd)
            if g:
                gesture_n += 1
                entries.append(entry(f"hypr-gesture:{g.group(1)}", "hypr.gestures", f"gesture #{gesture_n}",
                                     g.group(1), type="gesture",
                                     desc="Touchpad-gesztus: ujjak száma, irány, művelet. Indításkor egy "
                                          "`hyprctl keyword gesture` hívás állítja be.",
                                     default=None, has_default=False, file=where(c["src"], c["line"]),
                                     set=True, group="Gesztusok (hyprland.start)"))
                continue
            ev = c.get("event")
            entries.append(entry(f"hypr-exec:{cmd}", "hypr.exec", cmd, cmd, type="exec",
                                 desc=comment_above(Path(c["src"]), c["line"], comments),
                                 default=None, has_default=False, file=where(c["src"], c["line"]), set=True,
                                 group="Indításkor (hyprland.start)" if ev == "hyprland.start"
                                 else (f"Eseményre: {ev}" if ev else "Minden config-betöltéskor")))
    env: dict[str, list[dict]] = {}
    for c in calls:
        if c["fn"] == "env" and len(c["args"]) >= 2:
            env.setdefault(c["args"][0], []).append(c)
    for name, lst in env.items():
        last = lst[-1]
        note = ""
        if len(lst) > 1:
            vals = {str(x["args"][1]) for x in lst}
            note = ("Többször beállítva" + (" eltérő értékkel" if len(vals) > 1 else " ugyanazzal az értékkel")
                    + ": " + " → ".join(f'{Path(x["src"]).name}:{x["line"]}' for x in lst) + ".")
        entries.append(entry(f"hypr-env:{name}", "hypr.env", name, last["args"][1], type="string",
                             desc=comment_above(Path(last["src"]), last["line"], comments),
                             default=None, has_default=False, file=where(last["src"], last["line"]),
                             set=True, note=note,
                             group="Grafika / NVIDIA" if any(t in name for t in ("NV", "GBM", "LIBVA", "GLX"))
                             else ("Kurzor" if "CURSOR" in name else "Toolkit és session")))
    for c in calls:
        if c["fn"] == "monitor":
            a = c["args"][0]
            out = a.get("output") or "*"
            entries.append(entry(f"hypr-monitor:{out}", "hypr.monitors", f"monitor {out}",
                                 {k: v for k, v in a.items() if k != "output"}, type="object",
                                 desc="Üres output = minden más monitor (alapszabály)." if out == "*" else "",
                                 default=None, has_default=False, file=where(c["src"], c["line"]), set=True,
                                 group="Monitorok"))
        elif c["fn"] == "device":
            a = c["args"][0]
            entries.append(entry(f"hypr-device:{a.get('name')}", "hypr.monitors", f"device {a.get('name')}",
                                 {k: v for k, v in a.items() if k != "name"}, type="object",
                                 desc=comment_above(Path(c["src"]), c["line"], comments),
                                 default=None, has_default=False, file=where(c["src"], c["line"]), set=True,
                                 group="Eszközök"))
    defs = hypr_dir / "core/definitions.lua"
    def_lines = defs.read_text().split("\n") if defs.exists() else []
    scheme_vars = set()
    scheme_file = hypr_dir / "scheme/current.lua"
    if scheme_file.exists():
        scheme_vars = set(re.findall(r'_G\["(\w+)"\]', scheme_file.read_text()))
    for c in calls:
        if c["fn"] != "var" or c["path"] in scheme_vars:
            continue
        ln = next((i + 1 for i, l in enumerate(def_lines) if f'_G["{c["path"]}"] =' in l), None)
        if ln is None:
            continue
        entries.append(entry(f"hypr-var:{c['path']}", "hypr.vars", c["path"], c["value"], type="string",
                             desc=comment_above(defs, ln, comments), default=None, has_default=False,
                             file=where(defs, ln), set=True,
                             group="Billentyű-kombinációk" if c["path"].startswith("kb") or c["path"].endswith("Mod")
                             else "Értékek"))

    return {
        "entries": entries,
        "categories": CATEGORIES,
        "info": {"live_source": live_src, "version": live.get("version", ""), "binds_overridden": overridden,
                 "errors": [e["args"] for e in errors], "calls": len(calls)},
    }


if __name__ == "__main__":
    import collections
    import sys
    r = collect(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".config/hypr",
                HERE.parent / "data/hypr-live.json")
    print(r["info"])
    print(collections.Counter(e["cat"] for e in r["entries"]))
