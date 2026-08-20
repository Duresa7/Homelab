#!/usr/bin/env python3
"""Fail-closed capacity gate for Kasm-owned Proxmox guests."""

from __future__ import annotations

import argparse
import json
import re
import socket
import subprocess
import sys
from pathlib import Path


DYNAMIC_MIN = 6200
DYNAMIC_MAX = 6299
MAX_DYNAMIC_GUESTS = 2
MAX_DYNAMIC_MEMORY_BYTES = 10 * 1024**3
MAX_NODE_MEMORY_RATIO = 0.85
MAX_STORAGE_RATIO = 0.80
DISK_KEY_PATTERN = re.compile(r"^(?:(?:scsi|sata|virtio|ide)|(?:efidisk|tpmstate))\d+$")
SIZE_PATTERN = re.compile(r"(?:^|,)size=(\d+(?:\.\d+)?)([KMGTPE]?)(?:B)?(?:,|$)", re.IGNORECASE)
SIZE_FACTORS = {
    "": 1,
    "K": 1024,
    "M": 1024**2,
    "G": 1024**3,
    "T": 1024**4,
    "P": 1024**5,
    "E": 1024**6,
}


def configured_storage_bytes(config: dict, storage: str) -> int:
    total = 0
    for key, raw_value in config.items():
        value = str(raw_value)
        if not DISK_KEY_PATTERN.match(str(key)) or not value.startswith(f"{storage}:"):
            continue
        match = SIZE_PATTERN.search(value)
        if not match:
            raise ValueError(f"cannot determine configured size for {key} on {storage}")
        total += int(float(match.group(1)) * SIZE_FACTORS[match.group(2).upper()])
    return total


def evaluate_capacity(state: dict) -> dict:
    vmid = int(state["vmid"])
    if not DYNAMIC_MIN <= vmid <= DYNAMIC_MAX:
        return {
            "allowed": True,
            "not_applicable": True,
            "reasons": [],
            "vmid": vmid,
        }

    running_vmids = {int(item) for item in state.get("running_dynamic_vmids", [])}
    running_vmids.discard(vmid)
    requested_memory = int(state.get("requested_memory_bytes", 0))
    dynamic_memory = int(state.get("running_dynamic_memory_bytes", 0))
    node_used = float(state.get("node_memory_used_bytes", 0))
    node_total = float(state.get("node_memory_total_bytes", 0))
    storage_used = float(state.get("storage_used_bytes", 0))
    requested_storage = float(state.get("requested_storage_bytes", 0))
    storage_total = float(state.get("storage_total_bytes", 0))

    projected_count = len(running_vmids) + 1
    projected_dynamic_memory = dynamic_memory + requested_memory
    projected_node_ratio = (node_used + requested_memory) / node_total if node_total else 1.0
    projected_storage_ratio = (
        (storage_used + requested_storage) / storage_total if storage_total else 1.0
    )

    reasons = []
    if projected_count > MAX_DYNAMIC_GUESTS:
        reasons.append("dynamic guest count would exceed 2")
    if projected_dynamic_memory > MAX_DYNAMIC_MEMORY_BYTES:
        reasons.append("dynamic guest memory would exceed 10 GiB")
    if projected_node_ratio > MAX_NODE_MEMORY_RATIO:
        reasons.append("node memory would exceed 85%")
    if projected_storage_ratio > MAX_STORAGE_RATIO:
        reasons.append("thin pool use exceeds 80%")

    return {
        "allowed": not reasons,
        "not_applicable": False,
        "reasons": reasons,
        "vmid": vmid,
        "projected": {
            "dynamic_guest_count": projected_count,
            "dynamic_memory_bytes": projected_dynamic_memory,
            "node_memory_ratio": round(projected_node_ratio, 6),
            "storage_ratio": round(projected_storage_ratio, 6),
        },
    }


def _pvesh_json(path: str) -> object:
    completed = subprocess.run(
        ["pvesh", "get", path, "--output-format", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def collect_live_state(vmid: int, node: str, storage: str) -> dict:
    resources = _pvesh_json("/cluster/resources")
    config = _pvesh_json(f"/nodes/{node}/qemu/{vmid}/config")
    node_status = _pvesh_json(f"/nodes/{node}/status")
    storage_status = _pvesh_json(f"/nodes/{node}/storage/{storage}/status")

    running = []
    dynamic_memory = 0
    for resource in resources:
        resource_vmid = resource.get("vmid")
        if resource.get("type") != "qemu" or resource.get("status") != "running":
            continue
        if resource_vmid is None or not DYNAMIC_MIN <= int(resource_vmid) <= DYNAMIC_MAX:
            continue
        if int(resource_vmid) == vmid:
            continue
        running.append(int(resource_vmid))
        dynamic_memory += int(resource.get("maxmem", 0))

    memory = node_status.get("memory", {})
    requested_memory = int(config.get("memory", 0)) * 1024**2
    return {
        "vmid": vmid,
        "running_dynamic_vmids": running,
        "running_dynamic_memory_bytes": dynamic_memory,
        "requested_memory_bytes": requested_memory,
        "node_memory_used_bytes": int(memory.get("used", 0)),
        "node_memory_total_bytes": int(memory.get("total", 0)),
        "storage_used_bytes": int(storage_status.get("used", 0)),
        "storage_total_bytes": int(storage_status.get("total", 0)),
        "requested_storage_bytes": configured_storage_bytes(config, storage),
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("vmid", nargs="?", type=int)
    parser.add_argument("phase", nargs="?", default="pre-start")
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--node", default=socket.gethostname().split(".")[0])
    parser.add_argument("--storage", default="ssd-lvm1")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    if args.phase != "pre-start":
        print(json.dumps({"allowed": True, "not_applicable": True, "phase": args.phase}))
        return 0
    if args.state_file:
        state = json.loads(args.state_file.read_text(encoding="utf-8"))
    elif args.vmid is not None:
        state = collect_live_state(args.vmid, args.node, args.storage)
    else:
        raise SystemExit("vmid or --state-file is required")

    result = evaluate_capacity(state)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["allowed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"allowed": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
