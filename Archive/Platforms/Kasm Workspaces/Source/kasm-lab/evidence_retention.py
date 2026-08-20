#!/usr/bin/env python3
"""Retain a stopped malware VM's evidence disk as an LVM-thin snapshot."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DYNAMIC_MIN = 6200
DYNAMIC_MAX = 6299
EVIDENCE_MIN = 6300
EVIDENCE_MAX = 6399
EVIDENCE_SLOT = "scsi1"
SOURCE_PATTERN = re.compile(r"^ssd-lvm1:(vm-(\d+)-disk-\d+)(?:,|$)")


def plan_retention(state: dict) -> dict:
    vmid = int(state["vmid"])
    phase = state.get("phase", "")
    config = state.get("config", {})
    tags = {item for item in str(config.get("tags", "")).split(";") if item}

    if phase != "post-stop":
        return {"applicable": False, "reason": "phase is not post-stop", "vmid": vmid}
    if not DYNAMIC_MIN <= vmid <= DYNAMIC_MAX:
        return {"applicable": False, "reason": "VMID is outside the disposable range", "vmid": vmid}
    if not {"kasm-malware", "evidence-scsi1"}.issubset(tags):
        return {"applicable": False, "reason": "missing malware evidence markers", "vmid": vmid}

    volume = str(config.get(EVIDENCE_SLOT, ""))
    match = SOURCE_PATTERN.match(volume)
    if not match or int(match.group(2)) != vmid:
        raise ValueError("evidence disk must be an ssd-lvm1 volume owned by the disposable VM")

    existing = {int(item) for item in state.get("existing_evidence_vmids", [])}
    evidence_vmid = next(
        (candidate for candidate in range(EVIDENCE_MIN, EVIDENCE_MAX + 1) if candidate not in existing),
        None,
    )
    if evidence_vmid is None:
        raise RuntimeError("evidence VMID range is exhausted")

    source_name = match.group(1)
    snapshot_name = f"vm-{evidence_vmid}-disk-0"
    return {
        "applicable": True,
        "vmid": vmid,
        "evidence_vmid": evidence_vmid,
        "source_lv": f"/dev/ssd-lvm1/{source_name}",
        "snapshot_lv": f"/dev/ssd-lvm1/{snapshot_name}",
        "snapshot_name": snapshot_name,
    }


def _qm_config(vmid: int) -> dict[str, str]:
    completed = subprocess.run(["qm", "config", str(vmid), "--current"], check=True, capture_output=True, text=True)
    config = {}
    for raw in completed.stdout.splitlines():
        if ": " in raw:
            key, value = raw.split(": ", 1)
            config[key] = value
    return config


def _existing_evidence_vmids() -> list[int]:
    completed = subprocess.run(
        ["lvs", "--noheadings", "-o", "lv_name", "ssd-lvm1"],
        check=True,
        capture_output=True,
        text=True,
    )
    result = []
    for line in completed.stdout.splitlines():
        match = re.fullmatch(r"vm-(63\d{2})-disk-\d+", line.strip())
        if match:
            result.append(int(match.group(1)))
    return result


def _existing_record(metadata_dir: Path, vmid: int, source_lv_uuid: str) -> dict | None:
    if not metadata_dir.exists():
        return None
    for path in metadata_dir.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if (
            int(record.get("source_vmid", -1)) == vmid
            and record.get("source_lv_uuid") == source_lv_uuid
        ):
            return record
    return None


def _lv_uuid(path: str) -> str:
    completed = subprocess.run(
        ["lvs", "--noheadings", "-o", "lv_uuid", path],
        check=True,
        capture_output=True,
        text=True,
    )
    value = completed.stdout.strip()
    if not value:
        raise RuntimeError(f"LVM returned no UUID for {path}")
    return value


def apply_retention(vmid: int, phase: str, metadata_dir: Path, lock_path: Path) -> dict:
    import fcntl

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        state = {
            "vmid": vmid,
            "phase": phase,
            "config": _qm_config(vmid),
            "existing_evidence_vmids": _existing_evidence_vmids(),
        }
        plan = plan_retention(state)
        if not plan["applicable"]:
            return plan
        source_lv_uuid = _lv_uuid(plan["source_lv"])
        existing_record = _existing_record(metadata_dir, vmid, source_lv_uuid)
        if existing_record:
            return {"applicable": True, "already_retained": True, **existing_record}

        subprocess.run(
            ["lvcreate", "--snapshot", "--name", plan["snapshot_name"], plan["source_lv"]],
            check=True,
        )
        subprocess.run(
            [
                "lvchange",
                "--addtag",
                "kasm_evidence",
                "--addtag",
                f"source_vmid_{vmid}",
                plan["snapshot_lv"],
            ],
            check=True,
        )
        verify = subprocess.run(
            ["lvs", "--noheadings", "-o", "lv_name,origin,lv_tags", plan["snapshot_lv"]],
            check=True,
            capture_output=True,
            text=True,
        )
        if plan["snapshot_name"] not in verify.stdout or "kasm_evidence" not in verify.stdout:
            raise RuntimeError("evidence snapshot verification failed")

        metadata_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "evidence_vmid": plan["evidence_vmid"],
            "source_vmid": vmid,
            "source_lv_uuid": source_lv_uuid,
            "volume": f"ssd-lvm1:{plan['snapshot_name']}",
            "created": datetime.now(timezone.utc).isoformat(),
            "sha256_manifest_status": "pending guest-side manifest validation",
        }
        metadata_path = metadata_dir / f"{plan['evidence_vmid']}.json"
        metadata_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        os.chmod(metadata_path, 0o600)
        return {"applicable": True, "already_retained": False, **record}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("vmid", type=int)
    parser.add_argument("phase")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--metadata-dir", type=Path, default=Path("/var/lib/kasm-lab/evidence"))
    parser.add_argument("--lock", type=Path, default=Path("/run/lock/kasm-evidence-retention.lock"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    if args.apply:
        result = apply_retention(args.vmid, args.phase, args.metadata_dir, args.lock)
    else:
        result = plan_retention(
            {
                "vmid": args.vmid,
                "phase": args.phase,
                "config": _qm_config(args.vmid),
                "existing_evidence_vmids": _existing_evidence_vmids(),
            }
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
