#!/usr/bin/env python3
"""Pre-warm the AGENT_ANSWER_CACHE with the most-asked questions.

Reads the agent-requests.log, picks the N most-frequent unique questions
from the last 14 days, and runs each one through the live HTTP /agent-answer
endpoint. Successful responses get cached (and now persisted) so they serve
instantly the next time a user asks them.

Usage:
  python3 agent_warmup.py [--top N] [--days D] [--max-seconds S]

Designed to be run from a systemd timer at low-traffic times (e.g. 4 AM).
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path

LOG_PATH = Path("/home/REDACTED_DEPLOYMENT_USER/lore-rag/logs/agent-requests.log")
HTTP_ENDPOINT = "http://127.0.0.1:19731/agent-answer"


def collect_top_questions(days: int, top: int) -> list[tuple[str, int]]:
    cutoff = time.time() - days * 86400
    counts: Counter[str] = Counter()
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts_str = d.get("ts") or ""
            try:
                # Best-effort timestamp parse — log uses ISO-8601 with offset.
                from datetime import datetime
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
            except Exception:
                continue
            if ts < cutoff:
                continue
            mode = d.get("mode")
            if mode != "archive":
                continue  # don't warm persona/backend_refusal — they're cheap anyway
            if d.get("best_effort"):
                continue  # don't warm bad answers
            q = (d.get("query") or "").strip()
            if not q or len(q) > 240:
                continue
            counts[q.lower()] += 1
    # Sort by frequency, take top.
    return counts.most_common(top)


def warm_one(query: str, max_seconds: int) -> tuple[bool, int]:
    payload = json.dumps({"query": query, "max_seconds": max_seconds}).encode("utf-8")
    req = urllib.request.Request(
        HTTP_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=max_seconds + 10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        elapsed_ms = int((time.time() - t0) * 1000)
        if data.get("best_effort"):
            return False, elapsed_ms
        return True, elapsed_ms
    except urllib.error.URLError:
        return False, int((time.time() - t0) * 1000)
    except Exception:
        return False, int((time.time() - t0) * 1000)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-warm the agent-answer cache.")
    parser.add_argument("--top", type=int, default=30, help="warm the top-N most-asked questions (default: 30)")
    parser.add_argument("--days", type=int, default=14, help="look back N days in the request log (default: 14)")
    parser.add_argument("--max-seconds", type=int, default=50, help="per-query timeout (default: 50)")
    parser.add_argument("--list-only", action="store_true", help="just print what would be warmed")
    args = parser.parse_args()

    top_qs = collect_top_questions(args.days, args.top)
    if not top_qs:
        print("[warmup] no questions to warm")
        return 0

    print(f"[warmup] selected {len(top_qs)} questions over the last {args.days} days")
    if args.list_only:
        for q, n in top_qs:
            print(f"  {n:3d}× {q}")
        return 0

    succeeded = 0
    started_at = time.time()
    for i, (q, n) in enumerate(top_qs, start=1):
        print(f"[warmup] {i}/{len(top_qs)} ({n}× asked) — {q[:80]}", flush=True)
        ok, ms = warm_one(q, args.max_seconds)
        status = "OK" if ok else "skipped"
        print(f"           -> {status} in {ms}ms", flush=True)
        if ok:
            succeeded += 1

    elapsed = int(time.time() - started_at)
    print(f"[warmup] done — {succeeded}/{len(top_qs)} succeeded in {elapsed}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
