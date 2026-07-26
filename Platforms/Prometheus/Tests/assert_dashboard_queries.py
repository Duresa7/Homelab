#!/usr/bin/env python3
"""Assert every PromQL expression in a Grafana dashboard returns data.

A dashboard can load cleanly and still show empty panels, which is worse than a
broken one because it reads as "nothing wrong". This walks the versioned
dashboard JSON, substitutes the Grafana variables the queries use, runs each
expression against the Prometheus HTTP API, and fails on any that error or come
back with no series.

Usage:
    python3 assert_dashboard_queries.py <dashboard.json> [prometheus_base_url]

Default base URL is http://127.0.0.1:9090.

Exit codes:
    0  every query returned at least one series
    2  one or more queries returned an error
    3  one or more queries returned no series
    4  the dashboard file could not be read or parsed

Queries whose panel title appears in ALLOW_EMPTY may legitimately return
nothing; they are reported but do not fail the run.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

# Grafana interpolates these before sending a query. The substitutions below
# mirror what the dashboard's own defaults resolve to, so the assertion tests
# the same expression Grafana would send.
# `$host` resolves to `.*` here rather than to one hostname, so the per-host
# detail row is tested against every host at once. Every panel there matches with
# `host=~"$host"` for exactly that reason.
VARIABLE_SUBSTITUTIONS = {
    "$__rate_interval": "5m",
    "$__interval": "1m",
    "$role": ".*",
    "$host": ".*",
}

# Panels that are correct when empty. A restart table with no rows means nothing
# restarted, which is the desired state rather than a fault.
ALLOW_EMPTY = {
    "Container restarts in the last 6 hours",
}


def interpolate(expr: str) -> str:
    for name, value in VARIABLE_SUBSTITUTIONS.items():
        expr = expr.replace(name, value)
    return expr


def collect_queries(dashboard: dict) -> list[tuple[str, str, str]]:
    """Return (panel_title, refId, expr) for every query, including nested rows."""
    found: list[tuple[str, str, str]] = []

    def walk(panels: list) -> None:
        for panel in panels or []:
            title = panel.get("title", "<untitled>")
            for target in panel.get("targets") or []:
                expr = target.get("expr")
                if expr and not target.get("hide"):
                    found.append((title, target.get("refId", "?"), expr))
            # Collapsed rows carry their children in a nested list.
            if panel.get("panels"):
                walk(panel["panels"])

    walk(dashboard.get("panels", []))
    return found


def run_query(base_url: str, expr: str) -> tuple[bool, int, str]:
    """Return (ok, series_count, message)."""
    url = f"{base_url.rstrip('/')}/api/v1/query?query=" + urllib.parse.quote(expr)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        detail = ""
        try:
            detail = json.load(error).get("error", "")
        except Exception:
            detail = error.reason if hasattr(error, "reason") else str(error)
        return False, 0, f"HTTP {error.code}: {detail}"
    except Exception as error:  # noqa: BLE001 - report whatever the transport gave us
        return False, 0, str(error)

    if payload.get("status") != "success":
        return False, 0, payload.get("error", "query returned a non-success status")
    return True, len(payload["data"]["result"]), ""


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 4

    path = argv[1]
    base_url = argv[2] if len(argv) > 2 else "http://127.0.0.1:9090"

    try:
        dashboard = json.load(open(path, encoding="utf-8"))
    except Exception as error:  # noqa: BLE001
        print(f"cannot read dashboard {path}: {error}")
        return 4

    queries = collect_queries(dashboard)
    if not queries:
        print(f"no queries found in {path}")
        return 4

    errored: list[str] = []
    empty: list[str] = []
    allowed_empty: list[str] = []

    print(f"Checking {len(queries)} queries from {dashboard.get('title', path)}")
    print(f"against {base_url}\n")

    for title, ref_id, raw_expr in queries:
        expr = interpolate(raw_expr)
        ok, count, message = run_query(base_url, expr)
        label = f"{title} [{ref_id}]"
        if not ok:
            print(f"  ERROR  {label}: {message}")
            errored.append(label)
        elif count == 0:
            if title in ALLOW_EMPTY:
                print(f"  empty  {label} (allowed)")
                allowed_empty.append(label)
            else:
                print(f"  EMPTY  {label}")
                empty.append(label)
        else:
            print(f"  ok     {label} -> {count} series")

    print()
    print(
        f"{len(queries)} queries: "
        f"{len(queries) - len(errored) - len(empty) - len(allowed_empty)} returned data, "
        f"{len(allowed_empty)} allowed empty, "
        f"{len(empty)} unexpectedly empty, "
        f"{len(errored)} errored"
    )

    if errored:
        print("\nErrored queries:")
        for label in errored:
            print(f"  - {label}")
        return 2
    if empty:
        print("\nUnexpectedly empty queries:")
        for label in empty:
            print(f"  - {label}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
