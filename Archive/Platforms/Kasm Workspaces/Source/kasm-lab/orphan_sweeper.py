#!/usr/bin/env python3
"""Plan and remove stale Kasm-owned VMs after a fail-closed Kasm API check."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path


DYNAMIC_MIN = 6200
DYNAMIC_MAX = 6299
DEFAULT_GRACE_MINUTES = 30
VMID_PATTERN = re.compile(r"(?<!\d)(62\d{2})(?!\d)")


def _tags(value: object) -> set[str]:
    if isinstance(value, str):
        return {item for item in re.split(r"[;,]", value) if item}
    return {str(item) for item in value or []}


def _timestamp(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def plan_orphans(
    vms: list[dict],
    active_vmids: set[int],
    now: dt.datetime | None = None,
    grace_minutes: int = DEFAULT_GRACE_MINUTES,
    active_names: set[str] | None = None,
    registered_vmids: set[int] | None = None,
    registered_names: set[str] | None = None,
) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(minutes=grace_minutes)
    active_names = {name.casefold() for name in active_names or set()}
    registered_vmids = registered_vmids or set()
    registered_names = {name.casefold() for name in registered_names or set()}
    result = {"delete": [], "keep": []}

    for vm in sorted(vms, key=lambda item: int(item["vmid"])):
        vmid = int(vm["vmid"])
        tags = _tags(vm.get("tags"))
        reason = None
        if not DYNAMIC_MIN <= vmid <= DYNAMIC_MAX:
            reason = "outside reserved VMID range"
        elif "kasm-autoscale" not in tags:
            reason = "missing kasm-autoscale marker"
        elif "retain-evidence" in tags:
            reason = "retained evidence marker"
        name = str(vm.get("name", "")).casefold()
        if reason is None:
            if vmid in active_vmids or name in active_names:
                reason = "active Kasm session"
            elif vmid in registered_vmids or name in registered_names:
                reason = "registered Kasm server"
            elif _timestamp(vm["last_seen"]) > cutoff:
                reason = "inside grace period"

        item = {"vmid": vmid, "name": vm.get("name", ""), "status": vm.get("status", "")}
        if reason:
            item["reason"] = reason
            result["keep"].append(item)
        else:
            item["reason"] = "inactive beyond grace period"
            result["delete"].append(item)
    return result


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _post_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20, context=ssl.create_default_context()) as response:
        return json.load(response)


def _api_payload(settings: dict[str, str], **extra: object) -> dict:
    required = ("KASM_URL", "KASM_API_KEY", "KASM_API_KEY_SECRET")
    missing = [key for key in required if not settings.get(key)]
    if missing:
        raise RuntimeError(f"missing Kasm API settings: {', '.join(missing)}")
    return {
        "api_key": settings["KASM_API_KEY"],
        "api_key_secret": settings["KASM_API_KEY_SECRET"],
        **extra,
    }


def _identifiers(servers: list[dict]) -> tuple[set[int], set[str]]:
    vmids: set[int] = set()
    names: set[str] = set()
    for server in servers:
        searchable = []
        for key in ("hostname", "friendly_name", "name"):
            value = str(server.get(key, "")).strip()
            if value:
                names.add(value.casefold())
                searchable.append(value)
        for match in VMID_PATTERN.finditer(" ".join(searchable)):
            vmid = int(match.group(1))
            if DYNAMIC_MIN <= vmid <= DYNAMIC_MAX:
                vmids.add(vmid)
    return vmids, names


def kasm_inventory(settings: dict[str, str]) -> dict[str, set]:
    base_url = settings.get("KASM_URL", "").rstrip("/") + "/api/public"
    sessions_response = _post_json(base_url + "/get_kasms", _api_payload(settings))
    if sessions_response.get("error_message"):
        raise RuntimeError("Kasm API rejected the session inventory request")

    session_servers = [session.get("server") or {} for session in sessions_response.get("kasms", [])]
    active_vmids, active_names = _identifiers(session_servers)

    pools_response = _post_json(
        base_url + "/get_server_pools",
        _api_payload(settings, page=0, page_size=200),
    )
    if pools_response.get("error_message"):
        raise RuntimeError("Kasm API rejected the server-pool inventory request")

    registered_servers = []
    for pool in pools_response.get("server_pools", []):
        pool_id = pool.get("server_pool_id")
        if not pool_id:
            continue
        detail = _post_json(
            base_url + "/get_server_pools",
            _api_payload(settings, target_server_pool={"server_pool_id": pool_id}),
        )
        if detail.get("error_message"):
            raise RuntimeError("Kasm API rejected a server-pool detail request")
        registered_servers.extend((detail.get("server_pool") or {}).get("servers", []))

    registered_vmids, registered_names = _identifiers(registered_servers)
    return {
        "active_vmids": active_vmids,
        "active_names": active_names,
        "registered_vmids": registered_vmids,
        "registered_names": registered_names,
    }


def _protected(vmid: int, name: str, inventory: dict[str, set]) -> bool:
    folded_name = name.casefold()
    return (
        vmid in inventory["active_vmids"]
        or folded_name in inventory["active_names"]
        or vmid in inventory["registered_vmids"]
        or folded_name in inventory["registered_names"]
    )


def _pvesh_resources() -> list[dict]:
    completed = subprocess.run(
        ["pvesh", "get", "/cluster/resources", "--type", "vm", "--output-format", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def collect_vms(state_path: Path, inventory: dict[str, set], now: dt.datetime) -> list[dict]:
    previous = {}
    if state_path.exists():
        previous = json.loads(state_path.read_text(encoding="utf-8")).get("inactive_since", {})

    current: dict[str, str] = {}
    vms = []
    for resource in _pvesh_resources():
        if resource.get("type") != "qemu" or resource.get("vmid") is None:
            continue
        vmid = int(resource["vmid"])
        if not DYNAMIC_MIN <= vmid <= DYNAMIC_MAX:
            continue
        name = str(resource.get("name", ""))
        if _protected(vmid, name, inventory):
            last_seen = now.isoformat()
        else:
            last_seen = previous.get(str(vmid), now.isoformat())
            current[str(vmid)] = last_seen
        vms.append(
            {
                "vmid": vmid,
                "name": name,
                "status": resource.get("status", ""),
                "last_seen": last_seen,
                "tags": resource.get("tags", ""),
            }
        )

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"inactive_since": current}, indent=2) + "\n", encoding="utf-8")
    os.chmod(state_path, 0o600)
    return vms


def _destroy(vmid: int) -> None:
    status = subprocess.run(["qm", "status", str(vmid)], check=True, capture_output=True, text=True)
    if "status: stopped" not in status.stdout:
        subprocess.run(["qm", "stop", str(vmid), "--timeout", "60"], check=True)
    subprocess.run(
        [
            "qm",
            "destroy",
            str(vmid),
            "--purge",
            "1",
            "--destroy-unreferenced-disks",
            "1",
        ],
        check=True,
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--env-file", type=Path, default=Path("/etc/kasm-lab/orphan-sweeper.env"))
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--runtime-state", type=Path, default=Path("/var/lib/kasm-lab/orphan-state.json"))
    parser.add_argument("--grace-minutes", type=int, default=DEFAULT_GRACE_MINUTES)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    now = dt.datetime.now(dt.timezone.utc)
    if args.state_file:
        state = json.loads(args.state_file.read_text(encoding="utf-8"))
        inventory = {
            "active_vmids": {int(item) for item in state.get("active_vmids", [])},
            "active_names": {str(item).casefold() for item in state.get("active_names", [])},
            "registered_vmids": {int(item) for item in state.get("registered_vmids", [])},
            "registered_names": {
                str(item).casefold() for item in state.get("registered_names", [])
            },
        }
        vms = state.get("vms", [])
    else:
        settings = _read_env(args.env_file)
        inventory = kasm_inventory(settings)
        vms = collect_vms(args.runtime_state, inventory, now)

    plan = plan_orphans(
        vms,
        inventory["active_vmids"],
        now=now,
        grace_minutes=args.grace_minutes,
        active_names=inventory["active_names"],
        registered_vmids=inventory["registered_vmids"],
        registered_names=inventory["registered_names"],
    )
    if args.apply and not args.state_file:
        fresh_inventory = kasm_inventory(_read_env(args.env_file))
        for item in plan["delete"]:
            if _protected(item["vmid"], item["name"], fresh_inventory):
                raise RuntimeError(
                    f"VM {item['vmid']} became active or registered during the final Kasm check"
                )
            _destroy(item["vmid"])
    print(json.dumps({"mode": "apply" if args.apply else "dry-run", **plan}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
