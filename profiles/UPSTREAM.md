# Beágyazott upstream klónok

Ezek a könyvtárak `.gitignore`-ban vannak, mert saját git történetük van.
Innen állíthatók vissza. Frissítve: 2026-07-29 12:55

| Könyvtár | Upstream | Branch | Rögzített commit | Dátum |
|---|---|---|---|---|
| `profiles/stable` | https://github.com/caelestia-dots/caelestia.git | main | `2e5598c627734cc87089d5ea570e80db558a04f7` | 2026-06-30 |
| `profiles/end4` | https://github.com/end-4/dots-hyprland.git | main | `c04b0bbc8143a2b2166c1f699f7583cb28ff78fe` | 2026-06-14 |
| `profiles/hyde` | https://github.com/HyDE-Project/HyDE.git | master | `a51460a7b1a822ee7194318b60a38850f711b923` | 2026-05-26 |
| `profiles/my-caelestia/shell` | https://github.com/caelestia-dots/caelestia.git | main | `fb9fa1ccbb5bba97dc25ac2402704b7bc5508dcc` | 2026-06-12 |

## Visszaállítás

```bash
# Példa (profiles/stable):
git clone https://github.com/caelestia-dots/caelestia.git ~/dotfiles/profiles/stable
git -C ~/dotfiles/profiles/stable checkout <commit a táblából>
```

## Megjegyzés a `caelestia-upstream` symlinkről

A `profiles/caelestia-upstream` egy symlink a `stable`-re, ezért a
`dotswitch list` kétszer mutatja ugyanazt a profilt. A symlink követve van,
de a `dotswitch` `stable` néven kezeli.


## A `hyde` profil extra lépései

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

### Amitől a HyDE nem indul el

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

### Visszaváltás a HyDE-ról

A HyDE a démonjait **systemd user unitokként** indítja
(`hyde-<XDG_SESSION_DESKTOP>-<név>.service` / `.scope`), ezért puszta
`pkill` nem elég — a `dotswitch` `stop_hyde_units()` függvénye állítja le
őket profilváltáskor.


## Hyprland config-formátum: `.lua` vs `.conf`

| Profil | Formátum | Miért |
|---|---|---|
| `my-caelestia` | `.lua` | a caelestia v2 Lua configot használ |
| `stable` | `.lua` | ugyanaz |
| `git` | `.lua` | ugyanaz |
| `end4` | `.lua` | az end-4 dots natívan Lua-alapú |
| **`hyde`** | **`.conf`** | a HyDE hyprlang-alapú, és a saját eszközei (`hyq`, `hyde-config`, `theme.switch.sh`) `.conf`-ot olvasnak/írnak |

**A Hyprland INDULÁSKOR választ parsert:** ha van `hyprland.lua`, azt tölti be
(Lua parser), különben `hyprland.conf`-ot (hyprlang). Menet közben **nem tud
váltani** a kettő között — a `hyprctl keyword` ilyenkor ezt mondja:

```
keyword can't work with non-legacy parsers. Use eval.
```

Ezért a `hyde` profilra (vagy onnan vissza) váltás **újralépést igényel a
sessionbe**. A `dotswitch` ezt észleli (`check_hypr_format`) és kiírja.
A symlinkek azonnal a helyükre kerülnek, csak a Hyprland config lép
érvénybe később.

### FONTOS: a HyDE profilra soha ne fusson a Lua-generátor

A `scripts/translate_hypr_lua.py` `.conf`-ból `.lua`-t generál. Ha ez lefut a
`hyde` profilra, a Hyprland onnantól a generált `hyprland.lua`-t tölti be a
HyDE `hyprland.conf`-ja HELYETT — és mivel a generátor nem kezeli a HyDE
`bindd` (leírásos bind) szintaxisát, **114 hibás keybind** keletkezik, a HyDE
core configja (waybar, env, téma) pedig egyáltalán nem töltődik be.

Pontosan ez tette használhatatlanná a HyDE profilt korábban: 48 generált
`.lua` fájl volt a `Configs/.config/hypr` alatt, `hyprctl configerrors` 118
hibát mutatott.

A `dotswitch` már védve van ellene:

```bash
if [[ -d "$hypr_dir" && "$current_shell_type" != "hyde" ]]; then
    python3 .../translate_hypr_lua.py "$hypr_dir"
fi
```

Ha mégis megjelennének, így lehet kitakarítani:

```bash
find ~/dotfiles/profiles/hyde/Configs/.config/hypr -name '*.lua' -delete
hyprctl reload
```

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
