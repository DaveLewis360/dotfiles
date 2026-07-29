#!/usr/bin/env python3
"""dotswitch overlay applier.

A közös (rice-független) beállításokat (~/dotfiles/shared/common.json) ráteszi a profil
user-override fájljára egy "managed block" formában, a profil natív formátumában:
  - lua:  hl.config({ input = { kb_layout = "hu", ... } })   (caelestia, end4)
  - conf: input { kb_layout = hu ... }                        (HyDE)

Idempotens: minden futáskor eltávolítja a korábbi managed blokkot, majd újat ír.
A managed blokkon kívüli (felhasználói) tartalmat érintetlenül hagyja.

Használat: apply_overlay.py <common.json> <target_file> <lua|conf>
"""
import json
import sys


def build_body(inp: dict, fmt: str) -> str:
    kv = [(k, inp.get(k, "")) for k in ("kb_layout", "kb_variant", "kb_options")]
    kv = [(k, v) for k, v in kv if v != ""]
    numlock = inp.get("numlock_by_default")

    if not kv and not isinstance(numlock, bool):
        return ""

    if fmt == "lua":
        inner = [f'        {k} = "{v}",' for k, v in kv]
        if isinstance(numlock, bool):
            inner.append(f"        numlock_by_default = {'true' if numlock else 'false'},")
        return "hl.config({\n    input = {\n" + "\n".join(inner) + "\n    }\n})"
    else:  # conf
        inner = [f"    {k} = {v}" for k, v in kv]
        if isinstance(numlock, bool):
            inner.append(f"    numlock_by_default = {'true' if numlock else 'false'}")
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
