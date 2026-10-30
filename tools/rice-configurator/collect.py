#!/usr/bin/env python3
"""rice-configurator: a paraméter-katalógus legenerálása.

    python3 collect.py              # az aktív dotswitch-profilból
    python3 collect.py --profile my-caelestia

Kimenet: data/catalog.js (window.RICE_CATALOG = {...}), amit az index.html
<script>-tel tölt be, így a webapp file://-ról is megy. Mellékterméke a
data/hypr-live.json: a futó Hyprland lekérdezett adatai, ha legközelebb
nem érhető el.

Csak olvas: az élő configot nem írja át, író hyprctl-parancsot nem futtat.
Kiírás előtt titok- és személyesadat-szűrés fut (a repó publikus).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "collectors"))

import hyprland  # noqa: E402
import privacy  # noqa: E402
import profiles  # noqa: E402
import schemes  # noqa: E402
import shell  # noqa: E402
import system  # noqa: E402
import terminal  # noqa: E402
from common import tilde  # noqa: E402

GROUPS = [
    ("hypr", "Hyprland"),
    ("shell", "Caelestia shell"),
    ("tokens", "Caelestia design tokenek"),
    ("scheme", "Színsémák"),
    ("cli", "Caelestia CLI"),
    ("term", "Terminál"),
    ("profiles", "dotswitch"),
    ("system", "Rendszertéma"),
]
APP_THEME_KEYS = ["background", "surfaceContainerLow", "surfaceContainer", "surfaceContainerHigh",
                  "surfaceContainerHighest", "onSurface", "onSurfaceVariant", "primary", "onPrimary",
                  "primaryContainer", "onPrimaryContainer", "secondaryContainer", "onSecondaryContainer",
                  "tertiary", "error", "outline", "outlineVariant"]


def main() -> int:
    repo = HERE.parents[1]
    state = Path.home() / ".local/state/dotfiles/active_profile"
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--profile", default=state.read_text().strip() if state.exists() else "my-caelestia-bar")
    ap.add_argument("--out", default=str(HERE / "data/catalog.js"))
    args = ap.parse_args()

    profile_dir = repo / "profiles" / args.profile
    meta = json.loads((profile_dir / ".meta.json").read_text())
    if meta.get("shell_type") != "caelestia":
        print(f"A(z) {args.profile} profil nem caelestia-alapú; a gyűjtők erre készültek.", file=sys.stderr)
        return 1
    shell_repo = Path(meta["quickshell_source"])
    hypr_dir = (profile_dir / "hypr").resolve()
    (HERE / "data").mkdir(exist_ok=True)

    parts = {
        "hypr": hyprland.collect(hypr_dir, HERE / "data/hypr-live.json"),
        "shell": shell.collect(shell_repo, profile_dir, repo / "profiles"),
        "schemes": schemes.collect(profile_dir),
        "terminal": terminal.collect(profile_dir),
        "profiles": profiles.collect(repo, args.profile),
        "system": system.collect(),
    }

    entries, cats = [], []
    for p in parts.values():
        entries.extend(tilde(e) for e in p["entries"])  # $HOME → ~ mindenhol
        cats.extend(p["categories"])
    # egyedi azonosítók
    seen: dict[str, int] = {}
    for e in entries:
        n = seen.get(e["id"], 0)
        seen[e["id"]] = n + 1
        if n:
            e["id"] = f'{e["id"]}#{n + 1}'
    counts: dict[str, int] = {}
    for e in entries:
        counts[e["cat"]] = counts.get(e["cat"], 0) + 1
    categories = []
    for cid, title, desc in cats:
        if counts.get(cid):
            categories.append({"id": cid, "title": title, "desc": desc, "group": cid.split(".")[0],
                               "count": counts[cid]})
    known_cats = {c["id"] for c in categories}
    orphan = sorted({e["cat"] for e in entries} - known_cats)
    if orphan:
        print("Kategória nélküli bejegyzések:", orphan, file=sys.stderr)
        return 1

    presets_src = json.loads((HERE / "presets.json").read_text())
    ids = {e["id"] for e in entries}
    presets, missing = {}, []
    for m in presets_src["marks"]:
        if m["id"] not in ids:
            missing.append(m["id"])
            continue
        presets[m["id"]] = {k: v for k, v in m.items() if k != "id"}
    if missing:
        print("A presets.json ismeretlen azonosítói:", missing, file=sys.stderr)
        return 1

    try:
        colours = json.loads((Path.home() / ".local/state/caelestia/scheme.json").read_text())["colours"]
    except (OSError, ValueError, KeyError):
        colours = {}
    body = json.dumps(entries, ensure_ascii=False, sort_keys=False)
    catalog = {
        "format": "rice-configurator/catalog-v1",
        "generated": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "hash": hashlib.sha256(body.encode()).hexdigest()[:12],
        "profile": args.profile,
        "sources": tilde({
            "hyprland": parts["hypr"]["info"], "shell": parts["shell"]["info"],
            "schemes": parts["schemes"]["info"], "terminal": parts["terminal"]["info"],
            "profiles": parts["profiles"]["info"], "system": parts["system"]["info"],
        }),
        "groups": [{"id": g, "title": t} for g, t in GROUPS if any(c["group"] == g for c in categories)],
        "categories": categories,
        "presets": presets,
        "presetSource": presets_src.get("source", ""),
        "theme": {k: colours[k] for k in APP_THEME_KEYS if k in colours},
        "fonts": parts["system"]["fonts"],
    }
    head = json.dumps(catalog, ensure_ascii=False, indent=1)
    lines = ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries)
    text = head[:-2] + ',\n "entries": [\n' + lines + "\n ]\n}"
    json.loads(text)  # érvényes JSON-e

    hits = privacy.scan(text)
    cache = HERE / "data/hypr-live.json"
    if cache.exists():
        hits += [(n, h, "hypr-live.json: " + c) for n, h, c in privacy.scan(cache.read_text())]
    if hits:
        print("A titok-/személyesadat-szűrő találatot jelzett, nem írok fájlt:", file=sys.stderr)
        for name, hit, ctx in hits[:40]:
            print(f"  [{name}] {hit!r}  …{ctx}…", file=sys.stderr)
        return 2

    out = Path(args.out)
    out.write_text("// Generálta: collect.py — ne szerkeszd kézzel.\nwindow.RICE_CATALOG = " + text + ";\n")
    print(f"{out}: {len(entries)} paraméter, {len(categories)} kategória, {len(presets)} előjelölés, "
          f"{out.stat().st_size // 1024} KB")
    print(f"Hyprland élő adat: {parts['hypr']['info']['live_source']}")
    for g, t in GROUPS:
        cs = [c for c in categories if c["group"] == g]
        if cs:
            print(f"  {t}: {sum(c['count'] for c in cs)}  (" + ", ".join(f"{c['title']} {c['count']}" for c in cs) + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
