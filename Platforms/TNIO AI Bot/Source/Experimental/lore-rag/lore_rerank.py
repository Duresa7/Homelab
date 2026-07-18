"""GPT-as-judge reranker for lore retrieval candidates.

Replaces brittle BM25/vector ordering with a single LLM scoring pass.
One Codex call per rerank, batched up to RERANK_TOP_K candidates.
Cached by (corpus_version, question, candidate keys).
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Iterable

from lore_config import (
    ANSWER_TOP_K,
    RERANK_MIN_SCORE,
    RERANK_MODEL,
    RERANK_TIMEOUT_SECONDS,
    RERANK_TOP_K,
)


_RERANK_CACHE: dict[str, tuple[float, list[dict]]] = {}
_RERANK_TTL_SECONDS = 900


def _candidate_key(row: dict) -> str:
    return "|".join(
        str(row.get(k) or "")
        for k in ("source_id", "title", "section", "source_url", "path", "chunk_id")
    )


def _cache_key(corpus_version: str, question: str, rows: list[dict]) -> str:
    h = hashlib.sha1()
    h.update((corpus_version or "").encode("utf-8"))
    h.update(b"\x00")
    h.update(re.sub(r"\s+", " ", question.strip().lower()).encode("utf-8"))
    h.update(b"\x00")
    for row in rows:
        h.update(_candidate_key(row).encode("utf-8"))
        h.update(b"\x01")
    return h.hexdigest()


def _excerpt_for_prompt(row: dict, max_chars: int = 600) -> str:
    text = re.sub(r"\s+", " ", str(row.get("excerpt") or row.get("text") or "")).strip()
    return text[:max_chars]


def _build_prompt(question: str, rows: list[dict]) -> str:
    blocks = []
    for idx, row in enumerate(rows, start=1):
        title = row.get("title") or row.get("source_title") or "Untitled"
        section = row.get("section") or row.get("sheet_title") or row.get("path") or ""
        excerpt = _excerpt_for_prompt(row)
        blocks.append(
            f"[{idx}] TITLE: {title}\nSECTION: {section}\nEXCERPT: {excerpt}"
        )
    body = "\n\n".join(blocks)
    return (
        "You score lore-archive excerpts for usefulness in answering the user's question. "
        "Return JSON only, of the form {\"scores\":[{\"id\":1,\"score\":0-10,\"why\":\"\"}, ...]}. "
        "10 = excerpt directly answers the question for the named subject. "
        "7-9 = excerpt contains the key facts but for a related subject or section. "
        "4-6 = tangentially related, mentions topic but not the answer. "
        "0-3 = unrelated, wrong subject, or low signal. "
        "Penalize matches whose subject does not match the question's subject (e.g. a different character with a similar name). "
        "Be strict; multiple low scores are fine.\n\n"
        f"QUESTION: {question}\n\n"
        f"EXCERPTS:\n{body}\n\n"
        "JSON:"
    )


def _safe_json_object(text: str) -> dict:
    match = re.search(r"\{.*\}", text or "", re.S)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def rerank(
    question: str,
    rows: Iterable[dict],
    *,
    corpus_version: str = "",
    top_k: int = ANSWER_TOP_K,
    deadline: float | None = None,
    generate_text=None,
) -> list[dict]:
    """Score and reorder candidates by Codex relevance.

    `generate_text` is injected (from lore_mcp_server) so we don't import it
    at module load and create a circular import.
    """
    rows = [r for r in rows if isinstance(r, dict)][:RERANK_TOP_K]
    if not rows:
        return []
    if generate_text is None:
        return rows[:top_k]
    if deadline is not None and time.time() >= deadline - 1:
        return rows[:top_k]

    cache_key = _cache_key(corpus_version, question, rows)
    cached = _RERANK_CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _RERANK_TTL_SECONDS:
        return cached[1][:top_k]

    timeout = RERANK_TIMEOUT_SECONDS
    if deadline is not None:
        timeout = max(2, min(timeout, int(deadline - time.time())))
    try:
        raw = generate_text(
            _build_prompt(question, rows),
            num_predict=400,
            timeout=timeout,
            model=RERANK_MODEL,
        )
    except Exception:
        return rows[:top_k]

    parsed = _safe_json_object(raw)
    scores = parsed.get("scores") if isinstance(parsed.get("scores"), list) else []
    by_id: dict[int, float] = {}
    for entry in scores:
        if not isinstance(entry, dict):
            continue
        try:
            sid = int(entry.get("id"))
            sc = float(entry.get("score"))
        except (TypeError, ValueError):
            continue
        by_id[sid] = sc

    if not by_id:
        return rows[:top_k]

    annotated: list[tuple[float, int, dict]] = []
    for idx, row in enumerate(rows, start=1):
        score = by_id.get(idx, 0.0)
        if score < RERANK_MIN_SCORE:
            continue
        enriched = dict(row)
        enriched["rerank_score"] = score
        annotated.append((score, idx, enriched))

    annotated.sort(key=lambda t: (-t[0], t[1]))
    ordered = [row for _, _, row in annotated]

    if not ordered:
        # Everything filtered out — keep top-rated even if below threshold.
        ranked = sorted(
            ((by_id.get(i + 1, 0.0), i, r) for i, r in enumerate(rows)),
            key=lambda t: (-t[0], t[1]),
        )
        ordered = []
        for score, _, row in ranked:
            enriched = dict(row)
            enriched["rerank_score"] = score
            ordered.append(enriched)

    _RERANK_CACHE[(cache_key)] = (time.time(), ordered)
    return ordered[:top_k]
