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
