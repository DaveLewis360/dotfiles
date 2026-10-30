"""Caelestia shell.json és shell-tokens.json → katalógus-bejegyzések.

A séma a caelestia.py-ból jön (C++ fejlécek + Nexus-feliratok), az élő érték
a profil shell.json-jából. A forrásrepót (~/Reference/my-caelestia-shell-bar)
csak olvassa.
"""
from __future__ import annotations

from pathlib import Path

import caelestia
from common import entry, tilde, where

SECTIONS = {
    "appearance": ("Megjelenés", "Méretezés, betűk, animáció-tempó, átlátszóság."),
    "general": ("Általános", "Alapértelmezett appok, tétlenség és zárolás, akkumulátor-figyelmeztetés, nyelv, logó."),
    "background": ("Háttér", "Tapéta, asztali óra, audio-vizualizáló."),
    "bar": ("Bar", "A sáv: elemei, munkaterület-jelző, tálca, óra, státuszikonok, popoutok."),
    "border": ("Képernyőkeret", "A képernyő szélén körbefutó keret, amiből a panelek kinyílnak."),
    "dashboard": ("Dashboard", "A felső dashboard: óra, média, teljesítmény, időjárás."),
    "launcher": ("Launcher", "Alkalmazásindító: találatok, kedvencek, akciók, fuzzy keresés."),
    "lock": ("Zárolóképernyő", "Ujjlenyomat, Howdy, értesítések a zárolóképernyőn."),
    "nexus": ("Nexus (beállítás-ablak)", "A shell saját beállítás-ablaka: tapéták, hálózatlista."),
    "notifs": ("Értesítés-popupok", "Az értesítések felugró ablakai: lejárat, teljes képernyő, csoportosítás."),
    "osd": ("OSD", "Hangerő- és fényerő-kijelzés."),
    "services": ("Szolgáltatások", "Időjárás, mértékegységek, óraformátum, GPU, hangerő-lépés, lejátszó, dalszöveg."),
    "session": ("Session-menü", "Kilépés, újraindítás, leállítás, hibernálás: ikonok és parancsok."),
    "sidebar": ("Értesítési panel (sidebar)", "Az értesítési panel (a forrásban modules/sidebar, NotifDock)."),
    "utilities": ("Quick panel (utilities)", "Kártyák (keep awake, felvétel, gyorskapcsolók), toastok, VPN."),
    "paths": ("Útvonalak", "Tapéta-könyvtár, dalszövegek, GIF-ek, képek."),
    "fork": ("Saját fork", "A DaveLewis360/shell fork saját kapcsolói (bar iránya, Num Lock jelző)."),
}
TOKEN_SECTIONS = {
    "appearance": ("Design tokenek: megjelenés", "Lekerekítés-, térköz-, padding-, betűméret-skála, animáció-görbék és -hosszak."),
    "sizes": ("Design tokenek: méretek", "Az egyes panelek és elemek pixelméretei."),
}

TYPE_MAP = {"bool": "bool", "int": "int", "qreal": "float", "QString": "string", "QStringList": "list",
            "QVariantMap": "object", "QVariant": "object", "QList<qreal>": "list", "list": "list"}


def _type(e: dict) -> str:
    t = e["type"]
    path = ".".join(e["path"])
    if t.startswith("enum:"):
        return "enum"
    if t == "QString" and (path.startswith("appearance.font.") and
                           (e["path"][-1] == "family" or e["path"][-1] in ("clock", "workspaces"))):
        return "font"
    if t == "QList<qreal>" and ".curves." in "." + path:
        return "curve-qml"
    return TYPE_MAP.get(t, "string")


def collect(repo: Path, profile_dir: Path, profiles_root: Path) -> dict:
    shell_json = profile_dir / "shell.json"
    tokens_json = Path.home() / ".config/caelestia/shell-tokens.json"
    others = {}
    for p in sorted(profiles_root.iterdir()):
        sj = p / "shell.json"
        if p.resolve() != profile_dir.resolve() and sj.is_file():
            others[p.name] = sj
    r = caelestia.collect(repo, shell_json, tokens_json, others)
    entries, cats = [], []
    used = set()
    for kind, sections, prefix in (("shell", SECTIONS, "shell"), ("tokens", TOKEN_SECTIONS, "tokens")):
        for e in r[kind]["entries"]:
            if e.get("node"):
                continue
            top = e["path"][0] if len(e["path"]) > 1 else "general"
            cat = f"{prefix}.{top}"
            used.add((cat, top, kind))
            nx = e.get("nexus", {})
            desc = " ".join(x for x in (e.get("comment", ""), nx.get("subtext", "")) if x).strip()
            typ = _type(e)
            opts = e.get("options")
            note = ""
            if e.get("others"):
                note = "Más profilban: " + "; ".join(
                    f"{k}: {v if not isinstance(v, (list, dict)) else '(eltér)'}" for k, v in e["others"].items())
            if kind == "tokens":
                file = tilde(str(tokens_json)) + ("" if tokens_json.exists() else " (nincs ilyen fájl: minden alapértéken)")
            else:
                file = where(shell_json)
            preview = {"font": "font", "curve-qml": "curve"}.get(typ, "")
            if kind == "tokens" and "animDurations" in e["path"]:
                preview = "duration"
            entries.append(entry(
                f"{kind}:" + ".".join(e["path"]), cat, ".".join(e["path"]), tilde(e["current"]),
                label=nx.get("label", ""), desc=desc, type=typ, default=tilde(e["default"]), options=opts,
                vmin=nx.get("from"), vmax=nx.get("to"), file=file, set=e["set"],
                group=".".join(e["path"][:-1]) if len(e["path"]) > 2 else ".".join(e["path"][:1]),
                note=note, preview=preview,
                extra={"elem": e.get("element"), "fields": e.get("fields")} if e["type"] == "list" and e.get("element") else None))
        for u in r[kind]["unknown"]:
            entries.append(entry(f"{kind}:" + ".".join(u["path"]), f"{prefix}.{u['path'][0]}", ".".join(u["path"]),
                                 tilde(u["value"]), note="A shell sémája nem ismeri ezt a kulcsot.",
                                 file=where(shell_json), set=True, has_default=False))
    for (cat, top, kind) in sorted(used):
        title, desc = (SECTIONS if kind == "shell" else TOKEN_SECTIONS).get(top, (top, ""))
        cats.append((cat, title, desc))
    order = list(SECTIONS) + list(TOKEN_SECTIONS)
    cats.sort(key=lambda c: (c[0].startswith("tokens"), order.index(c[0].split(".")[1]) if c[0].split(".")[1] in order else 99))
    return {"entries": entries, "categories": cats,
            "info": {"shell_json": where(shell_json), "repo": tilde(str(repo)), "nexus_labels": r["nexus_labels"],
                     "others": sorted(others)}}
