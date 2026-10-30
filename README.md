# dotfiles — Hyprland / Quickshell rice-rendszer

Több teljes desktop-környezet ("rice") egy helyen, köztük egy paranccsal váltva.
A saját tartalom verziókövetett, tehát visszavonható. A generált fájlok
(színséma, overlay, terminál-téma) nem, ezek listája a `.gitignore`-ban van.

Frissítve: 2026-10-30

---

## Váltás a rendszerek között

```bash
dotswitch mine       # Saját Caelestia fork      ← a jelenlegi, megszokott
dotswitch bar        # Upstream Caelestia + egyetlen kapcsoló: felső vagy bal bar
dotswitch next       # BROKEN — kísérleti újraépítés, csak megerősítéssel (--force)
dotswitch git        # Caelestia upstream (git main)
dotswitch end4       # end_4 Illogical Impulse

dotswitch status     # aktív profil + minden symlink
dotswitch list       # elérhető profilok
dotswitch active     # csak az aktív profil neve
```

Váltás után **logout/login** javasolt a teljes hatáshoz.

### Mit tesz egy váltás

0. BROKEN-ként jelölt profilnál (`.meta.json` `"status": "broken"`) előbb
   megerősítést kér; `--force`-szal kérdés nélkül vált
1. Leállítja a futó shellt (quickshell / qs / caelestia shell / waybar / dunst / swaync)
2. Törli a QML cache-t (`~/.cache/quickshell/`)
3. Beállítja a `QML_IMPORT_PATH`-ot a profil `.meta.json`-ja szerint
4. Átirányítja a `~/.config/{hypr,fish,ghostty,foot,kitty,waybar,dunst,rofi,swaync}`
   symlinkeket a profilra (a `.meta.json` `configs` blokkja dönti el, melyiket)
5. Ráteszi a közös beállításokat (`shared/common.json` → pl. `kb_layout=hu,us`)
   a profil overlay-fájljára, és beköti az `apps/` univerzális app-configjait
6. A `.conf`-forrású profiloknál generálja a Hyprland `.lua` configokat a
   `.conf`-okból (`translate_hypr_lua.py`; a `scheme/` alatti `.lua`-t nem írja
   felül). A `"hypr_source": "lua"` profiloknál ez kimarad (lásd lent)
7. Beköti a `shell.json` / `cli.json`-t a `~/.config/caelestia/` alá
8. Elindítja a shellt, újratölti a Hyprlandot, alkalmazza a színeket

Állapot: `~/.local/state/dotfiles/{active_profile,qml_import_path,switch.log}`

### Hyprland 0.57: `.lua` és `.conf`

A Hyprland 0.57 óta (ezen a gépen 2026-10-28 óta) csak a `hyprland.lua`-t
tudja betölteni, a `.conf` parser kikerült belőle. A `my-caelestia*` profilok
közös `hypr` könyvtárában ezért **a `.lua` a szerkesztett forrás**
(`.meta.json`: `"hypr_source": "lua"`). A `dotswitch` ezekre a profilokra nem
futtatja a `.conf` → `.lua` fordítót, a közös beállításokat pedig közvetlenül a
`hardware/overlay.lua`-ba írja (`"overlay_format": "lua"`).

- A `.conf` fájlok még megvannak, de elavultak: a Hyprland és a `dotswitch` sem
  olvassa őket. Pár nap használat után kerülnek ki a gitből.
- A színsémát (`hypr/scheme/current.lua`) a caelestia CLI írja háttér- vagy
  sémaváltáskor.
- A fordító (`translate_hypr_lua.py`) a `hypr_source` nélküli profiloknál fut
  tovább (pl. `end4`).
- Váltás előtt és egy `.conf`/`.lua` módosítás után: `scripts/lua-source-dryrun`
  (semmit nem ír; összeveti a régi és az új utat, és lefuttatja a
  `Hyprland --verify-config`-ot).
- Részletek és a profilonkénti táblázat:
  [`profiles/UPSTREAM.md`](profiles/UPSTREAM.md#hyprland-config-formátum-lua-vs-conf).

---

## Profilok

| Profil | Mi ez | Quickshell forrás |
|---|---|---|
| **`my-caelestia`** | **Saját fork** — horizontális bar, MiniDash, videó wallpaper | `~/Reference/my-caelestia-shell` |
| `my-caelestia-bar` | **Ez az aktív (2026-10-30).** Upstream Caelestia + egy kapcsoló: felső vagy bal bar (Nexus → Panels → Taskbar → Position, vagy `barmode`). A hypr/fish/terminál configok symlinkek a `my-caelestia`-ra, saját csak a `shell.json` | `~/Reference/my-caelestia-shell-bar` (a `bar-toggle` ágra épül) |
| `my-caelestia-next` | **BROKEN.** Ugyanez újraépítve a v2.5.0-ra (patch stack, natív `fork` config). A hypr/fish/terminál configok symlinkek a `my-caelestia`-ra, saját csak a `shell.json` | `~/Reference/my-caelestia-shell-next` (branch `next`) |
| `git` | Caelestia upstream (git main) — összehasonlítási alap | `~/Reference/caelestia-shell-git` |
| `end4` | end-4/dots-hyprland | `profiles/end4/dots/.config/quickshell/ii` |

A beágyazott upstream klónok nincsenek ebben a repóban (saját git történetük van) —
lásd [`profiles/UPSTREAM.md`](profiles/UPSTREAM.md) a pontos commitokkal.

---

## A saját fork fejlesztése

A fork: `~/Reference/my-caelestia-shell` → `git@github.com:DaveLewis360/shell.git`
Upstream: `https://github.com/caelestia-dots/shell.git`

Mit módosít a fork és melyik változtatás mennyire konfliktusveszélyes:
[`~/Reference/my-caelestia-shell/CUSTOMIZATIONS.md`](../Reference/my-caelestia-shell/CUSTOMIZATIONS.md)

### Upstream frissítés beolvasztása

```bash
shell-sync-upstream --dry-run    # mi jönne + konfliktus-előrejelzés
shell-sync-upstream              # merge (előtte automatikus pre-merge tag)
shell-rebuild                    # C++/QML pluginek újraépítése
dotswitch mine                   # aktiválás és teszt
```

Ha valami félresikerült:

```bash
shell-sync-upstream --abort   # félbehagyott merge eldobása
shell-sync-upstream --undo    # befejezett merge visszavonása
shell-sync-upstream --list    # összes visszaállítási pont
```

### Miért konfliktusos a merge

Az upstream a `63da6361` committal (2025-05-27) **szándékosan vertikális-only**
lett, és nincs bar-orientáció opció a `shell.json` sémában. A fork visszahozza a
horizontális bart 18 fájlban (`Column`→`Row`, `y`↔`x`,
`implicitWidth`↔`implicitHeight`) — ez tartós divergencia.

Ezért van bekapcsolva a **`rerere`**: minden konfliktus-feloldást megjegyez, és a
következő merge-nél automatikusan alkalmazza. Egy konfliktust elég egyszer megoldani.

---

## Könyvtárszerkezet

```
~/dotfiles/
├── profiles/
│   ├── my-caelestia/     SAJÁT — hypr, fish, foot, ghostty, shell.json, cli.json
│   ├── my-caelestia-bar/ upstream + bar-kapcsoló: saját shell.json, a többi symlink
│   ├── my-caelestia-next/ BROKEN — kísérleti újraépítés
│   ├── git/              csak configok, a shellt a Reference-ből veszi
│   ├── end4/             upstream klón (gitignore)
│   └── UPSTREAM.md       a klónok manifestje commit SHA-kkal
├── shared/               minden profilra érvényes
│   ├── common.json       kb_layout stb. — EGY helyen szerkeszd
│   ├── gitconfig         = ~/.gitconfig
│   ├── gitconfig.local   git identitás
│   └── gitignore, vimrc, Xresources, irbrc, gemrc
├── scripts/
│   ├── dotswitch             profilváltás
│   ├── barmode               bar felül vagy balra (a profil .meta.json barmode mezője szerint)
│   ├── shell-restart         a shell újraindítása / --start: indítás, ha nem fut
│   ├── shell-sync-upstream   fork frissítése upstreamből (visszavonhatóan)
│   ├── shell-rebuild         a shell C++/QML pluginjeinek buildje
│   ├── dotclean              régi mentések visszavonható kitakarítása
│   ├── translate_hypr_lua.py .conf → .lua generálás (csak .conf-forrású profilnál)
│   ├── lua-source-dryrun     száraz ellenőrzés: régi és új út, verify-config
│   ├── apply_overlay.py      common.json ráolvasztása a profilra
│   ├── update_css_vars.py    színek terminálokba és VS Code-ba
│   └── ghostty               Ghostty indító a blur-shimmel
├── apps/                 rice-független app-configok (minden profilban ugyanaz)
│   ├── btop/btop.conf
│   └── ghostty/          config + blur-shim.c
└── zen-wrappers/
```

---

## Visszavonhatóság

Nincs btrfs/snapper ezen a gépen (ext4), ezért **a git a visszaállítás eszköze**.

| Mit | Hogyan |
|---|---|
| Bármely dotfiles-változtatás | `git -C ~/dotfiles log` → `git revert <commit>` |
| Kiinduló állapot (2026-07-29) | `git -C ~/dotfiles checkout baseline-20260729` |
| A 07-31 és 10-29 közötti, addig commitolatlan munka | a `wip/pre-migration-20261025` ág (7 tematikus commit, a GitHubon is) |
| Fork merge visszavonása | `shell-sync-upstream --undo` |
| Fork korábbi állapota | `shell-sync-upstream --list` → `git reset --hard refs/backup/<név>` |
| Archivált fork-branchek | `shell-sync-upstream --list` → `git branch <név> refs/backup/archive/<név>` |
| Kitakarított mentések | `dotclean --list` → `dotclean --restore <ts>` |

A shell-repók visszaállítási pontjai a `refs/backup/` névtérben vannak, **nem
tagként** — mert a `CMakeLists.txt` a verziót a `git describe --tags`-ból veszi,
és egy saját tag eltörné a buildet.

Teljes visszaállítási pont a nagy átalakítás előttről:
`~/dotfiles-restore-point-20260729_124849/` (symlink-állapot, HEAD-ek, patchek,
teljes `dotfiles-tree.tar.gz`).

---

## Régi mentések takarítása

```bash
dotclean              # jelentés: mi mennyit foglal és miért felesleges
dotclean --stage 1    # bizonyítottan redundáns (~27 GB) → kuka
dotclean --stage 2    # átnézendő (~698 MB) → kuka
dotclean --purge <ts> # végleges törlés (csak ez szabadít fel helyet)
```

A `--stage` nem töröl, csak áthelyez, tehát `--restore`-ral visszavonható.
