# Beágyazott upstream klónok és külső shell-források

Frissítve: 2026-10-30

## Beágyazott klónok (a `profiles/` alatt, `.gitignore`-ban)

Ezeknek saját git történetük van, ezért nincsenek a repóban. Innen állíthatók
vissza. A táblában a 2026-10-30-i HEAD áll.

| Könyvtár | Upstream | Branch | Commit | Dátum |
|---|---|---|---|---|
| `profiles/end4` | https://github.com/end-4/dots-hyprland.git | main | `2f0c8bf42b803f4d597572f2a014d4e78d7d9f26` | 2026-09-14 |

```bash
git clone https://github.com/end-4/dots-hyprland.git ~/dotfiles/profiles/end4
git -C ~/dotfiles/profiles/end4 checkout <commit a táblából>
```

Ami már nincs meg (a `2925bd6`, 2026-07-31 óta; a mentések a
`~/.local/share/dotfiles-trash` alatt, `dotclean --restore`):

| Volt | Mi lett vele |
|---|---|
| `profiles/stable` | törölve; ugyanazon a v2.2.0 tagen állt, mint a `git` vonal. A `dotswitch stable/caelestia/upstream` a `git` profilra visz |
| `profiles/caelestia-upstream` | a `stable`-re mutató symlink volt, törölve |
| `profiles/hyde` | a HyDE teljesen kikerült (lent archívként a régi leírás) |
| `profiles/my-caelestia/shell` | már nincs ilyen könyvtár; a saját fork a `~/Reference` alatt van (lent) |

## Külső Quickshell-források (`~/Reference`, nem a repó része)

A profil `.meta.json`-ja (`quickshell_source`, `qml_import_path`) hivatkozik
rájuk. Mindegyiknek saját repója van; a `build/qml` a `shell-rebuild` kimenete.

| Profil | Könyvtár | Remote | Branch (2026-10-30) |
|---|---|---|---|
| `my-caelestia` | `~/Reference/my-caelestia-shell` | `DaveLewis360/shell` | `main` |
| `my-caelestia-bar` | `~/Reference/my-caelestia-shell-bar` | `DaveLewis360/shell` | `feat/chat-sidebar` (a `bar-toggle`-re épül) |
| `my-caelestia-next` | `~/Reference/my-caelestia-shell-next` | `DaveLewis360/shell` | `next` (BROKEN) |
| `git` | `~/Reference/caelestia-shell-git` | `caelestia-dots/shell` | `main` |

## Hyprland config-formátum: `.lua` vs `.conf`

**A Hyprland 0.57 óta csak `.lua` configot tud betölteni.** A 0.57.0 kivette
a legacy hyprlang parsert ([hyprwm/Hyprland#15539](https://github.com/hyprwm/Hyprland/pull/15539)),
és vele a `hyprctl keyword` parancsot is. Ezen a gépen 2026-10-28 óta 0.57.0 fut.

| Profil | Amit a Hyprland betölt | A szerkesztett forrás |
|---|---|---|
| `my-caelestia`, `my-caelestia-bar`, `my-caelestia-next` (közös `hypr`) | `hyprland.lua` | a `.lua` (`"hypr_source": "lua"`); a `.conf` elavult, a fordító nem fut rá; az overlay a `hardware/overlay.lua`-ba ír |
| `git` | `hyprland.lua` | a `.lua` (Lua-natív, nincs `.conf`) |
| `end4` | `hyprland.lua` | a `.lua` (az upstream Lua-natív) |

- A `scheme/current.lua`-t a caelestia CLI írja (háttér- vagy sémaváltáskor).
  A fordító a `scheme/` alatti `.lua`-t ezért nem írja felül, csak akkor
  generálja, ha még nincs meg (`5a02521`). Előtte minden `dotswitch` a júniusi
  `scheme/current.conf` színeit írta vissza.
- A `dotswitch` `running_hypr_format()` függvénye 0.57-től mindig `lua`-t mond
  (`d400276`). Előtte a `hyprctl keyword` próba miatt tévesen „újralépés kell”
  riasztást adott.
- A `"hypr_source": "lua"` profiloknál a `dotswitch` nem futtatja a fordítót.
  A váltás előtti száraz ellenőrzés: `scripts/lua-source-dryrun [profil]`.
- Az `apply_overlay.py` lua-kimenete az ablakszabályokat `hl.window_rule()`
  hívásként írja. A korábbi `hl.config({ windowrule = { "..." } })` formát a
  0.57 hiba nélkül elfogadja, de nem érvényesíti: a `windowrule` nem ismert
  config-kulcs (`windowrule = 5` → „unknown config key”), a táblás alakra
  pedig egy kitalált szabálynévvel is „config ok” jön. A `git` profil közös
  ablakszabályai így eddig hatástalanok voltak.

## Archív: HyDE (2026-07-31 óta nincs, `2925bd6`)

A lenti leírás a régi `hyde` profilé. Csak arra az esetre maradt meg, ha a
HyDE-t valaha újra be kellene hozni. A Hyprland 0.57 a HyDE `.conf`-alapú
configját már nem tudná betölteni.

### A `hyde` profil extra lépései

A HyDE nem csak configokból áll: van futásidejű adata és letöltött témái is.
Ha a `profiles/hyde` klónt újra kell hozni, ezek is kellenek:

```bash
git clone https://github.com/HyDE-Project/HyDE.git ~/dotfiles/profiles/hyde
git -C ~/dotfiles/profiles/hyde checkout <commit a fenti táblából>

# A letöltött témák symlinkje (a 310 MB nem a repó része)
ln -sfn ~/.local/share/hyde-themes \
        ~/dotfiles/profiles/hyde/Configs/.config/hyde/themes

# Hogy az upstream klón git-státusza tiszta maradjon
cat >> ~/dotfiles/profiles/hyde/.git/info/exclude <<'EOF'
.meta.json
*.lua
Configs/.config/hyde/themes
EOF
```

A `.meta.json`-t a `~/dotfiles`-ból kell visszatenni (az a mi fájlunk, nem
az upstreamé): `git -C ~/dotfiles checkout -- profiles/hyde/.meta.json`
— illetve mivel a `profiles/hyde` gitignore-olt, a `.meta.json` sem követett,
ezért a tartalmát a `profiles/UPSTREAM.md` mellett érdemes külön megőrizni.

#### Amitől a HyDE nem indul el

Két hiba, ami korábban működésképtelenné tette:

1. **A fallback `source` ki volt kommentelve.** A
   `Configs/.config/hypr/hyprland.conf` mindössze 5 érdemi sort tartalmaz;
   minden lényeg (`env`, `variables`, `defaults`, `windowrules`, `dynamic`,
   **`startup`** ← ez indítja a waybart, `finale`) a
   `source = $HOME/.local/share/hyde/hyprland.conf` sor mögött van. Mivel a
   `HYPRLAND_CONFIG` környezeti változó nincs beállítva, e nélkül a sor nélkül
   a Hyprland gyakorlatilag üres configot kap.

2. **A témák nem voltak a helyükön.** A HyDE a
   `$HYDE_CONFIG_HOME/themes` = `~/.config/hyde/themes` alatt keresi őket
   (`globalcontrol.sh:196`). A 12 letöltött téma egy régi
   `hyde.bak-dotswitch-*` mentésben ragadt, a profil `hyde` könyvtárában
   nem volt `themes/`, így a téma-rendszernek nem volt mit alkalmaznia.

#### Visszaváltás a HyDE-ról

A HyDE a démonjait **systemd user unitokként** indítja
(`hyde-<XDG_SESSION_DESKTOP>-<név>.service` / `.scope`), ezért puszta
`pkill` nem elég — a `dotswitch` `stop_hyde_units()` függvénye állítja le
őket profilváltáskor.


### A HyDE profilra nem futhatott a Lua-generátor

A `translate_hypr_lua.py` nem kezelte a HyDE `bindd` szintaxisát: egy futás
48 generált `.lua`-t és 118 config-hibát hagyott maga után. A `dotswitch`
ezért a HyDE-ra nem futtatta. A guard a HyDE-val együtt kikerült.

### A HyDE upstream `/home/khing` hibája

Az upstream HyDE repóban 4 futásidőben olvasott fájl a maintainer home
útvonalát tartalmazza bedrótozva (ezek auto-generált fájlok, amiket a
fejlesztő gépén generálva commitoltak):

| Fájl | előfordulás |
|---|---|
| `Configs/.config/waybar/style.css` | 2 |
| `Configs/.config/waybar/includes/includes.json` | 89 |
| `Configs/.config/dunst/dunstrc` | 6 |
| `Configs/.config/hyde/wallbash/scripts/cava.sh` | 1 |

Ettől a waybar **el sem indul**:

```
style.css:16: Failed to import: /home/khing/.local/share/waybar/styles/defaults.css
hyde-Hyprland-bar.service: Failed with result 'exit-code'
```

Javítás újraklónozás után:

```bash
cd ~/dotfiles/profiles/hyde
for f in Configs/.config/waybar/style.css \
         Configs/.config/waybar/includes/includes.json \
         Configs/.config/dunst/dunstrc \
         Configs/.config/hyde/wallbash/scripts/cava.sh; do
    sed -i "s|/home/khing|$HOME|g" "$f"
    git update-index --skip-worktree "$f"   # a klón maradjon tiszta
done
```
