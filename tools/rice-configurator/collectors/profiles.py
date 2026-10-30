"""dotswitch-profilok (.meta.json) és a közös réteg (shared/common.json)."""
from __future__ import annotations

import json
from pathlib import Path

from common import entry, tilde, where

ALIASES = {"my-caelestia": "mine", "my-caelestia-bar": "bar", "my-caelestia-next": "next",
           "git": "git (rolling, stable, caelestia, upstream)", "end4": "end4"}


def collect(repo: Path, active: str) -> dict:
    entries = []
    profiles = sorted(p for p in (repo / "profiles").iterdir() if (p / ".meta.json").is_file())
    names = [p.name for p in profiles]
    state = Path.home() / ".local/state/dotfiles/active_profile"
    entries.append(entry("dotswitch:active", "profiles.list", "Aktív profil", active, type="enum",
                         options=names, desc="A `dotswitch <alias>` váltja. A váltás újraírja a ~/.config symlinkjeit, "
                                             "ráteszi a közös réteget és újraindítja a shellt.",
                         default=None, has_default=False, file=where(state), set=True, group="Profilválasztás"))
    for p in profiles:
        meta = json.loads((p / ".meta.json").read_text())
        desc = meta.get("description", "")
        broken = "[BROKEN]" in desc or meta.get("status") == "broken"
        val = {
            "név": meta.get("name", ""),
            "alias": ALIASES.get(p.name, p.name),
            "shell": meta.get("shell_type", ""),
            "shell-forrás": tilde(meta.get("quickshell_source", "")),
            "overlay": f'{meta.get("overlay_format", "")} → {meta.get("overlay_target", "")}',
            "configok": sorted(k for k, v in meta.get("configs", {}).items() if v),
        }
        if meta.get("hypr_source"):
            val["hypr-forrás"] = meta["hypr_source"]
        note = []
        if p.name == active:
            note.append("Ez az aktív profil.")
        if broken:
            note.append("BROKEN jelölésű: a dotswitch megerősítést kér.")
        links = sorted(x.name + " → " + str(Path(x.readlink())) for x in p.iterdir() if x.is_symlink())
        if links:
            note.append("Symlinkek: " + ", ".join(links) + ".")
        entries.append(entry(f"dotswitch:profile.{p.name}", "profiles.list", p.name, val, type="object",
                             desc=desc, default=None, has_default=False, file=where(p / ".meta.json"),
                             set=True, group="Profilok", note=" ".join(note)))

    common = repo / "shared/common.json"
    cj = json.loads(common.read_text())
    cf = where(common)
    for k, v in cj.get("input", {}).items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if not k2.startswith("_"):
                    entries.append(entry(f"common:input.{k}.{k2}", "profiles.common", f"input.{k}.{k2}", v2,
                                         desc="Minden profilra ráteszi a dotswitch (felülírja a profil saját értékét).",
                                         default=None, has_default=False, file=cf, set=True, group="Bevitel"))
        else:
            entries.append(entry(f"common:input.{k}", "profiles.common", f"input.{k}", v,
                                 desc="Minden profilra ráteszi a dotswitch. Üres string: kimarad az overlayből.",
                                 default=None, has_default=False, file=cf, set=True, group="Bevitel"))
    for b in cj.get("binds", []):
        entries.append(entry(f"common:bind.{b['keys']}", "profiles.common", b["keys"],
                             f'{b["dispatcher"]} {b.get("args", "")}'.strip(), type="bind",
                             label=b.get("description", ""), desc=b.get("_comment", ""), default=None,
                             has_default=False, file=cf, set=True, group="Közös bindok", preview="keys"))
    for a in cj.get("actions", []):
        entries.append(entry(f"common:action.{a['keys']}", "profiles.common", a["keys"],
                             f'akció: {a["action"]}' + (f' (flags: {a["flags"]})' if a.get("flags") else ""),
                             type="bind", label=a.get("description", ""), desc=a.get("_comment", ""),
                             default=None, has_default=False, file=cf, set=True,
                             group="Közös akciók (profilonként más megvalósítás)", preview="keys"))
    for r in cj.get("windowrules", []):
        m = ", ".join(f"{k}: {v}" for k, v in r.get("match", {}).items())
        entries.append(entry(f"common:wrule.{m}|{r['rule']}", "profiles.common", m, r["rule"], type="rule",
                             desc=r.get("_comment", ""), default=None, has_default=False, file=cf, set=True,
                             group="Közös ablakszabályok"))
    for ws, apps in cj.get("cliToggles", {}).items():
        if ws.startswith("_"):
            continue
        for app, spec in apps.items():
            entries.append(entry(f"common:cliToggle.{ws}.{app}", "profiles.common", f"cliToggles.{ws}.{app}",
                                 {k: v for k, v in spec.items() if not k.startswith("_")}, type="object",
                                 desc=spec.get("_comment", ""), default=None, has_default=False, file=cf,
                                 set=True, group="Közös toggle-ök (cli.json-ba olvad)"))
    return {"entries": entries,
            "categories": [
                ("profiles.list", "Profilok", "A dotswitch profiljai. Jelöld, melyik kell még (tartsd / nem érdekel)."),
                ("profiles.common", "Közös réteg (common.json)",
                 "Rice-független beállítások: minden profilra ráteszi a dotswitch, a profil formátumában."),
            ],
            "info": {"profiles": names, "active": active}}
