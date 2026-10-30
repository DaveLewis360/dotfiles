"""Közös segédek a gyűjtőknek: bejegyzés-építés, útvonal-rövidítés, futtatás.

Minden gyűjtő csak olvas. A külső parancsok (hyprctl, ghostty, gsettings,
fc-list) mind lekérdezők; író hyprctl-parancsot (keyword, reload, dispatch)
egyik modul sem futtat.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

HOME = str(Path.home())


def tilde(s):
    """A home-könyvtár útvonalát ~-ra cseréli (stringben, listában, dictben is)."""
    if isinstance(s, str):
        return s.replace(HOME + "/", "~/").replace(HOME, "~")
    if isinstance(s, list):
        return [tilde(x) for x in s]
    if isinstance(s, dict):
        return {tilde(k) if isinstance(k, str) else k: tilde(v) for k, v in s.items()}
    return s


def where(path, line=None):
    p = tilde(str(path))
    return f"{p}:{line}" if line else p


def run(cmd: list[str], timeout: int = 15) -> str | None:
    """Egy lekérdező parancs stdout-ja, vagy None, ha nem sikerült."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def entry(id, cat, key, cur, *, label="", desc="", type="", default=None, options=None,
          vmin=None, vmax=None, file="", set=None, group="", live=None, note="", preview="",
          extra=None, has_default=True):
    e = {"id": id, "cat": cat, "key": key, "cur": cur}
    if group:
        e["group"] = group
    if label:
        e["label"] = label
    if desc:
        e["desc"] = desc
    e["type"] = type or guess_type(cur)
    if has_default:
        e["def"] = default
    if options:
        e["opts"] = options
    if vmin is not None:
        e["min"] = vmin
    if vmax is not None:
        e["max"] = vmax
    if file:
        e["file"] = file
    if set is not None:
        e["set"] = set
    if live is not None:
        e["live"] = live
    if note:
        e["note"] = note
    if preview:
        e["prev"] = preview
    if extra:
        e["x"] = extra
    return e


def guess_type(v):
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "object"
    return "string"


HEX6 = re.compile(r"^#?[0-9a-fA-F]{6}$")


def humanize(key: str) -> str:
    """camelCase / snake_case kulcsrész olvasható szavakra."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key).replace("_", " ").replace("-", " ")
    return s[:1].upper() + s[1:]


def comment_above(path: Path, line: int, cache: dict) -> str:
    """A megadott sor fölötti összefüggő -- / # kommentblokk (vagy a sor végi komment)."""
    if not line:
        return ""
    lines = cache.get(path)
    if lines is None:
        try:
            lines = Path(path).read_text().split("\n")
        except OSError:
            lines = []
        cache[path] = lines
    if line - 1 >= len(lines):
        return ""
    own = lines[line - 1]
    m = re.search(r"\s--\s*(.+)$", own)
    if m and '"' not in m.group(1):
        return m.group(1).strip()
    out = []
    i = line - 2
    while i >= 0:
        s = lines[i].strip()
        if s.startswith("--") and not s.startswith("---") and "====" not in s:
            out.append(s.lstrip("-").strip())
            i -= 1
        else:
            break
    return " ".join(reversed(out)).strip()
