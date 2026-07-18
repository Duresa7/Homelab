"""Tool catalog for the LLM-driven lore agent.

Each tool takes simple JSON-friendly arguments and returns a list of compact
dicts with `{title, section, excerpt, ...}`. The agent presents this catalog to
Codex, which decides which tools to call (and with what args) before answering.

Design principles:
  - Functions are deterministic and side-effect-free.
  - Returned data is small and uniform (LLM-friendly): title, section, excerpt.
  - Heavy lifting (BM25, vector, structured records) is delegated to the
    existing primitives in lore_mcp_server / lore_records — these tools are
    composition wrappers, not new search algorithms.
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Callable


# --------------------------------------------------------------------------- #
# Tool: search_archive
# --------------------------------------------------------------------------- #


def tool_search_archive(
    query: str,
    *,
    limit: int = 10,
    lore_search_fn: Callable,
    fallback_plan_fn: Callable,
    compact_source_fn: Callable,
) -> list[dict]:
    """Broad search over chunks + structured records.

    The same engine the agent already uses for its main retrieval pass, exposed
    so the LLM can re-query with refined wording when its first pass was too
    narrow or wrong-subject-locked.
    """
    plan = fallback_plan_fn(query)
    try:
        res = lore_search_fn(query, limit=max(4, min(int(limit), 14)), plan=plan)
    except Exception:
        return []
    rows = res.get("results") if isinstance(res, dict) else []
    out = []
    for idx, row in enumerate((rows or [])[:limit], start=1):
        out.append(compact_source_fn(row, idx))
    return out


# --------------------------------------------------------------------------- #
# Tool: look_up_subject
# --------------------------------------------------------------------------- #


def tool_look_up_subject(
    name: str,
    *,
    search_records_tool: Callable,
    compact_source_fn: Callable,
) -> list[dict]:
    """Find structured records and chunks whose name/alias matches `name`.

    Use when the user names a specific subject (character, faction, planet,
    document) and you want the *primary* dossier — not noisy adjacent matches.
    Returns at most 8 closely-matching candidates.
    """
    n = (name or "").strip()
    if not n:
        return []
    try:
        rows = search_records_tool(n, limit=8) or []
    except Exception:
        rows = []
    nlow = n.lower()
    # Prioritize rows whose title/section/excerpt explicitly mentions the name.
    primary = []
    secondary = []
    for r in rows:
        haystack = (
            (r.get("title") or "") + " " +
            (r.get("section") or "") + " " +
            (r.get("excerpt") or "")
        ).lower()
        (primary if nlow in haystack else secondary).append(r)
    ordered = primary + secondary
    out = []
    for idx, row in enumerate(ordered[:8], start=1):
        out.append(compact_source_fn(row, idx))
    return out


# --------------------------------------------------------------------------- #
# Tool: read_doc
# --------------------------------------------------------------------------- #


def tool_read_doc(
    doc_title: str,
    query: str = "",
    *,
    lore_search_fn: Callable,
    fallback_plan_fn: Callable,
    compact_source_fn: Callable,
) -> list[dict]:
    """Fetch sections of a specific doc, optionally filtered by `query`.

    Use when you know which doc has the answer (e.g. "TNIO: Codex of Planets"
    for a housing question) and want to pull its content directly rather than
    relying on broad-search ranking. If `query` is empty, returns the doc's
    most-representative chunks.
    """
    d = (doc_title or "").strip()
    if not d:
        return []
    plan = fallback_plan_fn(query or doc_title)
    plan = {**plan, "source_hints": [d]}
    search_query = query.strip() or doc_title
    try:
        res = lore_search_fn(search_query, limit=12, plan=plan)
    except Exception:
        return []
    rows = res.get("results") if isinstance(res, dict) else []
    # Filter to this doc only.
    d_lower = d.lower()
    matched = [
        r for r in (rows or [])
        if d_lower in (r.get("title") or "").lower()
    ]
    out = []
    for idx, row in enumerate(matched[:8], start=1):
        out.append(compact_source_fn(row, idx))
    return out


# --------------------------------------------------------------------------- #
# Tool: list_records
# --------------------------------------------------------------------------- #


_RECORDS_DIR = Path("/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/records")


def tool_list_records(
    kind: str,
    contains: str = "",
    *,
    compact_source_fn: Callable,
) -> list[dict]:
    """List records of a given kind, optionally filtered by substring.

    `kind` is one of: entities, assets, planets, rules, rosters.
    `contains` filters records whose name or fields contain that substring.
    Use this for catalog-style questions: "list all dark councilors", "what
    planets are imperial-controlled", "what rules govern combat", etc.
    Returns up to 12 matching records.
    """
    kind = (kind or "").strip().lower()
    if kind not in {"entities", "assets", "planets", "rules", "rosters"}:
        return []
    path = _RECORDS_DIR / f"{kind}.jsonl"
    if not path.exists():
        return []
    needle = (contains or "").strip().lower()
    matches: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            blob = (
                str(rec.get("name") or "") + " " +
                " ".join(rec.get("aliases") or []) + " " +
                str(rec.get("summary") or "") + " " +
                " ".join(str(v) for v in (rec.get("fields") or {}).values())
            ).lower()
            if needle and needle not in blob:
                continue
            matches.append(rec)
            if len(matches) >= 50:  # hard cap — we'll trim further below
                break
    except Exception:
        return []
    # Convert to the same shape the agent expects.
    out = []
    for idx, rec in enumerate(matches[:12], start=1):
        excerpt = (rec.get("summary") or "") + (
            "\n" + "\n".join(f"{k}: {v}" for k, v in (rec.get("fields") or {}).items())
            if rec.get("fields") else ""
        )
        row = {
            "title": rec.get("source", {}).get("title") or rec.get("name"),
            "section": rec.get("name"),
            "excerpt": excerpt[:600],
            "source_url": rec.get("source", {}).get("webViewLink"),
            "record_type": rec.get("record_type"),
            "match_type": "list_records",
        }
        out.append(compact_source_fn(row, idx))
    return out


# --------------------------------------------------------------------------- #
# Tool: find_relationships — knowledge-graph triple lookup
# --------------------------------------------------------------------------- #


_RELATIONSHIPS_PATH = Path("/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/records/relationships.jsonl")
_RELATIONSHIPS_LOCK = threading.Lock()
_RELATIONSHIPS_CACHE: list[dict] | None = None
_RELATIONSHIPS_CACHE_MTIME: float = 0.0


def _load_relationships() -> list[dict]:
    """Load and cache the relationships triples file. Re-reads on mtime change."""
    global _RELATIONSHIPS_CACHE, _RELATIONSHIPS_CACHE_MTIME
    try:
        mtime = _RELATIONSHIPS_PATH.stat().st_mtime
    except Exception:
        return _RELATIONSHIPS_CACHE or []
    if _RELATIONSHIPS_CACHE is not None and mtime == _RELATIONSHIPS_CACHE_MTIME:
        return _RELATIONSHIPS_CACHE
    with _RELATIONSHIPS_LOCK:
        if _RELATIONSHIPS_CACHE is not None and mtime == _RELATIONSHIPS_CACHE_MTIME:
            return _RELATIONSHIPS_CACHE
        out: list[dict] = []
        try:
            with _RELATIONSHIPS_PATH.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            return _RELATIONSHIPS_CACHE or []
        _RELATIONSHIPS_CACHE = out
        _RELATIONSHIPS_CACHE_MTIME = mtime
        return out


def tool_find_relationships(
    subject: str,
    predicate: str = "",
    *,
    compact_source_fn: Callable,
) -> list[dict]:
    """Look up knowledge-graph relationships involving a subject.

    Returns triples like (Darth Reken, trained_by, Dread Master Dias Iroizi)
    — extracted from the corpus by `extract_relationships.py`.

    Use for relational questions: "who trained Reken?", "what ships does
    Aiterian command?", "who is in the Praetorian Legion?". This tool gives
    sharp factual answers when the relationship has been mined; falls back
    silently to empty when the graph hasn't been populated.
    """
    s = (subject or "").strip().lower()
    if not s or len(s) < 2:
        return []
    p_filter = (predicate or "").strip().lower()
    triples = _load_relationships()
    if not triples:
        return []
    matches: list[dict] = []
    for t in triples:
        subj = (t.get("subject") or "").lower()
        obj = (t.get("object") or "").lower()
        pred = (t.get("predicate") or "").lower()
        # Match if subject or object contains the search term — relationships
        # work both directions ("who trained X" and "who did X train").
        if s not in subj and s not in obj:
            continue
        if p_filter and p_filter not in pred:
            continue
        matches.append(t)
        if len(matches) >= 30:
            break
    if not matches:
        return []
    # Group identical triples (same subj/pred/obj) so duplicates collapse.
    seen_keys: set[tuple[str, str, str]] = set()
    unique: list[dict] = []
    for t in matches:
        key = (t.get("subject", ""), t.get("predicate", ""), t.get("object", ""))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique.append(t)

    # Format as agent-source rows so the answerer can ingest them like any
    # other retrieval result.
    out: list[dict] = []
    for i, t in enumerate(unique[:12], start=1):
        excerpt = f"{t.get('subject')} — {t.get('predicate')} — {t.get('object')}"
        row = {
            "title": t.get("source_title") or "Knowledge Graph",
            "section": t.get("predicate") or "relationship",
            "source_url": t.get("source_url") or "",
            "excerpt": excerpt,
            "match_type": "relationship",
        }
        out.append(compact_source_fn(row, i))
    return out


# --------------------------------------------------------------------------- #
# Tool: term_sweep — exhaustive literal-substring sweep with wide context
# --------------------------------------------------------------------------- #


_CHUNKS_PATH = Path("/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/chunks.jsonl")
_CHUNKS_CACHE_LOCK = threading.Lock()
_CHUNKS_CACHE: dict | None = None  # {file_id: [(ordinal_or_None, chunk_dict), ...] sorted by ordinal}
_CHUNKS_CACHE_MTIME: float = 0.0


def _load_chunks_index() -> dict:
    """Load and cache the chunks corpus, indexed by file_id, sorted by ordinal.

    Re-reads if chunks.jsonl mtime changes (so a re-sync invalidates).
    """
    global _CHUNKS_CACHE, _CHUNKS_CACHE_MTIME
    try:
        mtime = _CHUNKS_PATH.stat().st_mtime
    except Exception:
        return _CHUNKS_CACHE or {}
    if _CHUNKS_CACHE is not None and mtime == _CHUNKS_CACHE_MTIME:
        return _CHUNKS_CACHE
    with _CHUNKS_CACHE_LOCK:
        if _CHUNKS_CACHE is not None and mtime == _CHUNKS_CACHE_MTIME:
            return _CHUNKS_CACHE
        idx: dict[str, list] = {}
        try:
            with _CHUNKS_PATH.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    cid = rec.get("chunk_id") or ""
                    meta = rec.get("metadata") or {}
                    fid = meta.get("file_id") or ""
                    if not fid:
                        continue
                    parts = cid.split(":")
                    ordinal = None
                    if len(parts) >= 3:
                        try:
                            ordinal = int(parts[1])
                        except Exception:
                            ordinal = None
                    idx.setdefault(fid, []).append((ordinal, rec))
            # Sort each doc's chunks by ordinal. Non-int ordinals (sheet rows)
            # sort to the end in their file_id-relative order.
            BIG = 10**9
            for fid in idx:
                # Track stable order for non-int ordinals (preserve file order).
                lst = idx[fid]
                # Stable sort: int ordinals first, then non-int in original order.
                int_items = [(o, r) for o, r in lst if isinstance(o, int)]
                noni_items = [(o, r) for o, r in lst if not isinstance(o, int)]
                int_items.sort(key=lambda t: t[0])
                idx[fid] = int_items + noni_items
        except Exception:
            return _CHUNKS_CACHE or {}
        _CHUNKS_CACHE = idx
        _CHUNKS_CACHE_MTIME = mtime
        return idx


def tool_term_sweep(
    terms: list[str] | str,
    *,
    window_paragraphs: int = 4,
    compact_source_fn: Callable,
) -> list[dict]:
    """Exhaustive literal-substring sweep across every chunk in the archive.

    For each term, finds every chunk that literally contains it (case-
    insensitive substring), and returns a wide window (~`window_paragraphs`
    of context) around each hit by including neighbor chunks. NO per-doc
    cap — every doc that mentions a term contributes. Adjacent hits in the
    same doc are merged so overlapping context isn't repeated.

    Returns a list of long-form windows. The agent's sift pass (LLM-as-judge)
    decides which windows are actually relevant before the final answer.

    Use when:
      - The user's question has distinctive terms and the right answer might
        live in a doc the ranker is missing.
      - You want exhaustive recall instead of top-K.
      - Catalog/list questions ("every doc that mentions X").

    Avoid for common words ('rule', 'is') — prefer distinctive terms.
    """
    if isinstance(terms, str):
        terms = [terms]
    norm: list[str] = []
    for t in (terms or []):
        s = (t or "").strip()
        if s and len(s) >= 2:
            norm.append(s)
    if not norm:
        return []

    radius = max(1, int(window_paragraphs or 4) // 2)

    idx = _load_chunks_index()
    if not idx:
        return []

    lows = [(t, t.lower()) for t in norm]

    out: list[dict] = []
    for fid, lst in idx.items():
        # Find every position in this doc's chunk list that matches any term.
        hit_positions: list[tuple[int, set[str]]] = []  # (position_in_lst, terms_at_hit)
        for i, (_, rec) in enumerate(lst):
            text_low = (rec.get("text") or "").lower()
            if not text_low:
                continue
            hit_terms: set[str] = set()
            for orig, low in lows:
                if low in text_low:
                    hit_terms.add(orig)
            if hit_terms:
                hit_positions.append((i, hit_terms))
        if not hit_positions:
            continue

        # Merge adjacent / overlapping windows so we don't repeat context.
        # Each merged window: (start_idx, end_idx, anchor_terms_set)
        windows: list[tuple[int, int, set[str]]] = []
        for pos, hterms in hit_positions:
            ws = max(0, pos - radius)
            we = min(len(lst) - 1, pos + radius)
            if windows and ws <= windows[-1][1] + 1:
                p_s, p_e, p_t = windows[-1]
                windows[-1] = (p_s, max(p_e, we), p_t | hterms)
            else:
                windows.append((ws, we, set(hterms)))

        # Build a row per window.
        for ws, we, win_terms in windows:
            chunks_in_window = lst[ws : we + 1]
            if not chunks_in_window:
                continue
            texts: list[str] = []
            for (_, rec) in chunks_in_window:
                t = (rec.get("text") or "").strip()
                if t:
                    texts.append(t)
            if not texts:
                continue
            excerpt = "\n\n".join(texts)

            first_meta = chunks_in_window[0][1].get("metadata") or {}
            section = first_meta.get("section") or first_meta.get("path") or ""
            row = {
                "title": first_meta.get("name") or "Untitled",
                "section": section,
                "source_url": first_meta.get("webViewLink"),
                "path": first_meta.get("path"),
                "excerpt": excerpt,
                "match_type": "term_sweep",
                "anchor_terms": sorted(win_terms),
                "file_id": fid,
            }
            out.append(row)

    # Hand each row through compact_source_fn with a fat excerpt cap so the
    # sift pass / answerer get enough context to judge.
    formatted: list[dict] = []
    for i, row in enumerate(out, start=1):
        try:
            compact = compact_source_fn(row, i, max_excerpt=4500)
        except TypeError:
            # compact_source_fn might not accept max_excerpt — fall back.
            compact = compact_source_fn(row, i)
        # Preserve our extra fields that compact_source may have dropped.
        compact["match_type"] = "term_sweep"
        compact["anchor_terms"] = row["anchor_terms"]
        formatted.append(compact)
    return formatted


# --------------------------------------------------------------------------- #
# Tool registry — schema shown to the planning LLM
# --------------------------------------------------------------------------- #


TOOL_CATALOG = [
    {
        "name": "search_archive",
        "args": {"query": "string", "limit": "int (default 10, max 14)"},
        "purpose": (
            "Broad keyword + vector search across the TNIO Drive (chunks + "
            "records). Use when the question is open-ended or you want a wide "
            "candidate sweep. Use specific terms; avoid filler words."
        ),
        "example": '{"name":"search_archive","args":{"query":"praetorian forge alchemy","limit":8}}',
    },
    {
        "name": "look_up_subject",
        "args": {"name": "string"},
        "purpose": (
            "Direct lookup by exact subject name (character, doc, faction). "
            "Returns that subject's primary dossier records. Use when the "
            "user names a specific subject and you want THE record, not "
            "noisy adjacent matches."
        ),
        "example": '{"name":"look_up_subject","args":{"name":"Darth Reken"}}',
    },
    {
        "name": "read_doc",
        "args": {"doc_title": "string", "query": "string (optional)"},
        "purpose": (
            "Read sections from a specific doc by title. Use when you know "
            "which doc holds the answer (e.g. TNIO: Codex of Planets for a "
            "planet question, or TNIO Guild Rules for a rules question) and "
            "want its content directly."
        ),
        "example": '{"name":"read_doc","args":{"doc_title":"TNIO: Codex of Planets","query":"player housing"}}',
    },
    {
        "name": "list_records",
        "args": {
            "kind": "entities|assets|planets|rules|rosters",
            "contains": "string (optional substring filter)",
        },
        "purpose": (
            "Catalog/list questions: enumerate all records of a kind. Use for "
            "'who is in X faction', 'what planets are imperial', 'what rules "
            "govern Y', etc. Returns up to 12 matching records."
        ),
        "example": '{"name":"list_records","args":{"kind":"rosters","contains":"Dark Councilor"}}',
    },
    {
        "name": "find_relationships",
        "args": {
            "subject": "string (a character/faction/place name)",
            "predicate": "string (optional: filter by relation type, e.g. 'trained_by', 'commands', 'owns')",
        },
        "purpose": (
            "Knowledge-graph lookup. Returns structured (subject → predicate "
            "→ object) triples mined from the archive. Use for relational "
            "questions: 'who trained Reken', 'what ships does Aiterian command', "
            "'who's in the Praetorian Legion', 'who killed X', 'where is Y "
            "located'. Sharp factual answers when the graph is populated; "
            "returns empty if the relationship hasn't been mined — fall back "
            "to look_up_subject or term_sweep in that case."
        ),
        "example": '{"name":"find_relationships","args":{"subject":"Darth Reken","predicate":"trained_by"}}',
    },
    {
        "name": "term_sweep",
        "args": {
            "terms": "list of strings (specific keywords/phrases)",
            "window_paragraphs": "int (default 4, range 2-8)",
        },
        "purpose": (
            "EXHAUSTIVE literal-substring sweep across every chunk in the "
            "archive. For each term, finds every doc/chunk that literally "
            "contains it and returns a wide window (~4 paragraphs of context) "
            "around each hit. NO per-doc cap — every match contributes. Use "
            "when ranking might be missing the right doc, when phrasing "
            "variation hides the literal hit, or for catalog questions ('every "
            "mention of X'). Pick DISTINCTIVE terms (proper nouns, jargon, "
            "compound concepts) — common words like 'rule' or 'is' will return "
            "too much. The agent will sift the results before answering."
        ),
        "example": '{"name":"term_sweep","args":{"terms":["Praetorian","kyber forge"],"window_paragraphs":4}}',
    },
]


def format_tool_catalog_for_prompt() -> str:
    lines = []
    for tool in TOOL_CATALOG:
        lines.append(f"  • {tool['name']}({', '.join(tool['args'].keys())})")
        lines.append(f"      {tool['purpose']}")
        lines.append(f"      example: {tool['example']}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Tool dispatcher — runs a single tool call against bound primitives
# --------------------------------------------------------------------------- #


def run_tool(
    name: str,
    args: dict,
    *,
    lore_search_fn: Callable,
    fallback_plan_fn: Callable,
    compact_source_fn: Callable,
    search_records_tool: Callable,
) -> list[dict]:
    """Execute a single tool call. Returns rows or [] on error."""
    name = (name or "").strip()
    args = args or {}
    try:
        if name == "search_archive":
            return tool_search_archive(
                str(args.get("query") or ""),
                limit=int(args.get("limit") or 10),
                lore_search_fn=lore_search_fn,
                fallback_plan_fn=fallback_plan_fn,
                compact_source_fn=compact_source_fn,
            )
        if name == "look_up_subject":
            return tool_look_up_subject(
                str(args.get("name") or ""),
                search_records_tool=search_records_tool,
                compact_source_fn=compact_source_fn,
            )
        if name == "read_doc":
            return tool_read_doc(
                str(args.get("doc_title") or ""),
                str(args.get("query") or ""),
                lore_search_fn=lore_search_fn,
                fallback_plan_fn=fallback_plan_fn,
                compact_source_fn=compact_source_fn,
            )
        if name == "list_records":
            return tool_list_records(
                str(args.get("kind") or ""),
                str(args.get("contains") or ""),
                compact_source_fn=compact_source_fn,
            )
        if name == "find_relationships":
            return tool_find_relationships(
                str(args.get("subject") or ""),
                str(args.get("predicate") or ""),
                compact_source_fn=compact_source_fn,
            )
        if name == "term_sweep":
            raw_terms = args.get("terms") or []
            if isinstance(raw_terms, str):
                raw_terms = [raw_terms]
            terms_list = [str(t) for t in (raw_terms or []) if str(t).strip()]
            wp = args.get("window_paragraphs") or 4
            try:
                wp_int = int(wp)
            except Exception:
                wp_int = 4
            return tool_term_sweep(
                terms_list,
                window_paragraphs=wp_int,
                compact_source_fn=compact_source_fn,
            )
    except Exception:
        return []
    return []


# --------------------------------------------------------------------------- #
# Tool-call parsing
# --------------------------------------------------------------------------- #


_JSON_BLOCK_RE = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", re.S)


def parse_tool_calls(raw: str) -> list[dict]:
    """Extract `[{name, args}, ...]` from the planning LLM's response.

    Accepts either `{"tools":[...]}` or `[{...},{...}]` or a single `{...}`.
    Defensive against extra prose around the JSON.
    """
    if not raw:
        return []
    raw = raw.strip()
    # Try to find the first balanced JSON object/array.
    m = re.search(r"(\{.*\}|\[.*\])", raw, re.S)
    if not m:
        return []
    blob = m.group(1)
    try:
        data = json.loads(blob)
    except Exception:
        # Tolerate trailing commas / unclosed braces — find any inner JSON object.
        data = None
        for sub in _JSON_BLOCK_RE.findall(blob):
            try:
                data = json.loads(sub)
                break
            except Exception:
                continue
        if data is None:
            return []
    calls: list[dict] = []
    if isinstance(data, dict):
        if "tools" in data and isinstance(data["tools"], list):
            for c in data["tools"]:
                if isinstance(c, dict) and c.get("name"):
                    calls.append({"name": str(c["name"]), "args": c.get("args") or {}})
        elif data.get("name"):
            calls.append({"name": str(data["name"]), "args": data.get("args") or {}})
    elif isinstance(data, list):
        for c in data:
            if isinstance(c, dict) and c.get("name"):
                calls.append({"name": str(c["name"]), "args": c.get("args") or {}})
    return calls[:4]  # cap at 4 tools per round
