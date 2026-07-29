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
