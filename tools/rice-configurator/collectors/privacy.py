"""Titok- és személyesadat-szűrő a generált katalógusra (a repó publikus).

A collect.py ezzel ellenőrzi a kimenetet, mielőtt kiírja. Találat esetén
nem ír fájlt, és kilép hibával.
"""
from __future__ import annotations

import re

PATTERNS = [
    ("home-útvonal", re.compile(r"/home/[a-z_][\w-]*")),
    ("IPv4", re.compile(r"(?<![\w.])(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\w.])")),
    ("tailnet", re.compile(r"\.ts\.net\b|tailc[0-9a-f]+", re.I)),
    ("e-mail", re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I)),
    ("GitHub-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|github_pat_\w{20,}")),
    ("API-kulcs", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}|\bxox[abprs]-[\w-]{10,}|\bAKIA[0-9A-Z]{16}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("privát kulcs", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("jelszó/token mező", re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\b\s*[=:]\s*[\"']?[^\s\"',}]{6,}")),
    ("hosszú hex", re.compile(r"\b[0-9a-f]{32,}\b")),
    ("MAC-cím", re.compile(r"\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b", re.I)),
    ("URL-hitelesítő", re.compile(r"https?://[^\s/\"']*:[^\s/\"']*@")),
]

# ismert, ártalmatlan találatok (pl. a Ghostty dokumentációjában szereplő példák)
ALLOW = {
    "IPv4": {"127.0.0.1", "0.0.0.0"},
    "e-mail": set(),
}


def scan(text: str) -> list[tuple[str, str, str]]:
    """(minta-neve, találat, környezet) listája."""
    found = []
    for name, pat in PATTERNS:
        for m in pat.finditer(text):
            hit = m.group(0)
            if hit in ALLOW.get(name, set()):
                continue
            ctx = text[max(0, m.start() - 60): m.end() + 40].replace("\n", " ")
            found.append((name, hit, ctx))
    return found
