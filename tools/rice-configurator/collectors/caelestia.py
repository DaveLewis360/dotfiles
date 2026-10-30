"""Caelestia shell: a shell.json / shell-tokens.json séma a C++ forrásból.

A shell (DaveLewis360/shell fork, a my-caelestia-shell-bar build) a configot
C++-ban deklarálja (plugin/src/Caelestia/Config/*.hpp, CONFIG_PROPERTY makrók).
Ez a modul a fejlécekből felépíti a teljes kulcsfát (típus, alapérték, enum-
értékek), a Nexus beállítás-oldalak QML-jéből hozzáveszi a felirat/leírás
szövegeket és a csúszkák határait, majd ráteszi az élő shell.json értékeit.

A forrást csak olvassa.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

MACROS = ("CONFIG_PROPERTY", "CONFIG_GLOBAL_PROPERTY", "CONFIG_ENUM_PROPERTY",
          "CONFIG_GLOBAL_ENUM_PROPERTY", "CONFIG_SUBOBJECT", "CONFIG_GLOBAL_SUBOBJECT",
          "CONFIG_LIST", "CONFIG_GLOBAL_LIST")
QFONT_WEIGHTS = {"Thin": 100, "ExtraLight": 200, "Light": 300, "Normal": 400, "Medium": 500,
                 "DemiBold": 600, "Bold": 700, "ExtraBold": 800, "Black": 900}


# ─────────────────────────────────────────────────────────────────────────────
#  kis C++-szöveg segédek
# ─────────────────────────────────────────────────────────────────────────────

def strip_comments_keep_lines(src: str) -> str:
    """// és /* */ kommentek törlése; a stringeken belül nem."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1]); i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            out.append(c); i += 1
    return "".join(out)


def balanced(src: str, start: int) -> int:
    """A src[start] == '(' zárójel párjának indexe (stringeket átugorva)."""
    depth, i, n = 0, start, len(src)
    while i < n:
        c = src[i]
        if c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            i = j + 1
            continue
        if c in "({[":
            depth += 1
        elif c in ")}]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("kiegyensúlyozatlan zárójel")


def split_args(s: str) -> list[str]:
    """Felső szintű vesszők mentén szétvágja a makró-argumentumokat."""
    args, depth, cur, i, n = [], 0, [], 0, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 2 if s[j] == "\\" else 1
            cur.append(s[i:j + 1]); i = j + 1
            continue
        if c in "({[<" and not (c == "<" and depth == 0 and not re.match(r"\w", s[i - 1:i] or " ")):
            depth += 1
        elif c in ")}]>" and depth > 0:
            depth -= 1
        if c == "," and depth == 0:
            args.append("".join(cur).strip()); cur = []
        else:
            cur.append(c)
        i += 1
    if "".join(cur).strip():
        args.append("".join(cur).strip())
    return args


def macro_calls(body: str, names=MACROS):
    """(makrónév, [argumentumok], pozíció) a body-ban, sorrendben."""
    pat = re.compile(r"\b(" + "|".join(names) + r")\s*\(")
    pos = 0
    while True:
        m = pat.search(body, pos)
        if not m:
            return
        open_i = m.end() - 1
        close_i = balanced(body, open_i)
        yield m.group(1), split_args(body[open_i + 1:close_i]), m.start()
        pos = close_i + 1


# ─────────────────────────────────────────────────────────────────────────────
#  alapértékek: C++ inicializáló → Python érték
# ─────────────────────────────────────────────────────────────────────────────

def _vmap(pairs):
    return {k: v for k, v in pairs}


def cpp_value(expr: str, ctype: str):
    """Egy C++ alapérték-kifejezés értéke, vagy {'raw': ...}, ha nem értelmezhető."""
    e = expr.strip()
    m = re.fullmatch(r"DEFAULT_ARG\((.*)\)", e, re.S)
    if m:
        e = m.group(1).strip()
    loc = re.match(r"QStandardPaths::writableLocation\(QStandardPaths::(\w+)Location\)\s*\+\s*u\"([^\"]*)\"_s$", e)
    if loc:
        return "~/" + loc.group(1) + loc.group(2)
    strings: list[str] = []

    def keep(m):
        strings.append(bytes(m.group(1), "utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8"))
        return f"__S{len(strings) - 1}__"

    try:
        t = re.sub(r'u"((?:[^"\\]|\\.)*)"_s', keep, e)
        t = re.sub(r'QStringLiteral\("((?:[^"\\]|\\.)*)"\)', keep, t)
        t = re.sub(r'(?<![\w_])"((?:[^"\\]|\\.)*)"', keep, t)
        t = re.sub(r"\bmarkCtx\((__S\d+__)\s*,\s*__S\d+__\)", r"\1", t)
        t = re.sub(r"\bmark\((__S\d+__)\)", r"\1", t)
        t = re.sub(r"\bLIST_ENTRY\((\w+),\s*(true|false)\)",
                   lambda m: f'_vmap([["id","{m.group(1)}"],["enabled",{m.group(2)}]])', t)
        t = re.sub(r"\bICON_RULE_EXACT\((__S\d+__),\s*(__S\d+__)\)",
                   r'_vmap([["name",\1],["icon",\2]])', t)
        t = re.sub(r"\bICON_RULE_REGEX\((__S\d+__),\s*(__S\d+__),\s*(__S\d+__)\)",
                   r'_vmap([["regex",\1],["flags",\2],["icon",\3]])', t)
        t = re.sub(r"\b(?:caelestia::settings::)?vmap\(", "_vmap(", t)
        t = re.sub(r"\bQ(?:String|Variant)?List(?:<\w+>)?\s*\{", "{", t)
        t = re.sub(r"\bQFont::(\w+)", lambda m: str(QFONT_WEIGHTS.get(m.group(1), 400)), t)
        t = re.sub(r"static_cast<int>\(", "int(", t)
        t = re.sub(r"std::numeric_limits<int>::max\(\)", "2147483647", t)
        t = re.sub(r"\b(?:caelestia::config::)?(\w+)::(\w+)\b", lambda m: f'"{m.group(2)}"', t)
        t = t.replace("{", "[").replace("}", "]")
        t = re.sub(r"\btrue\b", "True", t)
        t = re.sub(r"\bfalse\b", "False", t)
        t = re.sub(r"(\d)\.?f\b", r"\1", t)
        t = re.sub(r"__S(\d+)__", lambda m: repr(strings[int(m.group(1))]), t)
        val = eval(t, {"__builtins__": {}}, {"_vmap": _vmap, "int": int, "True": True, "False": False})
    except Exception:
        return {"raw": expr.strip()}
    if val == [] and ctype in ("QString",):
        return ""
    if val == [] and ctype in ("QVariantMap",):
        return {}
    if val == [] and ctype in ("QVariant",):
        return None
    if isinstance(val, float) and val.is_integer() and ctype == "int":
        return int(val)
    if isinstance(val, float):
        return round(val, 6)
    if isinstance(val, list) and ctype == "QList<qreal>":
        return [round(float(x), 6) for x in val]
    return val


# ─────────────────────────────────────────────────────────────────────────────
#  osztályok beolvasása
# ─────────────────────────────────────────────────────────────────────────────

def _font_classes(src: str) -> dict[str, list[dict]]:
    """Az appearanceconfig.hpp FONT_STYLE / FONT_CONFIG makróinak kifejtése."""
    classes: dict[str, list[dict]] = {}

    def font_props(fexpr: str) -> dict:
        d = {"family": "", "size": None, "weight": 400, "italic": False, "vaxes": {"ROND": 25}}
        m = re.search(r"FONT\(\{(.*)\}\)", fexpr, re.S)
        inner = m.group(1) if m else ""
        for k, v in re.findall(r"\.(\w+)\s*=\s*(\{\}|static_cast<int>\([^)]*\)|[^,}]+)", inner):
            d[k] = cpp_value(v, "QVariantMap" if k == "vaxes" else "int")
        return d

    def font_class(name: str, props: dict) -> None:
        classes[name] = [
            {"kind": "prop", "type": "QString", "name": "family", "default": props["family"],
             "comment": "Üres: a stílus családját örökli"},
            {"kind": "prop", "type": "int", "name": "size", "default": props["size"]},
            {"kind": "prop", "type": "int", "name": "weight", "default": props["weight"]},
            {"kind": "prop", "type": "bool", "name": "italic", "default": props["italic"]},
            {"kind": "prop", "type": "QVariantMap", "name": "vaxes", "default": props["vaxes"]},
        ]

    body = strip_comments_keep_lines(src)
    for name, args, _ in macro_calls(body, ("FONT_STYLE", "FONT_CONFIG")):
        if name == "FONT_STYLE" and len(args) == 5:
            style, fam = args[0], cpp_value(args[1], "QString")
            for size, fexpr in zip(("Large", "Medium", "Small"), args[2:]):
                font_class(f"FontConfig{style}{size}", font_props(fexpr))
            classes[f"FontStyle{style}"] = [
                {"kind": "prop", "type": "QString", "name": "family", "default": fam},
                *[{"kind": "sub", "type": f"FontConfig{style}{s}", "name": s.lower()}
                  for s in ("Large", "Medium", "Small")],
            ]
        elif name == "FONT_CONFIG" and len(args) == 3 and args[0] != "Style":
            font_class(f"FontConfig{args[0]}{args[1]}", font_props(args[2]))
    return classes


def parse_headers(cfg_dir: Path) -> tuple[dict, dict]:
    """(osztálynév → tagok, listatípus → elemosztály)"""
    classes: dict[str, list[dict]] = {}
    list_types: dict[str, str] = {}
    for hpp in sorted(cfg_dir.glob("*.hpp")):
        raw = hpp.read_text()
        if hpp.name == "appearanceconfig.hpp":
            classes.update(_font_classes(raw))
        for m in re.finditer(r"CONFIG_LIST_TYPE\((\w+),\s*(\w+)\)", raw):
            list_types[m.group(2)] = m.group(1)
        for cm in re.finditer(r"^class (\w+) : public settings::(?:ObjectNode|RootNode) \{", raw, re.M):
            cname = cm.group(1)
            end = raw.find("\n};", cm.end())
            block = raw[cm.end():end]
            if "#define" in block:
                continue
            members = []
            # a tag előtti // komment leírásként megmarad
            lines = block.split("\n")
            comment_for: dict[int, str] = {}
            pending: list[str] = []
            offset = 0
            for ln in lines:
                s = ln.strip()
                if s.startswith("//"):
                    pending.append(s.lstrip("/").strip())
                elif s.startswith("CONFIG_"):
                    comment_for[offset] = " ".join(pending).strip()
                    pending = []
                elif s:
                    pending = []
                offset += len(ln) + 1
            for mname, args, pos in macro_calls(block):
                comment = ""
                line_start = block.rfind("\n", 0, pos) + 1
                comment = comment_for.get(line_start, "")
                trail = re.search(r"//\s*(.*)", block[pos:block.find("\n", pos) if block.find("\n", pos) > 0 else None])
                glob = "GLOBAL" in mname
                if mname.endswith("SUBOBJECT"):
                    members.append({"kind": "sub", "type": args[0], "name": args[1], "global": glob})
                elif mname.endswith("LIST"):
                    members.append({"kind": "list", "type": args[0], "name": args[1], "global": glob,
                                    "default": cpp_value(args[2], "list") if len(args) > 2 else [],
                                    "comment": comment})
                elif "ENUM" in mname:
                    members.append({"kind": "prop", "type": "enum:" + args[0], "name": args[1], "global": glob,
                                    "default": cpp_value(args[2], "enum"), "comment": comment})
                else:
                    ctype = args[0]
                    members.append({"kind": "prop", "type": ctype, "name": args[1], "global": glob,
                                    "default": cpp_value(",".join(args[2:3]) if len(args) > 2 else "{}", ctype),
                                    "comment": comment or (trail.group(1).strip() if trail and "[fork]" not in trail.group(1) else "")})
            classes[cname] = members
    return classes, list_types


def parse_enums(cfg_dir: Path) -> dict[str, list[str]]:
    src = (cfg_dir / "enums.hpp").read_text()
    return {m.group(1): [x.strip() for x in m.group(2).split(",") if x.strip()]
            for m in re.finditer(r"^ENUM\((\w+),\s*([^)]*)\)", src, re.M)}


# ─────────────────────────────────────────────────────────────────────────────
#  Nexus: feliratok és határok a beállítás-oldalakból
# ─────────────────────────────────────────────────────────────────────────────

TR = r'Tr\.tr(?:Ctx)?\("((?:[^"\\]|\\.)*)"'


def parse_nexus(nexus_dir: Path) -> dict[str, dict]:
    """config-kulcs → {label, subtext, from, to, step, page}"""
    out: dict[str, dict] = {}
    for qml in sorted(nexus_dir.rglob("*.qml")):
        page = qml.stem
        text = qml.read_text()
        title_m = re.search(r"title:\s*" + TR, text)
        section = title_m.group(1) if title_m else ""
        stack: list[dict] = [{"refs": [], "props": {}}]
        for ln in text.split("\n"):
            s = ln.strip()
            opens, closes = s.count("{"), s.count("}")
            # egy soros `x: { ... }` kifejezéseknél a nyitás és zárás kiegyenlíti egymást
            top = stack[-1]
            for key in ("label", "text", "subtext", "from", "to", "stepSize", "title"):
                m = re.match(rf"{key}:\s*(.*)$", s)
                if m:
                    v = m.group(1)
                    tm = re.search(TR, v)
                    if tm:
                        top["props"][key] = tm.group(1)
                    elif key in ("from", "to", "stepSize"):
                        nm = re.match(r"(-?[\d.]+)", v)
                        if nm:
                            top["props"][key] = float(nm.group(1))
            for ref in re.findall(r"\bGlobalConfig\.([a-zA-Z]+(?:\.[a-zA-Z]+)+)\s*=(?!=)", s):
                top["refs"].append(ref)
            for _ in range(max(0, opens - closes)):
                stack.append({"refs": [], "props": {}})
            for _ in range(max(0, closes - opens)):
                if len(stack) > 1:
                    blk = stack.pop()
                    label = blk["props"].get("label") or blk["props"].get("text") or blk["props"].get("title")
                    for ref in dict.fromkeys(blk["refs"]):
                        if label and ref not in out:
                            out[ref] = {"label": label, "subtext": blk["props"].get("subtext", ""),
                                        "from": blk["props"].get("from"), "to": blk["props"].get("to"),
                                        "step": blk["props"].get("stepSize"), "page": page, "section": section}
                    if not label and blk["refs"]:
                        stack[-1]["refs"].extend(blk["refs"])
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  fa + élő értékek
# ─────────────────────────────────────────────────────────────────────────────

def _missing():
    return _MISSING


class _Missing:
    def __repr__(self):
        return "<nincs>"


_MISSING = _Missing()


def _get(d, path):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return _MISSING
        cur = cur[p]
    return cur


def walk(classes, list_types, enums, cls, path, out, glob=False):
    for m in classes.get(cls, []):
        p = path + [m["name"]]
        g = glob or m.get("global", False)
        if m["kind"] == "sub":
            out.append({"node": True, "path": p, "type": m["type"]})
            walk(classes, list_types, enums, m["type"], p, out, g)
        elif m["kind"] == "list":
            elem = list_types.get(m["type"], "")
            fields = [f["name"] for f in classes.get(elem, []) if f["kind"] == "prop"]
            out.append({"path": p, "type": "list", "element": elem, "fields": fields,
                        "default": m.get("default"), "global": g, "comment": m.get("comment", "")})
        else:
            t = m["type"]
            entry = {"path": p, "type": t, "default": m.get("default"), "global": g,
                     "comment": m.get("comment", "")}
            if t.startswith("enum:"):
                entry["options"] = enums.get(t[5:], [])
            out.append(entry)


def collect(shell_repo: Path, shell_json: Path, tokens_json: Path, other_profiles: dict[str, Path]):
    cfg_dir = shell_repo / "plugin/src/Caelestia/Config"
    classes, list_types = parse_headers(cfg_dir)
    enums = parse_enums(cfg_dir)
    nexus = parse_nexus(shell_repo / "modules/nexus")

    def load(p: Path):
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}

    live = load(shell_json)
    tokens_live = load(tokens_json) if tokens_json.exists() else {}
    others = {name: load(p) for name, p in other_profiles.items()}

    result = {}
    for root_cls, live_data, key in (("ConfigRoot", live, "shell"), ("TokensRoot", tokens_live, "tokens")):
        flat: list[dict] = []
        walk(classes, list_types, enums, root_cls, [], flat)
        known = set()
        for e in flat:
            known.add(tuple(e["path"]))
            if e.get("node"):
                continue
            cur = _get(live_data, e["path"])
            e["set"] = cur is not _MISSING
            e["current"] = e["default"] if cur is _MISSING else cur
            dotted = ".".join(e["path"])
            if key == "shell" and dotted in nexus:
                e["nexus"] = nexus[dotted]
            if key == "shell":
                diff = {}
                for name, data in others.items():
                    ov = _get(data, e["path"])
                    ov = e["default"] if ov is _MISSING else ov
                    if ov != e["current"]:
                        diff[name] = ov
                if diff:
                    e["others"] = diff
        unknown = []

        def find_unknown(d, path):
            if not isinstance(d, dict):
                return
            for k, v in d.items():
                p = path + [k]
                if tuple(p) not in known:
                    unknown.append({"path": p, "value": v})
                elif isinstance(v, dict):
                    find_unknown(v, p)
        find_unknown(live_data, [])
        result[key] = {"entries": flat, "unknown": unknown}
    result["nexus_labels"] = len(nexus)
    result["enums"] = enums
    return result


if __name__ == "__main__":
    import sys
    home = Path.home()
    r = collect(home / "Reference/my-caelestia-shell-bar",
                home / ".config/caelestia/shell.json",
                home / ".config/caelestia/shell-tokens.json", {})
    for k in ("shell", "tokens"):
        leaves = [e for e in r[k]["entries"] if not e.get("node")]
        print(k, "leaves:", len(leaves), "set:", sum(e["set"] for e in leaves),
              "nexus:", sum(1 for e in leaves if "nexus" in e),
              "raw defaults:", sum(1 for e in leaves if isinstance(e["default"], dict) and "raw" in e["default"]),
              "unknown:", len(r[k]["unknown"]))
    if "-v" in sys.argv:
        for e in r["shell"]["entries"]:
            if not e.get("node"):
                print(".".join(e["path"]), e["type"], json.dumps(e["default"], ensure_ascii=False)[:60],
                      "| cur:", json.dumps(e["current"], ensure_ascii=False)[:40], "|", e.get("nexus", {}).get("label", ""))
        print("UNKNOWN", r["shell"]["unknown"])
