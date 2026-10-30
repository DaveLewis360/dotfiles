"""Terminálok: Ghostty (minden opció a saját dokumentációjával) és foot.

Ghostty: `ghostty +show-config --default --docs` (csak kiírja az alapconfigot,
ablakot nem nyit) + a profil configja és a `config-file` include-ok.
foot: a csomag /etc/xdg/foot/foot.ini mintafájlja (minden opció az
alapértékével) + a profil foot.ini-je.
"""
from __future__ import annotations

import re
from pathlib import Path

from common import entry, run, tilde, where

GHOSTTY_GROUPS = {
    "font": "Betű", "adjust": "Betű-finomhangolás", "window": "Ablak", "cursor": "Kurzor", "mouse": "Egér",
    "clipboard": "Vágólap", "gtk": "GTK", "background": "Háttér", "selection": "Kijelölés",
    "keybind": "Billentyűk", "shell": "Shell-integráció", "quick": "Quick terminal", "macos": "macOS",
    "linux": "Linux", "app": "Alkalmazás", "confirm": "Megerősítések", "unfocused": "Fókusz nélkül",
    "split": "Osztott nézet", "resize": "Átméretezés", "scrollback": "Görgetés", "palette": "Színek",
    "foreground": "Színek", "minimum": "Színek", "bold": "Betű", "theme": "Színek", "image": "Kép",
    "osc": "Terminál-protokoll", "term": "Terminál-protokoll", "desktop": "Értesítések",
    "notify": "Értesítések", "auto": "Frissítés", "async": "Teljesítmény", "freetype": "Betű",
    "grapheme": "Betű", "custom": "Shader", "link": "Linkek", "title": "Ablak", "command": "Indítás",
    "initial": "Indítás", "working": "Indítás", "wait": "Indítás", "abnormal": "Indítás", "env": "Indítás",
    "input": "Indítás", "config": "Config", "click": "Egér", "focus": "Ablak", "faint": "Színek",
    "alpha": "Színek", "search": "Keresés", "bell": "Csengő", "undo": "Ablak", "maximize": "Ablak",
    "fullscreen": "Ablak", "class": "Ablak", "x11": "Linux", "language": "Alkalmazás", "progress": "Ablak",
    "copy": "Vágólap", "right": "Egér", "scroll": "Görgetés", "vt": "Billentyűk", "key": "Billentyűk",
}
COLOR_KEYS = re.compile(r"(^|-)(color|background|foreground|palette)($|-)|^selection-|^cursor-text$")


def _parse_kv(path: Path, sep="=") -> list[tuple[str, str, int]]:
    out = []
    try:
        lines = path.read_text().split("\n")
    except OSError:
        return out
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith("#") or sep not in s:
            continue
        k, v = s.split(sep, 1)
        out.append((k.strip(), v.strip(), i))
    return out


def _scalar(v: str):
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v


def ghostty(config: Path) -> tuple[list[dict], dict]:
    docs = run(["ghostty", "+show-config", "--default", "--docs"], timeout=20) or ""
    opts: dict[str, dict] = {}
    order: list[str] = []
    doc: list[str] = []
    last = None
    for line in docs.split("\n"):
        if line.startswith("#"):
            doc.append(line[1:].removeprefix(" "))
            last = None
            continue
        if not line.strip():
            last = None
            continue
        if "=" in line:
            k, v = (x.strip() for x in line.split("=", 1))
            if k == last:
                opts[k]["defaults"].append(v)
            else:
                if k not in opts:
                    opts[k] = {"defaults": [v], "doc": doc}
                    order.append(k)
                last = k
            doc = []
    # felhasználói értékek: a fő config, utána a config-file include-ok (a Ghostty a végén tölti be őket)
    user: dict[str, list[tuple[str, str]]] = {}
    includes = []
    for k, v, ln in _parse_kv(config):
        if k == "config-file":
            includes.append(Path(v.lstrip("?").replace("~", str(Path.home()), 1)))
        user.setdefault(k, []).append((v, where(config.resolve(), ln)))
    for inc in includes:
        for k, v, ln in _parse_kv(inc):
            user.setdefault(k, []).append((v, where(inc, ln) + " (generált)"))
    entries = []
    for k in order:
        o = opts[k]
        full = "\n".join(o["doc"]).strip()
        para = re.split(r"\n\s*\n", full)[0].replace("\n", " ") if full else ""
        para = (para[:420] + "…") if len(para) > 420 else para
        enum = re.findall(r"^\s*\*\s+`([^`]+)`", full, re.M)
        enum = list(dict.fromkeys(enum)) if 1 < len(enum) <= 24 else None
        defaults = [d for d in o["defaults"]]
        multi = len(defaults) > 1 or k in ("keybind", "palette", "font-family", "font-feature", "env")
        u = user.get(k)
        if multi:
            default = defaults if defaults != [""] else []
            cur = [x[0] for x in u] if u else default
        else:
            default = _scalar(defaults[0]) if defaults else ""
            cur = _scalar(u[-1][0]) if u else default
        if k.startswith("font-family"):
            typ = "font"
        elif isinstance(default, bool):
            typ = "bool"
        elif COLOR_KEYS.search(k) and not isinstance(default, (bool, int, float)) and k != "background-opacity":
            typ = "color" if not multi else "list"
        elif enum:
            typ = "enum"
        elif isinstance(default, (int, float)):
            typ = "float" if isinstance(default, float) else "int"
        else:
            typ = "list" if multi else "string"
        notes = []
        if re.search(r"\b(macOS only|only (supported|available|works) on macOS)\b", full, re.I):
            notes.append("Csak macOS-en hat.")
        if u and len(u) > 1 and not multi:
            notes.append("Többször beállítva: " + " → ".join(x[1].split("/")[-1] for x in u) + ".")
        if k == "keybind" and isinstance(default, list):
            para = f"{para} (Alapból {len(default)} bind.)".strip()
        prefix = k.split("-")[0]
        group = GHOSTTY_GROUPS.get(prefix, "Egyéb")
        if prefix == "macos" and "Csak macOS-en hat." not in notes:
            notes.append("Csak macOS-en hat.")
        if "Csak macOS-en hat." in notes:
            group = "macOS (Linuxon hatástalan)"
        entries.append(entry(f"ghostty:{k}", "term.ghostty", k, cur, desc=para, type=typ, default=default,
                             options=enum, file=u[-1][1] if u else where(config.resolve()), set=bool(u),
                             group=group, note=" ".join(notes),
                             preview="font" if typ == "font" else ("color" if typ == "color" else
                                                                    ("swatches" if k == "palette" else ""))))
    return entries, {"options": len(order), "docs": bool(docs), "config": where(config.resolve())}


def foot(config: Path) -> tuple[list[dict], dict]:
    sample = Path("/etc/xdg/foot/foot.ini")
    entries = []
    defaults: dict[tuple[str, str], tuple[str, str]] = {}
    section = "main"
    order = []
    if sample.exists():
        for line in sample.read_text().split("\n"):
            s = line.strip()
            m = re.fullmatch(r"#?\s*\[([^\]]+)\]", s)
            if m:
                section = m.group(1)
                continue
            m = re.fullmatch(r"#\s*([a-z0-9][\w.-]*)\s*=\s*(.*?)(?:\s+#\s*(.*))?", s)
            if m and (section, m.group(1)) not in defaults:
                defaults[(section, m.group(1))] = (m.group(2).strip(), (m.group(3) or "").strip())
                order.append((section, m.group(1)))
    user: dict[tuple[str, str], tuple[str, str]] = {}
    section = "main"
    try:
        lines = config.read_text().split("\n")
    except OSError:
        lines = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        m = re.fullmatch(r"\[([^\]]+)\]", s)
        if m:
            section = m.group(1)
            continue
        if s and not s.startswith("#") and "=" in s:
            k, v = (x.strip() for x in s.split("=", 1))
            user[(section, k)] = (v, where(config.resolve(), i))
            if (section, k) not in defaults:
                order.append((section, k))
    for sec, k in order:
        d, comment = defaults.get((sec, k), ("", ""))
        u = user.get((sec, k))
        cur = u[0] if u else d
        is_font = sec in ("main", "csd") and k in ("font", "font-bold", "font-italic", "font-bold-italic")
        typ = "bool" if d in ("yes", "no") else ("font" if is_font
                                                  else ("color" if sec.startswith("colors") else "string"))
        entries.append(entry(f"foot:{sec}.{k}", "term.foot", f"[{sec}] {k}", cur, desc=comment, type=typ,
                             default=d, options=["yes", "no"] if typ == "bool" else None,
                             file=u[1] if u else where(config.resolve()), set=bool(u), group=sec,
                             preview="font" if typ == "font" else ("color" if typ == "color" else "")))
    return entries, {"options": len(order), "sample": sample.exists()}


def collect(profile_dir: Path) -> dict:
    g, gi = ghostty(profile_dir / "ghostty/config")
    f, fi = foot(profile_dir / "foot/foot.ini")
    return {"entries": g + f,
            "categories": [
                ("term.ghostty", "Ghostty", "Az alapértelmezett terminál (SUPER+Return). Minden opció a Ghostty "
                                           "saját dokumentációjából; a színeket a sémaváltás generálja."),
                ("term.foot", "foot", "A foot terminál configja a profilban (a minta /etc/xdg/foot/foot.ini)."),
            ],
            "info": {"ghostty": gi, "foot": fi}}
