#!/usr/bin/env python3
"""Knowledge graph extractor for the TNIO lore archive.

Runs Codex over each chunk in `state/chunks.jsonl` and asks it to extract
(subject, predicate, object) triples — relationships like:
  - Darth Reken → trained_by → Dread Master Dias Iroizi
  - Aiterian Revik → owns → Hssiss Yikazai
  - Praetorian Legion → uses → Forge Alchemy

Output is appended to `state/records/relationships.jsonl`, one triple per
line. Contains a doc-content-hash so re-runs skip docs we've already mined.

Designed to run as a one-shot or periodic background job (it's expensive —
each chunk = one Codex call). Not part of the per-5-min sync cycle.

Usage:
  python3 extract_relationships.py --rebuild      # re-extract everything
  python3 extract_relationships.py --incremental  # only new/changed chunks (default)
  python3 extract_relationships.py --limit 50     # cap chunks processed (testing)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/REDACTED_DEPLOYMENT_USER/lore-rag")

CHUNKS_PATH = Path("/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/chunks.jsonl")
RELATIONSHIPS_PATH = Path("/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/records/relationships.jsonl")
SEEN_PATH = Path("/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/records/relationships_seen.json")


def load_chunks() -> list[dict]:
    if not CHUNKS_PATH.exists():
        return []
    out = []
    with CHUNKS_PATH.open(encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def load_seen() -> dict:
    if not SEEN_PATH.exists():
        return {}
    try:
        return json.loads(SEEN_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_seen(seen: dict) -> None:
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SEEN_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(seen, ensure_ascii=False), encoding="utf-8")
    tmp.replace(SEEN_PATH)


_TRIPLE_PROMPT = (
    "You are mining a TNIO Sith Empire lore archive for structured "
    "knowledge-graph triples. Read the excerpt and extract distinct "
    "relationships as JSON in this exact shape:\n"
    "{\"triples\": [{\"subject\": \"...\", \"predicate\": \"...\", \"object\": \"...\"}, ...]}\n\n"
    "Rules:\n"
    "  • Use canonical names. \"Darth Reken\" not \"he\" or \"Reken's\".\n"
    "  • Predicates are short snake_case verbs/relations. Examples: trained_by, "
    "apprentice_of, master_of, owns, commands, located_on, member_of, "
    "title_held, allied_with, opposed_by, born_on, killed_by, founded, "
    "specializes_in, uses, forges, contains, ruled_by.\n"
    "  • Only extract relationships the text actually states. Don't speculate.\n"
    "  • Skip generic facts (\"Sith are dark side\"). Focus on named subjects.\n"
    "  • If nothing concrete is in the excerpt, return {\"triples\": []}.\n"
    "  • At most 12 triples per excerpt.\n\n"
    "EXCERPT:\n{excerpt}\n\nJSON:"
)


class CodexTimeout(Exception):
    """Raised so the caller can distinguish 'transient — retry next pass' from
    'parsed but found nothing'."""


def extract_for_chunk(chunk: dict, generate_text_fn, model: str) -> list[dict]:
    text = (chunk.get("text") or "").strip()
    if not text or len(text) < 80:
        return []
    # Shorter excerpt = faster Codex response. 1600 chars covers most
    # paragraphs without blowing past the timeout.
    prompt = _TRIPLE_PROMPT.replace("{excerpt}", text[:1600])
    try:
        raw = generate_text_fn(prompt, num_predict=380, timeout=35, model=model)
    except Exception as exc:
        # Surface timeouts so the caller can avoid marking the chunk 'seen'
        # and retry on a future pass.
        msg = str(exc)
        if "timed out" in msg.lower() or "timeout" in msg.lower():
            raise CodexTimeout(msg)
        print(f"  codex error: {exc}", flush=True)
        return []
    if not raw:
        return []
    m = re.search(r"\{.*\"triples\".*\}", raw, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except Exception:
        return []
    raw_triples = data.get("triples") or []
    if not isinstance(raw_triples, list):
        return []
    out = []
    for t in raw_triples[:12]:
        if not isinstance(t, dict):
            continue
        s = str(t.get("subject") or "").strip()
        p = str(t.get("predicate") or "").strip().lower()
        o = str(t.get("object") or "").strip()
        if not s or not p or not o or len(s) < 2 or len(o) < 2:
            continue
        if len(s) > 120 or len(o) > 200:
            continue
        out.append({
            "subject": s,
            "predicate": p,
            "object": o,
            "source_title": chunk.get("metadata", {}).get("name") or "",
            "source_url": chunk.get("metadata", {}).get("webViewLink") or "",
            "chunk_id": chunk.get("chunk_id"),
            "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract relationship triples from the TNIO archive.")
    parser.add_argument("--rebuild", action="store_true", help="ignore the seen-cache and reprocess all chunks")
    parser.add_argument("--incremental", action="store_true", help="only process chunks not yet seen (default behaviour)")
    parser.add_argument("--limit", type=int, default=0, help="stop after N chunks (testing)")
    parser.add_argument("--model", default="openai-codex/gpt-5.4-mini", help="LLM model to use")
    args = parser.parse_args()

    from lore_mcp_server import generate_text  # noqa: E402

    chunks = load_chunks()
    print(f"loaded {len(chunks)} chunks", flush=True)
    seen = {} if args.rebuild else load_seen()

    if args.rebuild and RELATIONSHIPS_PATH.exists():
        backup = RELATIONSHIPS_PATH.with_suffix(f".jsonl.bak.{int(time.time())}")
        RELATIONSHIPS_PATH.rename(backup)
        print(f"rebuilding — moved old triples to {backup}", flush=True)

    RELATIONSHIPS_PATH.parent.mkdir(parents=True, exist_ok=True)

    processed = 0
    new_triples = 0
    t0 = time.time()
    with RELATIONSHIPS_PATH.open("a", encoding="utf-8") as out:
        for i, chunk in enumerate(chunks):
            cid = chunk.get("chunk_id")
            content_hash = chunk.get("metadata", {}).get("contentHash") or ""
            seen_key = f"{cid}::{content_hash}"
            if not args.rebuild and seen.get(seen_key):
                continue

            try:
                triples = extract_for_chunk(chunk, generate_text, args.model)
            except CodexTimeout:
                # Don't mark as seen — try again on the next run.
                processed += 1
                continue
            for triple in triples:
                out.write(json.dumps(triple, ensure_ascii=False) + "\n")
            out.flush()
            new_triples += len(triples)
            seen[seen_key] = True
            processed += 1
            if processed % 10 == 0:
                elapsed = time.time() - t0
                rate = processed / max(0.01, elapsed)
                print(f"  [{processed} chunks, {new_triples} triples, {rate:.1f} chunks/s, {elapsed:.0f}s]", flush=True)
                save_seen(seen)
            if args.limit and processed >= args.limit:
                print(f"hit --limit {args.limit}, stopping", flush=True)
                break

    save_seen(seen)
    elapsed = time.time() - t0
    print(f"done — processed {processed} chunks, extracted {new_triples} triples in {elapsed:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
