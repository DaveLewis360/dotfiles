#!/usr/bin/env python3
"""dotswitch overlay applier.

A közös (rice-független) beállításokat (~/dotfiles/shared/common.json) ráteszi a profil
user-override fájljára egy "managed block" formában, a profil natív formátumában:
  - lua:  hl.config({ input = { kb_layout = "hu", touchpad = { ... } } })   (caelestia, end4)
  - conf: input { kb_layout = hu ... touchpad { ... } }                     (HyDE)

Idempotens: minden futáskor eltávolítja a korábbi managed blokkot, majd újat ír.
A managed blokkon kívüli (felhasználói) tartalmat érintetlenül hagyja.

A common.json "input" blokkja SZABADON bővíthető: minden skalár kulcs átkerül, és
egy szint mélységű alblokkokat (pl. touchpad) is kezel. Az üres string értékű
kulcsokat kihagyja, így a "kb_variant": "" nem ír felesleges sort.

Használat: apply_overlay.py <common.json> <target_file> <lua|conf>
"""
import json
import sys

# Ezek nem beállítások, hanem dokumentáció a common.json-ban.
IGNORED_KEYS = ("_comment",)


def fmt_value(v, fmt: str) -> str:
    """Egy skalár érték a cél formátum szerint."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    # string
    return f'"{v}"' if fmt == "lua" else str(v)


def emit(d: dict, fmt: str, indent: int) -> list[str]:
    """Rekurzívan (egy szint mélyen) kiírja a kulcs-érték párokat."""
    pad = " " * indent
    scalars, blocks = [], []

    for k, v in d.items():
        if k in IGNORED_KEYS:
            continue
        if isinstance(v, dict):
            blocks.append((k, v))
            continue
        # Az üres stringet szándékosan kihagyjuk (pl. kb_variant: "")
        if isinstance(v, str) and v == "":
            continue
        if fmt == "lua":
            scalars.append(f"{pad}{k} = {fmt_value(v, fmt)},")
        else:
            scalars.append(f"{pad}{k} = {fmt_value(v, fmt)}")

    lines = list(scalars)
    for name, sub in blocks:
        inner = emit(sub, fmt, indent + 4)
        if not inner:
            continue
        if fmt == "lua":
            lines.append(f"{pad}{name} = {{")
            lines.extend(inner)
            lines.append(f"{pad}}},")
        else:
            lines.append(f"{pad}{name} {{")
            lines.extend(inner)
            lines.append(f"{pad}}}")
    return lines


def build_body(inp: dict, fmt: str) -> str:
    inner = emit(inp, fmt, 8 if fmt == "lua" else 4)
    if not inner:
        return ""
    if fmt == "lua":
        return "hl.config({\n    input = {\n" + "\n".join(inner) + "\n    }\n})"
    return "input {\n" + "\n".join(inner) + "\n}"


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: apply_overlay.py <common.json> <target> <lua|conf>", file=sys.stderr)
        return 2
    common_path, target, fmt = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(common_path) as f:
        data = json.load(f)
    body = build_body(data.get("input", {}), fmt)

    comment = "--" if fmt == "lua" else "#"
    begin = f"{comment} >>> dotswitch managed (common settings) >>>"
    end = f"{comment} <<< dotswitch managed <<<"

    try:
        with open(target) as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        lines = []

    # Strip any previous managed block (idempotent).
    out, skip = [], False
    for ln in lines:
        s = ln.strip()
        if s == begin:
            skip = True
            continue
        if skip and s == end:
            skip = False
            continue
        if not skip:
            out.append(ln)

    if body:
        while out and out[-1].strip() == "":
            out.pop()
        if out:
            out.append("")
        out.append(begin)
        out.extend(body.splitlines())
        out.append(end)

    with open(target, "w") as f:
        f.write("\n".join(out) + ("\n" if out else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
