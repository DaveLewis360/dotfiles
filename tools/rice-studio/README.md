# rice-studio

Interaktív Hyprland dotfile-készítő **élő előnézettel**. Nem száraz paraméter-lista:
a bal oldalon egy szimulált Hyprland-munkaterület (tapéta, bar, ablakok, paletta,
betűminta, animáció), a jobb oldalon a vezérlők. Amit állítasz, az azonnal látszik.
**Hyprland-általános** — nem caelestia-kötött.

## Megnyitás

Statikus oldal, szerver nem kell:

```
xdg-open ~/dotfiles/tools/rice-studio/index.html
```

vagy a böngészőben: `file:///home/<felhasználó>/dotfiles/tools/rice-studio/index.html`.

Függőség nincs, hálózatot nem használ, és **semmit nem ír a gépre** a letöltésen kívül.
Az élő Hyprland-configot **nem** érinti — csak exportál (letöltés vagy vágólap).

## Mit lehet állítani

A legfontosabb rice-paraméterekre szűkítve, hat fülön:

| Fül | Paraméterek |
|---|---|
| **Téma & szín** | háttér, felület, szöveg, kiemelés + 3 másodlagos szín, séma-mód (megjegyzés) |
| **Elrendezés** | belső/külső rés (gaps), keretvastagság, csempézés (dwindle/master) |
| **Díszítés** | lekerekítés, aktív/inaktív átlátszatlanság, blur (be/ki, méret, menetek), árnyék |
| **Animáció** | be/ki, sebesség (Hyprland-egység), bezier-görbe (vizuális előnézettel) |
| **Betűtípus** | felület betűje, monospace betű |
| **Háttér** | tömör szín / gradiens (2 szín + szög), opcionális képútvonal |

A **Stílus…** gombbal hat kiindulási irány tölthető be (Tokyo Night, Gruvbox, Nord,
Cyber neon, Papír, Brutalist) — mindegyik csak kiindulópont, utána szabadon hangolod.

## Export

Az **Export…** gomb három formátumba ír:

- **Hyprland `.conf`** — valós kulcsokkal (`decoration { rounding = 14 }`, `blur { size = 12 }`,
  gradiens `col.active_border`, `animations { bezier = … }`).
- **Hyprland `.lua`** — a `hyprlang-lua` plugin `hl.config{…}` / `hl.bezier{…}` / `hl.animation(…)` API-jával.
- **JSON** — géppel olvasható összegzés (érték + alapérték + Hyprland-kulcs paraméterenként).

A "csak az alapértéktől eltérők" kapcsolóval a kimenet szűkíthető arra, amit tényleg
megváltoztattál. A betű, a séma-mód és a paletta megjegyzésként is bekerül (ezeket a
téma-/betű-eszközöd állítja, nem a Hyprland). Képútvonal esetén egy `exec-once` sor
készül (swww/hyprpaper).

> Az export **nem** másolja a fájlt a helyére. A `.conf`/`.lua` blokkot te illeszted
> be a saját configodba (pl. egy `appearance` részfájlba), így marad feletted a kontroll.

## Fájlok

```
index.html    a stúdió váza (előnézet + panel + dialógusok)
studio.css    a téma és az élő-előnézet (a --r-* CSS-változókon át vezérelve)
studio.js     a paraméter-modell, a vezérlők, az élő frissítés és az export
```

A paraméter-modell a `studio.js` tetején, a `def(...)` hívásokban van; új paramétert
egy sorral lehet hozzáadni (név, típus, alapérték, Hyprland-kulcs, és mit frissítsen
az előnézeten). A bezier-görbék és a kiindulási stílusok ugyanott, a `CURVES` és a
`PRESETS` objektumban.
