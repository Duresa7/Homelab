#!/usr/bin/env python3
"""Compare secret-safe Semaphore structure and verify SQLite integrity."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


SAFE_COLUMNS: dict[str, tuple[str, ...]] = {
    "project": ("id", "name", "type", "default_secret_storage_id"),
    "project__environment": ("id", "project_id", "name", "secret_storage_id"),
    "project__inventory": (
        "id",
        "project_id",
        "type",
        "inventory",
        "ssh_key_id",
        "name",
        "become_key_id",
        "repository_id",
        "runner_tag",
    ),
    "project__repository": (
        "id",
        "project_id",
        "git_url",
        "ssh_key_id",
        "name",
        "git_branch",
    ),
    "project__template": (
        "id",
        "project_id",
        "inventory_id",
        "repository_id",
        "playbook",
        "name",
        "type",
        "view_id",
        "app",
        "git_branch",
        "runner_tag",
    ),
    "project__view": (
        "id",
        "title",
        "project_id",
        "position",
        "hidden",
        "type",
        "filter",
        "sort_column",
        "sort_reverse",
    ),
    "access_key": (
        "id",
        "name",
        "type",
        "project_id",
        "environment_id",
        "user_id",
        "owner",
        "storage_id",
        "source_storage_id",
        "source_storage_key",
        "source_storage_type",
    ),
}


def connect_read_only(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def safe_snapshot(connection: sqlite3.Connection) -> dict[str, list[list[Any]]]:
    snapshot: dict[str, list[list[Any]]] = {}
    for table, columns in SAFE_COLUMNS.items():
        available = {
            row[1] for row in connection.execute(f"PRAGMA table_info({table})")
        }
        selected = tuple(column for column in columns if column in available)
        if not selected:
            snapshot[table] = []
            continue
        query = f"SELECT {', '.join(selected)} FROM {table} ORDER BY {selected[0]}"
        snapshot[table] = [list(row) for row in connection.execute(query)]
    return snapshot


def encrypted_key_records(connection: sqlite3.Connection) -> dict[int, bytes | str | None]:
    return {
        int(row[0]): row[1]
        for row in connection.execute("SELECT id, secret FROM access_key ORDER BY id")
    }


def environment_payloads(connection: sqlite3.Connection) -> dict[int, tuple[Any, ...]]:
    return {
        int(row[0]): tuple(row[1:])
        for row in connection.execute(
            "SELECT id, password, json, env FROM project__environment ORDER BY id"
        )
    }


def integrity_result(connection: sqlite3.Connection) -> str:
    row = connection.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "no result"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify live Semaphore state against a pre-change SQLite backup."
    )
    parser.add_argument("live_database", type=Path)
    parser.add_argument("backup_database", type=Path)
    args = parser.parse_args()

    with connect_read_only(args.live_database) as live:
        live_integrity = integrity_result(live)
        live_snapshot = safe_snapshot(live)
        live_keys = encrypted_key_records(live)
        live_environment_payloads = environment_payloads(live)
        template_environment_links = live.execute(
            "SELECT count(*) FROM project__template_environment"
        ).fetchone()[0]
    with connect_read_only(args.backup_database) as backup:
        backup_integrity = integrity_result(backup)
        backup_snapshot = safe_snapshot(backup)
        backup_keys = encrypted_key_records(backup)
        backup_environment_payloads = environment_payloads(backup)

    structure_matches = live_snapshot == backup_snapshot
    encrypted_keys_match = live_keys == backup_keys and bool(live_keys)
    environments_match = (
        live_environment_payloads == backup_environment_payloads
        and bool(live_environment_payloads)
    )
    counts = {
        table: len(rows)
        for table, rows in live_snapshot.items()
        if table in {"project", "project__template", "project__view", "access_key"}
    }

    print(f"live-sqlite-integrity={live_integrity}")
    print(f"backup-sqlite-integrity={backup_integrity}")
    print(f"safe-structure-unchanged={str(structure_matches).lower()}")
    print(f"encrypted-key-records-unchanged={str(encrypted_keys_match).lower()}")
    print(f"environment-payloads-unchanged={str(environments_match).lower()}")
    print(f"template-environment-links={template_environment_links}")
    print(f"object-counts={json.dumps(counts, sort_keys=True)}")

    if live_integrity != "ok" or backup_integrity != "ok":
        return 1
    if not structure_matches or not encrypted_keys_match or not environments_match:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
