# rice-configurator

Egy helyen mutatja a Hyprland + Caelestia (Quickshell) rendszer összes személyre szabható paraméterét: a mostani értéket, az alapértéket, a lehetséges értékeket, egy rövid leírást és a fájlt, ahol beállítod. Minden paraméternél jelölhető: **tartsd**, **változtasd** (javasolt értékkel) vagy **nem érdekel**, és írható hozzá megjegyzés. A végén az egész egy JSON-fájlba exportálható.

## Megnyitás

Statikus oldal, szerver nem kell:

```
xdg-open ~/dotfiles/tools/rice-configurator/index.html
```

vagy a böngészőben: `file:///home/<felhasználó>/dotfiles/tools/rice-configurator/index.html`.

A jelölések a böngésző helyi tárolójában (localStorage) automatikusan mentődnek. Az **Export JSON** letölti őket (`rice-preferences-ÉÉÉÉHHNN-ÓÓPP.json`), az **Import** visszatölti.

## Újragenerálás

```
python3 ~/dotfiles/tools/rice-configurator/collect.py            # az aktív dotswitch-profilból
python3 ~/dotfiles/tools/rice-configurator/collect.py --profile my-caelestia
```

Kimenet: `data/catalog.js` (ezt tölti be az oldal) és `data/hypr-live.json` (a futó Hyprland lekérdezett adatai, tartaléknak arra az esetre, ha legközelebb nem érhető el). Kell hozzá: `python3`, `lua`, és lehetőleg egy futó Hyprland.

A gyűjtők **csak olvasnak**. Az élő configot nem írják át, és író `hyprctl`-parancsot (keyword, reload, dispatch) nem futtatnak; csak a `hyprctl -i 0 descriptions|animations|version -j` lekérdezéseket. A Hyprland `.lua` configját a `collectors/hl_dump.lua` egy mock `hl` táblával olvassa be, végrehajtás nélkül.

Kiírás előtt titok- és személyesadat-szűrő fut (`collectors/privacy.py`): home-útvonal, IP-cím, e-mail, token, kulcs, MAC-cím. Találat esetén nem ír fájlt. A `$HOME` minden értékben `~`-ra cserélődik. (A repó publikus.)

## Források

| Terület | Forrás | Gyűjtő |
|---|---|---|
| Hyprland opciók | `hyprctl descriptions` (leírás, alapérték, élő érték, határok) + a profil `.lua` configja | `hyprland.py`, `hl_dump.lua` |
| Animációk, görbék | `hl.curve`, `hl.animation` + `hyprctl animations` | `hyprland.py` |
| Bindok, szabályok, autostart, env, monitorok, változók | a `.lua` config `hl.*` hívásai, fájl:sorral | `hyprland.py` |
| Caelestia shell.json, shell-tokens.json | a shell C++ config-fejlécei (`plugin/src/Caelestia/Config/*.hpp`), a Nexus beállítás-oldalak feliratai, a profil `shell.json`-ja | `caelestia.py`, `shell.py` |
| Színsémák | a caelestia CLI beépített sémái, `~/.local/state/caelestia/scheme.json` | `schemes.py` |
| CLI (cli.json) | a CLI `theme.py` kapcsolói + a profil `cli.json`-ja | `schemes.py` |
| Ghostty | `ghostty +show-config --default --docs` + `apps/ghostty/config` | `terminal.py` |
| foot | `/etc/xdg/foot/foot.ini` + a profil `foot.ini`-je | `terminal.py` |
| dotswitch | `profiles/*/.meta.json`, `shared/common.json` | `profiles.py` |
| GTK, Qt, ikonok, kurzor, betűk | `gsettings get`, `qt6ct.conf`, téma-könyvtárak, `fc-list` | `system.py` |

A leírások a forrásból jönnek, ezért a Hyprland, a Ghostty és a shell Nexus-feliratai angolok; a kategóriák és a saját kiegészítések magyarok.

## Előjelölés

A `presets.json` tartja, amit Dave preferenciáiról már tudunk. A `collect.py` ellenőrzi, hogy minden azonosító létezik, és beteszi a katalógusba. Az oldal első megnyitáskor ezekkel jelöl elő (az „előjelölve” címke); Dave bármelyiket átírhatja.

## Export-formátum (`rice-configurator/export-v1`)

```json
{
  "format": "rice-configurator/export-v1",
  "exported": "2026-10-30T21:00:00.000Z",
  "catalog": { "generated": "…", "hash": "…", "profile": "my-caelestia-bar", "total": 1753 },
  "counts": { "keep": 3, "change": 4, "ignore": 5, "commented": 1, "unmarked": 1741 },
  "notes": "általános megjegyzés",
  "items": [
    {
      "id": "hypr:decoration.rounding",
      "source": "hypr",
      "category": "Hyprland › Díszítés",
      "key": "decoration.rounding",
      "file": "~/dotfiles/profiles/my-caelestia/hypr/appearance/theme.lua:11",
      "current": 10,
      "default": 0,
      "decision": "change",
      "proposed": 14,
      "comment": "…",
      "preset": true
    }
  ]
}
```

- Az `items` csak a jelölt vagy megjegyzéssel ellátott paramétereket tartalmazza.
- `decision`: `keep` | `change` | `ignore` | `null` (csak megjegyzés).
- `proposed` csak `change` esetén van; a típushoz igazítva (szám, `true`/`false`, JSON-lista), ha értelmezhető, különben szöveg.
- `preset: true`: az előjelölésen Dave nem változtatott.
- Az `id` előtagja a forrás: `hypr`, `hypr-curve`, `hypr-anim`, `hypr-bind`, `hypr-window_rule`, `hypr-layer_rule`, `hypr-workspace_rule`, `hypr-exec`, `hypr-gesture`, `hypr-env`, `hypr-monitor`, `hypr-device`, `hypr-var`, `shell`, `tokens`, `scheme`, `scheme-builtin`, `cli`, `ghostty`, `foot`, `dotswitch`, `common`, `gsettings`, `qt6ct`.

## Fájlok

```
index.html, app.css, app.js   a webapp (függőség nélkül, hálózatot nem használ)
collect.py                    a katalógus legenerálása
collectors/                   a gyűjtők (csak olvasnak)
presets.json                  előjelölések
data/catalog.js               generált katalógus (commitolva, hogy azonnal megnyitható legyen)
data/hypr-live.json           a legutóbbi hyprctl-lekérdezés (tartalék)
```
