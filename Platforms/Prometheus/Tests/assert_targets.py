#!/usr/bin/env python3
"""Assert the live Prometheus target set matches the approved one.

Reads the /api/v1/targets response on stdin:

    curl -fsS http://127.0.0.1:9090/api/v1/targets | python3 assert_targets.py

The 2026-07-25 fleet expansion moved from one job per host to one job per
exporter type, so a target is no longer identified by its job label alone. This
keys on the scrape URL and checks the job and host labels attached to it.

Exit codes:
    0  expected target set present, all UP, no stale addresses
    2  target set does not match
    3  a forbidden stale address is still present
    4  a target is not UP
"""

import json
import sys

# scrape URL -> (job, host)
EXPECTED_TARGETS = {
    # node_exporter, 14 hosts
    "http://192.168.70.10:9100/metrics": ("node", "grey-server"),
    "http://192.168.70.11:9100/metrics": ("node", "purple-server"),
    "http://192.168.70.12:9100/metrics": ("node", "blue-server"),
    "http://192.168.70.13:9100/metrics": ("node", "red-server"),
    "http://192.168.72.2:9100/metrics": ("node", "security-01"),
    "http://192.168.72.3:9100/metrics": ("node", "splunk-siem"),
    "http://192.168.90.10:9100/metrics": ("node", "edge-01"),
    "http://192.168.40.35:9100/metrics": ("node", "docker-main"),
    "http://192.168.40.36:9100/metrics": ("node", "ansible-01"),
    "http://192.168.40.39:9100/metrics": ("node", "docker-blue"),
    "http://192.168.40.42:9100/metrics": ("node", "media-01"),
    "http://192.168.80.10:9100/metrics": ("node", "app-01"),
    "http://192.168.80.118:9100/metrics": ("node", "alpha-prod-01"),
    "http://192.168.85.2:9100/metrics": ("node", "docker-network"),
    # cAdvisor, docker-main only. The other six Docker hosts use Docker 29's
    # overlayfs storage driver, where cAdvisor registers no containers.
    "http://192.168.40.35:9101/metrics": ("cadvisor", "docker-main"),
    # Proxmox API exporter
    "http://pve-exporter:9221/pve?module=default&target=192.168.70.10": (
        "proxmox",
        None,
    ),
    # Prometheus self-scrape
    "http://localhost:9090/metrics": ("prometheus", "security-01"),
    # NUT, one target per UPS. Reaching these needed rules in both the UniFi
    # firewall and the Proxmox cluster firewall.
    "http://nut-exporter:9995/nut?target=192.168.70.13%3A3493": ("nut", "red-server"),
    "http://nut-exporter:9995/nut?target=192.168.70.10%3A3493": ("nut", "grey-server"),
}

# The 19 internal service names probed through NPM. Host label is absent; the
# instance label carries the probed URL.
EXPECTED_BLACKBOX_SERVICES = {
    "jellyfin",
    "seerr",
    "sonarr",
    "radarr",
    "prowlarr",
    "qbittorrent",
    "semaphore",
    "immich",
    "booklore",
    "termix",
    "dashboard",
    "forgejo",
    "portainer",
    "peanut",
    "syncthing",
    "wazuh",
    "grafana",
    "prometheus",
    "splunk",
}

# Retired addresses that must never reappear. 192.168.70.20 is the pre-migration
# security-01; 192.168.80.20 is supabase-01, which is stopped. 192.168.80.10
# (app-01) was on this list until 2026-07-25: it had been removed in the
# 2026-07-13 cleanup only because its exporter was unavailable, and it is now a
# legitimate target.
FORBIDDEN_ADDRESSES = {"192.168.70.20", "192.168.80.20"}


def main() -> int:
    targets = json.load(sys.stdin)["data"]["activeTargets"]

    scraped = {}
    blackbox_seen = set()
    for target in targets:
        labels = target["labels"]
        job = labels.get("job")
        if job == "blackbox":
            instance = labels.get("instance", "")
            # https://jellyfin.example.com/ -> jellyfin
            host = instance.split("://", 1)[-1].split("/", 1)[0]
            blackbox_seen.add(host.split(".", 1)[0])
        else:
            scraped[target["scrapeUrl"]] = (job, labels.get("host"))

    for target in sorted(
        targets, key=lambda item: (item["labels"].get("job", ""), item["scrapeUrl"])
    ):
        labels = target["labels"]
        print(
            "|".join(
                [
                    labels.get("job", "?"),
                    labels.get("host") or labels.get("instance", "-"),
                    target["health"],
                    target["lastError"] or "none",
                ]
            )
        )

    problems = []

    missing = set(EXPECTED_TARGETS) - set(scraped)
    unexpected = set(scraped) - set(EXPECTED_TARGETS)
    if missing:
        problems.append(f"missing targets: {sorted(missing)}")
    if unexpected:
        problems.append(f"unexpected targets: {sorted(unexpected)}")
    for url, expected in EXPECTED_TARGETS.items():
        actual = scraped.get(url)
        if actual and actual != expected:
            problems.append(
                f"{url}: expected job/host {expected}, found {actual}"
            )

    missing_services = EXPECTED_BLACKBOX_SERVICES - blackbox_seen
    extra_services = blackbox_seen - EXPECTED_BLACKBOX_SERVICES
    if missing_services:
        problems.append(f"missing blackbox services: {sorted(missing_services)}")
    if extra_services:
        problems.append(f"unexpected blackbox services: {sorted(extra_services)}")

    expected_total = len(EXPECTED_TARGETS) + len(EXPECTED_BLACKBOX_SERVICES)
    if len(targets) != expected_total:
        problems.append(
            f"expected {expected_total} targets, found {len(targets)}"
        )

    if problems:
        for problem in problems:
            print(f"target-set-mismatch: {problem}", file=sys.stderr)
        return 2

    for target in targets:
        for address in FORBIDDEN_ADDRESSES:
            if address in target["scrapeUrl"]:
                print(
                    f"forbidden stale address {address} remains in "
                    f"{target['scrapeUrl']}",
                    file=sys.stderr,
                )
                return 3

    down = [
        (t["labels"].get("job"), t["labels"].get("host") or t["labels"].get("instance"))
        for t in targets
        if t["health"] != "up"
    ]
    if down:
        print(f"targets not UP: {down}", file=sys.stderr)
        return 4

    print(
        f"ASSERTION: {expected_total} expected targets present and all UP "
        f"({len(EXPECTED_TARGETS)} scraped exporters, "
        f"{len(EXPECTED_BLACKBOX_SERVICES)} blackbox services)"
    )
    print("ASSERTION: stale addresses absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
