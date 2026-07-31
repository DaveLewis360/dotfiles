# dotfiles — Hyprland / Quickshell rice-rendszer

Több teljes desktop-környezet ("rice") egy helyen, köztük egy paranccsal váltva.
Minden változtatás verziókövetett, tehát visszavonható.

Frissítve: 2026-07-29

---

## Váltás a rendszerek között

```bash
dotswitch mine       # Saját Caelestia fork      ← ez a fejlesztendő
dotswitch git        # Caelestia upstream (git main)
dotswitch end4       # end_4 Illogical Impulse

dotswitch status     # aktív profil + minden symlink
dotswitch list       # elérhető profilok
dotswitch active     # csak az aktív profil neve
```

Váltás után **logout/login** javasolt a teljes hatáshoz.

### Mit tesz egy váltás

1. Leállítja a futó shellt (quickshell / qs / caelestia shell / waybar / dunst / swaync)
2. Törli a QML cache-t (`~/.cache/quickshell/`)
3. Beállítja a `QML_IMPORT_PATH`-ot a profil `.meta.json`-ja szerint
4. Átirányítja a `~/.config/{hypr,fish,ghostty,foot,kitty,waybar,dunst,rofi,swaync}`
   symlinkeket a profilra (a `.meta.json` `configs` blokkja dönti el, melyiket)
5. Generálja a Hyprland `.lua` configokat a `.conf`-okból (`translate_hypr_lua.py`)
6. Beköti a `shell.json` / `cli.json`-t a `~/.config/caelestia/` alá
7. Ráteszi a közös beállításokat (`shared/common.json` → pl. `kb_layout=hu`)
8. Elindítja a shellt, újratölti a Hyprlandot, alkalmazza a színeket

Állapot: `~/.local/state/dotfiles/{active_profile,qml_import_path,switch.log}`

---

## Profilok

| Profil | Mi ez | Quickshell forrás |
|---|---|---|
| **`my-caelestia`** | **Saját fork** — horizontális bar, MiniDash, videó wallpaper | `~/Reference/my-caelestia-shell` |
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
│   ├── shell-sync-upstream   fork frissítése upstreamből (visszavonhatóan)
│   ├── shell-rebuild         a shell C++/QML pluginjeinek buildje
│   ├── dotclean              régi mentések visszavonható kitakarítása
│   ├── translate_hypr_lua.py .conf → .lua generálás
│   ├── apply_overlay.py      common.json ráolvasztása a profilra
│   └── update_css_vars.py    színek terminálokba
├── apps/ghostty/
└── zen-wrappers/
```

---

## Visszavonhatóság

Nincs btrfs/snapper ezen a gépen (ext4), ezért **a git a visszaállítás eszköze**.

| Mit | Hogyan |
|---|---|
| Bármely dotfiles-változtatás | `git -C ~/dotfiles log` → `git revert <commit>` |
| Kiinduló állapot (2026-07-29) | `git -C ~/dotfiles checkout baseline-20260729` |
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
