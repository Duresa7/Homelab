#!/usr/bin/env python3
"""Create an integrity-checked SQLite backup without reading secret values."""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path


def read_only_uri(path: Path) -> str:
    return f"file:{path.resolve().as_posix()}?mode=ro"


def integrity_result(connection: sqlite3.Connection) -> str:
    row = connection.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "no result"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a new SQLite online backup and verify its integrity."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    source = args.source.resolve()
    destination = args.destination.resolve()
    if not source.is_file():
        parser.error(f"source is not a file: {source}")
    if not destination.parent.is_dir():
        parser.error(f"destination directory does not exist: {destination.parent}")

    try:
        try:
            descriptor = os.open(
                destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
            )
        except FileExistsError:
            parser.error(f"destination already exists: {destination}")
        else:
            os.close(descriptor)
        with sqlite3.connect(read_only_uri(source), uri=True) as live:
            with sqlite3.connect(destination) as backup:
                live.backup(backup)
        os.chmod(destination, 0o600)
        with sqlite3.connect(read_only_uri(destination), uri=True) as backup:
            result = integrity_result(backup)
        if result != "ok":
            raise RuntimeError(f"backup integrity check failed: {result}")
    except Exception:
        if destination.exists():
            destination.unlink()
        raise

    print(f"backup-created={destination}")
    print("sqlite-integrity=ok")
    print("mode=0600")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
