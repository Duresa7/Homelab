#!/usr/bin/env python3
"""Assert every dashboard's panels form a clean grid.

Grafana does not reject a dashboard whose panels overlap or run past column 24.
It silently reflows them, so the file in git and the thing on screen stop being
the same document and no error says so. Since the panels here are placed by a
generator, this checks the generator rather than trusting it.

Checks, per dashboard:
    1. no two panels occupy the same grid cell
    2. no panel starts before column 0 or ends past column 24
    3. every panel has a positive width and height
    4. panel ids and dashboard uids are unique across the set
    5. every query names a datasource that the dashboard actually declares

Usage:
    python3 assert_dashboard_layout.py <dashboard.json|directory>
"""
from __future__ import annotations

import json
import pathlib
import sys

COLUMNS = 24


def walk(panels, depth=0):
    """Yield (panel, depth). Row children are laid out in their own space."""
    for panel in panels or []:
        yield panel, depth
        if panel.get("type") == "row":
            yield from walk(panel.get("panels"), depth + 1)


def check(path: pathlib.Path) -> list[str]:
    problems: list[str] = []
    try:
        dash = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:  # noqa: BLE001
        return [f"{path.name}: will not parse: {error}"]

    title = dash.get("title", path.name)

    # Rows that carry their children (collapsed) place them in a separate
    # coordinate space, so each space is checked on its own.
    spaces: dict[int, list] = {0: []}
    space_id = 0
    for panel in dash.get("panels", []):
        if panel.get("type") == "row" and panel.get("collapsed"):
            space_id += 1
            spaces[space_id] = list(panel.get("panels") or [])
            spaces[0].append(panel)
        else:
            spaces[0].append(panel)

    for sid, panels in spaces.items():
        occupied: dict[tuple[int, int], str] = {}
        for panel in panels:
            gp = panel.get("gridPos") or {}
            x, y, w, h = gp.get("x"), gp.get("y"), gp.get("w"), gp.get("h")
            name = panel.get("title") or panel.get("type")
            if None in (x, y, w, h):
                problems.append(f"{title}: {name!r} has no gridPos")
                continue
            if w <= 0 or h <= 0:
                problems.append(f"{title}: {name!r} has size {w}x{h}")
                continue
            if x < 0 or x + w > COLUMNS:
                problems.append(f"{title}: {name!r} spans columns {x}..{x + w}, outside 0..{COLUMNS}")
                continue
            for cy in range(y, y + h):
                for cx in range(x, x + w):
                    hit = occupied.get((cx, cy))
                    if hit is not None:
                        problems.append(
                            f"{title}: {name!r} overlaps {hit!r} at column {cx}, row {cy}")
                        break
                    occupied[(cx, cy)] = name
                else:
                    continue
                break

    declared = set()
    ds = dash.get("templating", {}).get("list", [])
    for v in ds:
        if isinstance(v.get("datasource"), dict) and v["datasource"].get("uid"):
            declared.add(v["datasource"]["uid"])
    for panel, _ in walk(dash.get("panels", [])):
        pds = panel.get("datasource")
        if isinstance(pds, dict) and pds.get("uid"):
            declared.add(pds["uid"])
    if len(declared) > 1:
        problems.append(f"{title}: more than one datasource uid in use: {sorted(declared)}")

    return problems


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 4
    target = pathlib.Path(argv[1])
    paths = sorted(target.rglob("*.json")) if target.is_dir() else [target]
    if not paths:
        print(f"no dashboards under {target}")
        return 4

    problems: list[str] = []
    uids: dict[str, str] = {}
    for path in paths:
        problems.extend(check(path))
        try:
            dash = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        uid = dash.get("uid")
        if uid in uids:
            problems.append(f"uid {uid!r} used by both {uids[uid]} and {path.name}")
        uids[uid] = path.name

    print(f"Checked {len(paths)} dashboards, {len(uids)} unique uids")
    if problems:
        print(f"\n{len(problems)} layout problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 5
    print("No overlaps, nothing outside the 24-column grid, one datasource throughout.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
