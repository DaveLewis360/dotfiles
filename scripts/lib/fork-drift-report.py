#!/usr/bin/env python3
"""A fork-drift részletes jelentése.

Külön fájl, nem `python3 -c` egysoros: a commit-üzenetek aposztrófot és
idézőjelet is tartalmaznak, és a shellbe ágyazott Python-kódban ezek
elkerülhetetlenül escape-hibát okoznak. Az adat argv-ben jön, tehát a shell
nem is látja a tartalmát.

Használat: fork-drift-report.py '<json>'
"""
import json
import sys

B = "\033[1m"
DIM = "\033[2m"
YLW = "\033[33m"
R = "\033[0m"


def main() -> int:
    if len(sys.argv) < 2:
        return 2
    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"    (a jelentés nem olvasható: {e})", file=sys.stderr)
        return 1

    for entry in data.get("drifted", []):
        local = entry["local"]
        upstream = entry["upstream"]
        commits = entry["commits"]
        ins = entry["ins"]
        dele = entry["del"]
        print(f"    {B}{local}{R}  {DIM}← {upstream}{R}")
        print(f"        {commits} commit, +{ins} -{dele}")
        for line in entry.get("log", []):
            print(f"        {DIM}· {line}{R}")
        print()

    for entry in data.get("missing", []):
        local, upstream = entry[0], entry[1]
        print(f"    {YLW}{local}{R}  {DIM}← {upstream} (már nincs upstreamben){R}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
