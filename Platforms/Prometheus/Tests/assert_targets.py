#!/usr/bin/env python3

import json
import sys


EXPECTED_TARGETS = {
    "security-01": "http://192.168.72.2:9100/metrics",
    "edge-01": "http://192.168.90.10:9100/metrics",
    "grey-server": "http://192.168.70.10:9100/metrics",
    "purple-server": "http://192.168.70.11:9100/metrics",
    "blue-server": "http://192.168.70.12:9100/metrics",
    "red-server": "http://192.168.70.13:9100/metrics",
    "proxmox": (
        "http://pve-exporter:9221/pve?module=default&target=192.168.70.10"
    ),
}

FORBIDDEN_ADDRESSES = {"192.168.70.20", "192.168.80.10", "192.168.80.20"}


def main() -> int:
    targets = json.load(sys.stdin)["data"]["activeTargets"]
    actual_targets = {
        target["labels"]["job"]: target["scrapeUrl"] for target in targets
    }

    for target in sorted(targets, key=lambda item: item["labels"]["job"]):
        print(
            "|".join(
                [
                    target["labels"]["job"],
                    target["health"],
                    target["scrapeUrl"],
                    target["lastError"] or "none",
                ]
            )
        )

    if len(targets) != len(EXPECTED_TARGETS) or actual_targets != EXPECTED_TARGETS:
        print(
            f"target-set-mismatch expected={EXPECTED_TARGETS} "
            f"actual={actual_targets} count={len(targets)}",
            file=sys.stderr,
        )
        return 2

    if any(
        address in target["scrapeUrl"]
        for address in FORBIDDEN_ADDRESSES
        for target in targets
    ):
        print("forbidden stale address remains", file=sys.stderr)
        return 3

    if any(target["health"] != "up" for target in targets):
        return 4

    print("ASSERTION: expected target set present and all targets UP")
    print("ASSERTION: stale addresses absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
