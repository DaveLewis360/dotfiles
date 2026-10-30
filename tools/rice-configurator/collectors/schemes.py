"""Színsémák és a caelestia CLI (cli.json) beállításai.

Források (csak olvasás):
  - a CLI beépített sémái: <caelestia csomag>/data/schemes/<név>/<flavour>/<mode>.txt
  - a variánsok listája és a theme.enable* kapcsolók: utils/scheme.py, utils/theme.py
  - az aktuális séma: ~/.local/state/caelestia/scheme.json
  - a tapéta: ~/.local/state/caelestia/wallpaper/path.txt
  - a profil cli.json-ja
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from common import entry, tilde, where

# a sémák előnézetéhez megtartott színek (a teljes paletta a jelenlegi sémánál van meg)
PREVIEW_KEYS = ["background", "surfaceContainer", "surfaceContainerHigh", "onSurface", "onSurfaceVariant",
                "primary", "onPrimary", "primaryContainer", "secondary", "secondaryContainer", "tertiary",
                "tertiaryContainer", "error", "outline", "outlineVariant"]

THEME_TARGETS = {
    "enableTerm": "Terminálok színei (escape-szekvenciák a futó terminálokba).",
    "enableHypr": "Hyprland színek (scheme/current.lua vagy .conf): keretek, csoport-sáv, háttér.",
    "enableDiscord": "Discord-kliensek (Vesktop, Equibop stb.) CSS-témája.",
    "enableSpicetify": "Spotify (Spicetify) téma.",
    "enablePandora": "Pandora-téma (a CLI theme.py apply_pandora függvénye).",
    "enableFuzzel": "Fuzzel launcher színei.",
    "enableBtop": "btop téma.",
    "enableNvtop": "nvtop színek.",
    "enableHtop": "htop színek.",
    "enableGtk": "GTK 3/4 téma (gtk.css) és ikon-téma.",
    "enableQt": "Qt téma (qt5ct/qt6ct színséma) és ikon-téma.",
    "enableWarp": "Warp terminál téma.",
    "enableChromium": "Chromium-alapú böngészők téma-színe.",
    "enableZed": "Zed szerkesztő téma.",
    "enableCava": "cava audio-vizualizáló színei.",
}


def _pkg() -> Path | None:
    for base in sorted(Path("/usr/lib").glob("python3*/site-packages/caelestia")):
        if (base / "data/schemes").is_dir():
            return base
    return None


def _read_colours(p: Path) -> dict[str, str]:
    out = {}
    for line in p.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            out[parts[0]] = parts[1].lstrip("#").lower()
    return out


def collect(profile_dir: Path) -> dict:
    entries, info = [], {}
    pkg = _pkg()
    state = Path.home() / ".local/state/caelestia"
    try:
        cur = json.loads((state / "scheme.json").read_text())
    except (OSError, ValueError):
        cur = {}
    info["scheme_json"] = tilde(str(state / "scheme.json"))
    variants, enable_keys = [], []
    schemes: dict[str, dict[str, list[str]]] = {}
    if pkg:
        src = (pkg / "utils/scheme.py").read_text()
        m = re.search(r"scheme_variants\s*=\s*\[(.*?)\]", src, re.S)
        variants = re.findall(r'"(\w+)"', m.group(1)) if m else []
        enable_keys = re.findall(r'check\("(\w+)"\)', (pkg / "utils/theme.py").read_text())
        for txt in sorted((pkg / "data/schemes").glob("*/*/*.txt")):
            name, flav, mode = txt.parent.parent.name, txt.parent.name, txt.stem
            schemes.setdefault(name, {}).setdefault(flav, []).append(mode)
            colours = _read_colours(txt)
            entries.append(entry(
                f"scheme-builtin:{name}/{flav}/{mode}", "scheme.list", f"{name} · {flav} · {mode}",
                {k: colours[k] for k in PREVIEW_KEYS if k in colours}, type="scheme",
                desc=f"caelestia scheme set -n {name} -f {flav} -m {mode}",
                default=None, has_default=False, file=tilde(str(txt)), group=name, preview="swatches",
                note="Ez az aktív séma." if (cur.get("name"), cur.get("flavour"), cur.get("mode")) == (name, flav, mode) else ""))
    names = ["dynamic"] + sorted(schemes)
    sj = where(state / "scheme.json")
    entries[:0] = [
        entry("scheme:name", "scheme.current", "Séma neve", cur.get("name", ""), type="enum", options=names,
              desc="dynamic = a tapétából generált Material You séma; a többi a CLI beépített sémája.",
              default="dynamic", file=sj, set=True, group="Aktuális séma"),
        entry("scheme:flavour", "scheme.current", "Flavour", cur.get("flavour", ""), type="enum",
              options=sorted(schemes.get(cur.get("name", ""), {}).keys()) or ["default"],
              desc="A séma változata (pl. catppuccin: mocha, latte). dynamic sémánál: default.",
              default="default", file=sj, set=True, group="Aktuális séma"),
        entry("scheme:mode", "scheme.current", "Mód", cur.get("mode", ""), type="enum", options=["dark", "light"],
              desc="Sötét vagy világos.", default="dark", file=sj, set=True, group="Aktuális séma"),
        entry("scheme:variant", "scheme.current", "Variáns", cur.get("variant", ""), type="enum", options=variants,
              desc="A dynamic séma Material You variánsa (mennyire színes, milyen hangsúlyos).",
              default="tonalspot", file=sj, set=True, group="Aktuális séma"),
        entry("scheme:palette", "scheme.current", "Aktuális paletta", cur.get("colours", {}), type="palette",
              desc="A jelenlegi séma összes színe. Ezekből készül a Hyprland, a shell, a terminál és a GTK/Qt téma.",
              default=None, has_default=False, file=sj, set=True, group="Aktuális séma", preview="palette"),
    ]
    wp = state / "wallpaper/path.txt"
    if wp.exists():
        entries.insert(5, entry("scheme:wallpaper", "scheme.current", "Tapéta", tilde(wp.read_text().strip()),
                                type="path", desc="A dynamic séma ebből a képből generálódik.",
                                default=None, has_default=False, file=where(wp), set=True, group="Aktuális séma",
                                preview="image"))

    # ── cli.json ──────────────────────────────────────────────────────────
    cli = profile_dir / "cli.json"
    try:
        cfg = json.loads(cli.read_text())
    except (OSError, ValueError):
        cfg = {}
    cf = where(cli.resolve())
    theme = cfg.get("theme", {})
    for k in enable_keys:
        entries.append(entry(f"cli:theme.{k}", "cli.theme", f"theme.{k}", theme.get(k, True), type="bool",
                             desc=THEME_TARGETS.get(k, "Téma-cél a CLI-ben.") + " Sémaváltáskor ezt is átszínezi.",
                             default=True, file=cf, set=k in theme, group="Mit színezzen át a sémaváltás"))
    for k, d in (("iconTheme", "Ikon-téma (GTK/Qt), ha nincs módonkénti."),
                 ("iconThemeDark", "Ikon-téma sötét módban."), ("iconThemeLight", "Ikon-téma világos módban."),
                 ("postHook", "Parancs a sémaváltás után (shell).")):
        entries.append(entry(f"cli:theme.{k}", "cli.theme", f"theme.{k}", theme.get(k, ""), type="string",
                             desc=d, default="", file=cf, set=k in theme, group="Ikonok és hookok"))
    wpc = cfg.get("wallpaper", {})
    entries.append(entry("cli:wallpaper.postHook", "cli.theme", "wallpaper.postHook", tilde(wpc.get("postHook", "")),
                         type="string", desc="Parancs tapétaváltás után (itt: az élő VS Code téma frissítése).",
                         default="", file=cf, set="postHook" in wpc, group="Ikonok és hookok"))
    for ws, apps in cfg.get("toggles", {}).items():
        for app, spec in apps.items():
            entries.append(entry(f"cli:toggles.{ws}.{app}", "cli.toggles", f"toggles.{ws}.{app}",
                                 {k: v for k, v in spec.items() if k != "_comment"}, type="object",
                                 desc=(spec.get("_comment", "") + f" (caelestia toggle {ws})").strip(),
                                 default=None, has_default=False, file=cf, set=True, group=f"special:{ws}"))
    rec = cfg.get("record", {})
    entries.append(entry("cli:record.extraArgs", "cli.toggles", "record.extraArgs", rec.get("extraArgs", []),
                         type="list", desc="A `caelestia record` extra argumentumai (gpu-screen-recorder).",
                         default=[], file=cf, set="extraArgs" in rec, group="Felvétel"))
    entries.append(entry("cli:resizer.rules", "cli.toggles", "resizer.rules",
                         cfg.get("resizer", {}).get("rules", []), type="list",
                         desc="A `caelestia resizer` ablak-átméretező szabályai.", default=[], file=cf,
                         set="resizer" in cfg, group="Átméretező"))
    n_builtin = sum(1 for e in entries if e["cat"] == "scheme.list")
    cats = [
        ("scheme.current", "Aktuális séma", "A most érvényes séma, variáns, tapéta és a teljes paletta."),
        ("scheme.list", "Beépített sémák",
         f"A caelestia CLI {n_builtin} beépített sémája színmintákkal. Jelöld, melyik tetszik "
         "(tartsd = tetszik, nem érdekel = nem kell)."),
        ("cli.theme", "CLI: téma-célok", "~/.config/caelestia/cli.json: mit színezzen át a sémaváltás."),
        ("cli.toggles", "CLI: toggle-ök, felvétel", "A `caelestia toggle` special workspace-ei, felvétel, átméretező."),
    ]
    info.update({"schemes": len(schemes), "builtin": n_builtin, "variants": variants})
    return {"entries": entries, "categories": cats, "info": info}
