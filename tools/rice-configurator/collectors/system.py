"""Rendszertéma: GTK (gsettings), Qt (qt6ct), ikon- és kurzortémák, telepített betűk.

Csak lekérdez: `gsettings get`, `fc-list`, a téma-könyvtárak listázása.
"""
from __future__ import annotations

import configparser
import re
from pathlib import Path

from common import entry, run, tilde, where

GSETTINGS = [
    ("gtk-theme", "GTK-téma.", "theme"), ("icon-theme", "Ikon-téma.", "icon"),
    ("cursor-theme", "Kurzortéma (GTK-appok; a Hyprland az XCURSOR_THEME env-et használja).", "cursor"),
    ("cursor-size", "Kurzorméret (GTK).", None), ("color-scheme", "Sötét/világos preferencia az appoknak.", None),
    ("font-name", "Felület betűje (GTK).", "font"), ("document-font-name", "Dokumentum-betű.", "font"),
    ("monospace-font-name", "Fix szélességű betű.", "font"), ("font-antialiasing", "Élsimítás.", None),
    ("font-hinting", "Hinting.", None), ("text-scaling-factor", "Szövegméretezés.", None),
]
ENUMS = {"color-scheme": ["default", "prefer-dark", "prefer-light"],
         "font-antialiasing": ["none", "grayscale", "rgba"],
         "font-hinting": ["none", "slight", "medium", "full"]}


def _dirs(*bases) -> list[Path]:
    out = []
    for b in bases:
        p = Path(b).expanduser()
        if p.is_dir():
            out.extend(x for x in p.iterdir() if x.is_dir())
    return out


def themes() -> dict[str, list[str]]:
    roots = ("/usr/share/themes", "~/.themes", "~/.local/share/themes")
    gtk = sorted({d.name for d in _dirs(*roots) if (d / "gtk-3.0").is_dir() or (d / "gtk-4.0").is_dir()})
    iroots = ("/usr/share/icons", "~/.icons", "~/.local/share/icons")
    icons = sorted({d.name for d in _dirs(*iroots) if (d / "index.theme").exists() and not (d / "cursors").is_dir()})
    cursors = sorted({d.name for d in _dirs(*iroots) if (d / "cursors").is_dir()})
    return {"theme": gtk, "icon": icons, "cursor": cursors}


def fonts() -> list[str]:
    out = run(["fc-list", ":", "family"], timeout=20) or ""
    # minden név kell, az aliasok is (pl. "CaskaydiaCove Nerd Font,CaskaydiaCove NF")
    fams = {n.strip() for line in out.splitlines() for n in line.split(",") if n.strip()}
    return sorted(fams, key=str.lower)


def collect() -> dict:
    entries = []
    lists = themes()
    for key, desc, kind in GSETTINGS:
        v = run(["gsettings", "get", "org.gnome.desktop.interface", key], timeout=5)
        if v is None:
            continue
        v = v.strip()
        if v.startswith("'") and v.endswith("'"):
            v = v[1:-1]
        elif re.fullmatch(r"-?\d+", v):
            v = int(v)
        elif re.fullmatch(r"-?\d+\.\d+", v):
            v = float(v)
        opts = ENUMS.get(key) or (lists.get(kind) if kind in ("theme", "icon", "cursor") else None)
        typ = "font" if kind == "font" else ("enum" if opts else "")
        entries.append(entry(f"gsettings:{key}", "system.theme", key, v, desc=desc, type=typ, options=opts,
                             default=None, has_default=False, file="gsettings org.gnome.desktop.interface",
                             set=True, group="GTK (gsettings)", preview="font" if kind == "font" else ""))
    qt = Path.home() / ".config/qt6ct/qt6ct.conf"
    if qt.exists():
        cp = configparser.ConfigParser(interpolation=None)
        try:
            cp.read(qt)
        except configparser.Error:
            pass
        for sec, key, desc, kind in (("Appearance", "style", "Qt-stílus.", None),
                                     ("Appearance", "icon_theme", "Qt ikon-téma.", "icon"),
                                     ("Appearance", "color_scheme_path", "Qt színséma-fájl.", None),
                                     ("Appearance", "custom_palette", "Saját paletta használata.", None),
                                     ("Fonts", "general", "Qt felület-betű.", "font"),
                                     ("Fonts", "fixed", "Qt fix szélességű betű.", "font")):
            if cp.has_option(sec, key):
                v = cp.get(sec, key).strip('"')
                if kind == "font":
                    v = v.split(",")[0] + (f" {v.split(',')[1]}" if "," in v else "")
                entries.append(entry(f"qt6ct:{sec}.{key}", "system.theme", f"qt6ct [{sec}] {key}", tilde(v),
                                     desc=desc, type="font" if kind == "font" else ("enum" if kind else ""),
                                     options=lists.get(kind) if kind == "icon" else None, default=None,
                                     has_default=False, file=where(qt), set=True, group="Qt (qt6ct)",
                                     preview="font" if kind == "font" else ""))
    fl = fonts()
    return {"entries": entries,
            "categories": [("system.theme", "GTK, Qt, ikonok, kurzor",
                            "Az appok rendszertémája. A caelestia CLI (enableGtk, enableQt) sémaváltáskor "
                            "felülírhatja a színeket.")],
            "fonts": fl,
            "info": {"fonts": len(fl), "gtk_themes": len(lists["theme"]), "icon_themes": len(lists["icon"]),
                     "cursor_themes": len(lists["cursor"])}}
