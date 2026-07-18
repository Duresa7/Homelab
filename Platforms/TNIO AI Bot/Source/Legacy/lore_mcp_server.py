#!/usr/bin/env python3
import json
import hashlib
import math
import re
import subprocess
import time
import urllib.request
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import chromadb
from mcp.server.fastmcp import FastMCP

from lore_config import CHUNKS_PATH, COLLECTION_NAME, DEFAULT_SEARCH_LIMIT, EMBED_MODEL, INDEX_DIR, MANIFEST_PATH, OLLAMA_BASE_URL, RECORD_MANIFEST_PATH
from lore_records import answer_from_records, records_to_results, search_records


mcp = FastMCP("lore-search")

STOPWORDS = {
    "about",
    "are",
    "can",
    "does",
    "for",
    "from",
    "how",
    "hey",
    "into",
    "is",
    "many",
    "me",
    "much",
    "my",
    "of",
    "our",
    "the",
    "there",
    "tell",
    "that",
    "this",
    "we",
    "what",
    "when",
    "where",
    "who",
    "with",
    "your",
}


MIN_ANSWER_SCORE = 1.15
MAX_CONTEXT_CHARS = 12000
ANSWER_MODEL = "openai-codex/gpt-5.4-mini"
LORE_QUERY_TERMS = re.compile(
    r"\b(tnio|sith|empire|imperial|darth|kaas|dromund|planet|lore|archive|archives|faction|guild|rank|ability|abilities|force|saber|combat|dice|roll|beast|creature|tame|war forge|mandalorian|inquisition|jedi|republic|council|character|roster|holocron|codex|academy|stronghold|flagship|praetorian|ministry|kruea|aiterian|reken|ar'cava|harik)\b",
    re.I,
)
PERSONA_OR_SMALLTALK_TERMS = re.compile(
    r"\b(how are you|how do you feel|feeling|tell me about yourself|who are you|what are you|where are you|where are you located|what planet are you from|yourself|your purpose|your role|your identity|favorite|pizza|pretend|roleplay|pirate|captain)\b",
    re.I,
)
PROMPT_INJECTION_TERMS = re.compile(
    r"\b(ignore|disregard|forget|override)\s+(?:the\s+)?(?:lore|archive|archives|sources|instructions?|rules?|prompt)\b|\bpretend\s+you\s+are\b",
    re.I,
)


CACHE_TTL_SECONDS = 900
PLAN_CACHE: dict[str, tuple[float, dict]] = {}
ANSWER_CACHE: dict[str, tuple[float, dict]] = {}
SEARCH_CACHE: dict[str, tuple[float, dict]] = {}
LAST_CACHE_CORPUS_VERSION: str | None = None
SYNC_STATUS_PATH = CHUNKS_PATH.parent / "sync_status.json"


def cache_get(cache: dict, key: str):
    item = cache.get(key)
    if not item:
        return None
    created, value = item
    if time.time() - created > CACHE_TTL_SECONDS:
        cache.pop(key, None)
        return None
    return value


def cache_set(cache: dict, key: str, value):
    if len(cache) > 256:
        oldest = sorted(cache.items(), key=lambda item: item[1][0])[:64]
        for old_key, _ in oldest:
            cache.pop(old_key, None)
    cache[key] = (time.time(), value)
    return value


def load_json_file(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {}


def current_corpus_version() -> str:
    manifest = load_json_file(MANIFEST_PATH)
    version = manifest.get("corpusVersion")
    if version:
        return str(version)
    files = manifest.get("files", {})
    parts = [str(manifest.get("chunkCount", "")), str(manifest.get("recordCount", "")), str(manifest.get("recordExtractionVersion", ""))]
    for file_id in sorted(files):
        entry = files[file_id]
        parts.extend([file_id, entry.get("modifiedTime", ""), entry.get("contentHash", ""), entry.get("mimeType", "")])
    return hashlib.sha256("\n".join(parts).encode("utf-8", errors="replace")).hexdigest()[:20] if parts else "unknown"


def cache_namespace() -> str:
    global LAST_CACHE_CORPUS_VERSION
    version = current_corpus_version()
    if LAST_CACHE_CORPUS_VERSION is None:
        LAST_CACHE_CORPUS_VERSION = version
    elif LAST_CACHE_CORPUS_VERSION != version:
        PLAN_CACHE.clear()
        ANSWER_CACHE.clear()
        SEARCH_CACHE.clear()
        LAST_CACHE_CORPUS_VERSION = version
    return version


def embedding_health(timeout: int = 4) -> dict:
    payload = json.dumps({"model": EMBED_MODEL, "input": "health check"}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        return {"ok": bool(data.get("embeddings")), "model": EMBED_MODEL, "base_url": OLLAMA_BASE_URL, "latency_ms": round((time.time() - start) * 1000)}
    except Exception as exc:
        return {"ok": False, "model": EMBED_MODEL, "base_url": OLLAMA_BASE_URL, "error": str(exc)}


def health_status() -> dict:
    manifest = load_json_file(MANIFEST_PATH)
    sync_status = load_json_file(SYNC_STATUS_PATH)
    record_manifest = load_json_file(RECORD_MANIFEST_PATH)
    chunk_count = 0
    try:
        if CHUNKS_PATH.exists():
            with CHUNKS_PATH.open(encoding="utf-8") as handle:
                chunk_count = sum(1 for line in handle if line.strip())
    except Exception:
        chunk_count = 0
    try:
        chroma_count = int(get_collection().count())
    except Exception:
        chroma_count = 0
    embed = embedding_health()
    corpus = current_corpus_version()
    warnings = []
    if chunk_count <= 0:
        warnings.append("chunk index is empty")
    if manifest.get("recordCount", 0) <= 0:
        warnings.append("structured record index is empty")
    if chroma_count <= 0:
        warnings.append("vector index is empty")
    elif chunk_count > 0 and chroma_count != chunk_count:
        warnings.append(f"vector index count mismatch: chroma={chroma_count} chunks={chunk_count}")
    if record_manifest.get("total_records") is not None and manifest.get("recordCount") is not None and record_manifest.get("total_records") != manifest.get("recordCount"):
        warnings.append(f"record count mismatch: manifest={manifest.get('recordCount')} record_manifest={record_manifest.get('total_records')}")
    sync_validation = sync_status.get("validation") or {}
    if sync_validation and not sync_validation.get("ok", False):
        warnings.append("last sync validation failed")
    for warning in sync_validation.get("warnings") or []:
        if warning not in warnings:
            warnings.append(warning)
    if not embed.get("ok"):
        warnings.append("embedding service is unavailable")
    return {
        "ok": not warnings,
        "corpus_version": corpus,
        "manifest": {
            "last_sync": manifest.get("lastSync"),
            "file_count": manifest.get("fileCount") or len(manifest.get("files", {})),
            "chunk_count": manifest.get("chunkCount") or chunk_count,
            "record_count": manifest.get("recordCount"),
            "record_extraction_version": manifest.get("recordExtractionVersion") or record_manifest.get("extraction_version"),
        },
        "runtime": {
            "cache_version": LAST_CACHE_CORPUS_VERSION,
            "search_cache_entries": len(SEARCH_CACHE),
            "answer_cache_entries": len(ANSWER_CACHE),
            "plan_cache_entries": len(PLAN_CACHE),
        },
        "index": {
            "chunks_jsonl_count": chunk_count,
            "chroma_count": chroma_count,
            "record_manifest_total": record_manifest.get("total_records"),
        },
        "embedding": embed,
        "last_sync_status": sync_status,
        "warnings": warnings,
    }


def non_lore_persona_query(query: str) -> bool:
    if PROMPT_INJECTION_TERMS.search(query):
        return True
    return bool(PERSONA_OR_SMALLTALK_TERMS.search(query)) and not bool(LORE_QUERY_TERMS.search(query))


def generated_no_answer(text: str) -> bool:
    lower = re.sub(r"\s+", " ", (text or "").lower().replace("’", "'").replace("‘", "'"))
    return any(
        marker in lower
        for marker in [
            "available lore sources do not contain enough information",
            "provided sources do not contain",
            "provided source does not contain",
            "sources do not contain",
            "not mentioned in the provided",
            "not found in the provided",
            "isn't identified in the provided",
            "is not identified in the provided",
            "isn't identified in any of the provided",
            "is not identified in any of the provided",
            "isn't identified in the tnio",
            "is not identified in the tnio",
            "isn't identified in the lore",
            "is not identified in the lore",
            "identity isn't specified",
            "identity is not specified",
            "no record of",
            "no archive record",
            "archive does not contain",
            "archives do not contain",
            "i don't see any lore entry",
            "i do not see any lore entry",
            "couldn't find a tnio lore entry",
            "could not find a tnio lore entry",
            "couldn't find any tnio lore entry",
            "could not find any tnio lore entry",
            "couldn't find any tnio character",
            "could not find any tnio character",
            "couldn't find any tnio",
            "could not find any tnio",
            "no lore entry",
            "no lore or roster entry",
            "isn't specified in these sources",
            "is not specified in these sources",
            "none define",
            "none identify",
            "none of the sources define",
            "none of the sources identify",
        ]
    )


def cached_plan_query(query: str) -> dict:
    key = re.sub(r"\s+", " ", query.strip().lower())
    cached = cache_get(PLAN_CACHE, key)
    if cached is not None:
        return cached
    plan = fallback_plan(query)
    q = query.strip()
    capital_phrases = re.findall(r"\b[A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+){0,3}", q)
    entities = [p.strip() for p in capital_phrases if p.lower() not in {"what", "who", "how", "tell", "list"}]
    if entities:
        plan["entities"] = list(dict.fromkeys([*plan.get("entities", []), *entities]))[:12]
    lower = q.lower()
    if re.search(r"\b(planet|world|control|hyperlane|climate|landscape)\b", lower):
        plan["record_types"] = list(dict.fromkeys([*plan.get("record_types", []), "planet"]))
        plan["source_hints"] = list(dict.fromkeys([*plan.get("source_hints", []), "Codex of Planets"]))
    if re.search(r"\b(beast|creature|tame|pet|companion|handler|ysalamir|ysalamiri)\b", lower):
        plan["record_types"] = list(dict.fromkeys([*plan.get("record_types", []), "asset", "rule"]))
        plan["source_hints"] = list(dict.fromkeys([*plan.get("source_hints", []), "Codex to the Beasts of the Galaxy", "Beastmaster's Log"]))
    if re.search(r"\b(ability|force|saber|form|roll|dice|requirement|rank|progression|rule)\b", lower):
        plan["record_types"] = list(dict.fromkeys([*plan.get("record_types", []), "rule"]))
    if re.search(r"\b(roster|member|members|officer|officers|who are|intelligence|inquisition|council|military|agent)\b", lower):
        plan["record_types"] = list(dict.fromkeys([*plan.get("record_types", []), "roster", "entity"]))
    if "praetorian" in lower:
        plan["source_hints"] = list(dict.fromkeys([*plan.get("source_hints", []), "Praetorian Legion", "History of the Praetorian Legion"]))
    return cache_set(PLAN_CACHE, key, plan)


def result_confidence(rows: list[dict]) -> str:
    if not rows:
        return "low"
    top = rows[0].get("relevance_score", 0) or 0
    if top >= 8 or (len(rows) >= 2 and rows[1].get("relevance_score", 0) >= 5):
        return "high"
    if top >= 2.5:
        return "medium"
    return "low"


def retrieval_mode(plan: dict, rows: list[dict]) -> str:
    record_types = set(plan.get("record_types") or [])
    if record_types:
        return "+".join(sorted(record_types))
    if any(row.get("record_type") for row in rows):
        return "structured"
    if any(row.get("sheet_title") or row.get("row_number") for row in rows):
        return "table"
    if needs_broad_context(" ".join(plan.get("keywords") or [])):
        return "broad"
    return "mixed"


def enrich_result(row: dict, match_reason: str | None = None) -> dict:
    enriched = dict(row)
    section = enriched.get("section") or ""
    sheet_title = enriched.get("sheet_title")
    row_number = enriched.get("row_number")
    if not sheet_title and isinstance(section, str) and section.startswith("Sheet: "):
        sheet_title = section.replace("Sheet: ", "", 1).split(" | ", 1)[0]
    if not row_number and isinstance(section, str):
        m = re.search(r"Row (\d+)", section)
        if m:
            row_number = int(m.group(1))
    enriched["source_title"] = enriched.get("title")
    enriched["sheet_title"] = sheet_title
    enriched["row_number"] = row_number
    enriched["entity_name"] = enriched.get("entity_name") or enriched.get("row_primary")
    enriched["match_reason"] = match_reason or enriched.get("match_type") or "retrieved"
    return enriched


def generate_text(prompt: str, num_predict: int = 700, timeout: int = 240) -> str:
    cmd = [
        "/home/REDACTED_DEPLOYMENT_USER/.npm-global/bin/openclaw",
        "infer",
        "model",
        "run",
        "--gateway",
        "--json",
        "--model",
        ANSWER_MODEL,
        "--prompt",
        prompt,
    ]
    env = {"PATH": "/home/REDACTED_DEPLOYMENT_USER/.npm-global/bin:/usr/local/bin:/usr/bin:/bin", "HOME": "/home/REDACTED_DEPLOYMENT_USER"}
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, env=env)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "OpenClaw inference failed").strip())
    data = json.loads(proc.stdout)
    outputs = data.get("outputs") or []
    for output in outputs:
        text = (output.get("text") or "").strip()
        if text:
            return text
    raise RuntimeError("OpenClaw inference returned no text output")


def safe_json_object(text: str) -> dict:
    match = re.search(r"\{.*\}", text or "", re.S)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def listify(value, limit: int = 12) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        return []
    out = []
    for item in values:
        text = re.sub(r"\s+", " ", str(item or "").strip())
        if text and text.lower() not in {v.lower() for v in out}:
            out.append(text[:120])
        if len(out) >= limit:
            break
    return out


def fallback_plan(query: str) -> dict:
    terms = query_terms(query)
    return {
        "intent": "general_lore",
        "entities": [],
        "keywords": terms[:12],
        "source_hints": [],
        "record_types": [],
        "answer_type": "explanation",
        "needs_list": bool(re.search(r"\b(list|who are|which|what are all|members)\b", query.lower())),
        "needs_count": bool(re.search(r"\b(how many|count|number of)\b", query.lower())),
    }


def normalize_plan(query: str, data: dict) -> dict:
    plan = fallback_plan(query)
    if not data:
        return plan
    intent = re.sub(r"[^a-z0-9_ -]+", "", str(data.get("intent") or plan["intent"]).lower()).strip().replace(" ", "_")
    plan["intent"] = intent or plan["intent"]
    plan["entities"] = listify(data.get("entities"), 16)
    plan["keywords"] = listify(data.get("keywords"), 18) or plan["keywords"]
    plan["source_hints"] = listify(data.get("source_hints") or data.get("preferred_sources"), 10)
    plan["record_types"] = [x for x in listify(data.get("record_types"), 8) if x in {"entity", "roster", "planet", "rule", "asset"}]
    plan["answer_type"] = str(data.get("answer_type") or plan["answer_type"])[:80]
    plan["needs_list"] = bool(data.get("needs_list", plan["needs_list"]))
    plan["needs_count"] = bool(data.get("needs_count", plan["needs_count"]))
    return plan


def plan_query(query: str) -> dict:
    prompt = (
        "You are a search planner for a Google Drive lore retrieval system. "
        "Create a source-neutral search plan from the user question. Do not answer. "
        "Extract dynamic entities, aliases, document/source hints, and keywords that should be searched. "
        "Use source_hints only when the question implies a likely document, faction, group, codex, roster, guide, planet, or rule source. "
        "Return JSON only with keys: intent, entities, keywords, source_hints, record_types, answer_type, needs_list, needs_count.\n\n"
        "Examples of intents: profile_lookup, roster_lookup, rule_requirement, dice_rule, planet_lookup, faction_lore, count_lookup, general_lore.\n"
        f"QUESTION: {query}"
    )
    try:
        raw = generate_text(prompt, num_predict=240, timeout=180)
        return normalize_plan(query, safe_json_object(raw))
    except Exception:
        return fallback_plan(query)


def plan_search_text(query: str, plan: dict) -> str:
    parts = [query]
    for key in ("entities", "keywords", "source_hints", "record_types"):
        parts.extend(plan.get(key) or [])
    parts.append(str(plan.get("intent") or ""))
    parts.append(str(plan.get("answer_type") or ""))
    return " ".join(str(p) for p in parts if p).strip()

def embed_query(query: str) -> list[float] | None:
    payload = json.dumps({"model": EMBED_MODEL, "input": query}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        if data.get("embeddings"):
            return data["embeddings"][0]
    except Exception:
        pass

    payload = json.dumps({"model": EMBED_MODEL, "prompt": query}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["embedding"]
    except Exception:
        return None


def get_collection():
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def query_terms(query: str) -> list[str]:
    terms = []
    for term in re.findall(r"[A-Za-z0-9']+", query.lower()):
        if term in STOPWORDS:
            continue
        if len(term) <= 2 and not term.isdigit():
            continue
        terms.append(term)
        if term.endswith("s") and len(term) > 4:
            terms.append(term[:-1])
    return list(dict.fromkeys(terms))


def query_phrases(query: str, max_len: int = 4) -> list[str]:
    tokens = query_terms(query)
    phrases = []
    for size in range(min(max_len, len(tokens)), 1, -1):
        for idx in range(0, len(tokens) - size + 1):
            window = tokens[idx: idx + size]
            phrase = " ".join(window)
            has_number = any(ch.isdigit() for ch in phrase)
            has_named_token = any(token[:1].isalpha() and len(token) >= 5 for token in window)
            if has_number or size >= 3 or (size == 2 and has_named_token):
                phrases.append(phrase)
    return list(dict.fromkeys(phrases))


def load_chunks() -> list[dict]:
    if not CHUNKS_PATH.exists():
        return []
    chunks = []
    with CHUNKS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def tokenize(text: str) -> list[str]:
    return [term for term in re.findall(r"[A-Za-z0-9']+", text.lower()) if len(term) > 2 and term not in STOPWORDS]


def expand_query(query: str) -> str:
    return query.strip()



def plan_terms(plan: dict) -> list[str]:
    parts = []
    for key in ("entities", "keywords", "source_hints", "record_types"):
        parts.extend(plan.get(key) or [])
    return query_terms(" ".join(parts))


def text_has_all_terms(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return all(re.search(rf"\b{re.escape(term)}\b", lower) for term in terms)


def fuzzy_token_score(needles: list[str], haystack: str) -> float:
    hay_tokens = set(query_terms(haystack))
    score = 0.0
    for needle in needles:
        if len(needle) < 5 or needle.isdigit():
            continue
        best = 0.0
        for token in hay_tokens:
            if abs(len(token) - len(needle)) > 3:
                continue
            best = max(best, SequenceMatcher(None, needle, token).ratio())
        if best >= 0.92:
            score += 2.8
        elif best >= 0.86:
            score += 1.6
    return score



def expand_alias_terms(terms: list[str]) -> list[str]:
    return list(dict.fromkeys(terms))


def source_title_candidates(plan: dict, limit: int = 12) -> dict[str, dict]:
    chunks = load_chunks()
    hints = plan.get("source_hints") or []
    if not hints:
        return {}
    candidates = {}
    for chunk in chunks:
        meta = chunk["metadata"]
        source_text = " ".join([meta.get("name", ""), meta.get("path", ""), meta.get("section", "")]).lower()
        score = 0.0
        for hint in hints:
            terms = expand_alias_terms(query_terms(hint))
            if not terms:
                continue
            hits = sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", source_text))
            if hits >= min(2, len(terms)):
                score += 8.0 + hits
            elif hits:
                score += hits
        if score <= 0:
            continue
        candidates[chunk["chunk_id"]] = {
            "chunk_id": chunk["chunk_id"],
            "doc": chunk.get("text", ""),
            "meta": meta,
            "vector_score": 0.0,
            "lexical_score": score,
        }
    return dict(sorted(candidates.items(), key=lambda item: item[1]["lexical_score"], reverse=True)[:limit])

def source_hint_score(source_text: str, plan: dict) -> float:
    score = 0.0
    source_text = source_text.lower()
    generic_hints = {"rulebook", "core rules", "rules", "guide", "codex", "character creation", "character creation rules"}
    for hint in plan.get("source_hints") or []:
        if hint.lower().strip() in generic_hints:
            continue
        terms = expand_alias_terms(query_terms(hint))
        if terms and sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", source_text)) >= min(2, len(terms)):
            score += 4.0
        elif terms:
            score += 1.2 * sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", source_text))
    for entity in plan.get("entities") or []:
        terms = query_terms(entity)
        if terms and text_has_all_terms(source_text, terms):
            score += 2.0
    return min(score, 8.0)

def needs_broad_context(query: str) -> bool:
    q = query.lower()
    return bool(re.search(r"\b(how many|list|which|what are all|who are|all of the|every)\b", q))


def bm25_scores(chunks: list[dict], terms: list[str]) -> dict[str, float]:
    if not chunks or not terms:
        return {}
    doc_tokens = {}
    dfs = Counter()
    lengths = []
    for chunk in chunks:
        meta = chunk["metadata"]
        text = " ".join(
            [
                chunk.get("text", ""),
                meta.get("name", ""),
                meta.get("path", ""),
                meta.get("section", ""),
                meta.get("search_text", ""),
                meta.get("row_primary", ""),
            ]
        )
        tokens = tokenize(text)
        doc_tokens[chunk["chunk_id"]] = Counter(tokens)
        lengths.append(len(tokens) or 1)
        for term in set(tokens):
            dfs[term] += 1
    avgdl = sum(lengths) / max(1, len(lengths))
    k1 = 1.5
    b = 0.75
    n_docs = len(chunks)
    scores = {}
    for chunk, dl in zip(chunks, lengths):
        counts = doc_tokens[chunk["chunk_id"]]
        score = 0.0
        for term in terms:
            tf = counts.get(term, 0)
            if not tf:
                continue
            idf = math.log(1 + (n_docs - dfs[term] + 0.5) / (dfs[term] + 0.5))
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
        if score:
            scores[chunk["chunk_id"]] = score
    return scores


def lexical_candidates(query: str, limit: int, plan: dict | None = None) -> dict[str, dict]:
    chunks = load_chunks()
    if not chunks:
        return {}
    plan = plan or fallback_plan(query)
    q = query.lower()
    terms = query_terms(query)
    planned_terms = plan_terms(plan)
    all_terms = list(dict.fromkeys([*terms, *planned_terms]))
    bm25 = bm25_scores(chunks, all_terms)
    candidates = {}
    for chunk in chunks:
        meta = chunk["metadata"]
        haystack = " ".join(
            [
                chunk.get("text", ""),
                meta.get("name", ""),
                meta.get("path", ""),
                meta.get("section", ""),
                meta.get("search_text", ""),
                meta.get("row_primary", ""),
            ]
        ).lower()
        if not haystack:
            continue
        term_hits = sum(1 for term in all_terms if re.search(rf"\b{re.escape(term)}\b", haystack))
        phrase_hit = q in haystack
        if not term_hits and not phrase_hit and chunk["chunk_id"] not in bm25:
            continue
        title_haystack = " ".join([meta.get("name", ""), meta.get("path", ""), meta.get("section", ""), meta.get("row_primary", "")]).lower()
        source_haystack = " ".join([meta.get("name", ""), meta.get("path", ""), meta.get("section", "")]).lower()
        title_hits = sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", title_haystack))
        source_topic_hits = sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", source_haystack))
        coverage = term_hits / max(1, len(all_terms))
        source_boost = 0.0
        if source_topic_hits:
            source_boost += min(4.0, 1.5 * source_topic_hits)
        source_boost += source_hint_score(source_haystack, plan)
        score = (
            (3.0 if phrase_hit else 0.0)
            + (2.0 * coverage)
            + (1.25 * title_hits)
            + source_boost
            + min(8.0, bm25.get(chunk["chunk_id"], 0.0))
        )
        if meta.get("chunk_type") == "sheet_row":
            score += 0.25
        candidates[chunk["chunk_id"]] = {
            "chunk_id": chunk["chunk_id"],
            "doc": chunk["text"],
            "meta": meta,
            "vector_score": 0.0,
            "lexical_score": score,
            "term_hits": term_hits,
            "query_terms": len(all_terms),
        }
    return dict(sorted(candidates.items(), key=lambda item: item[1]["lexical_score"], reverse=True)[:limit])



def load_manifest_files() -> list[dict]:
    path = Path('/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/manifest.json')
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return list(data.get('files', {}).values())
    except Exception:
        return []


def flatten_sheet_payload(payload: dict, max_rows_per_sheet: int | None = 120) -> str:
    parts = []
    for sheet_title, rows in payload.get('values', {}).items():
        parts.append(f'## Sheet: {sheet_title}')
        selected_rows = rows if max_rows_per_sheet is None else rows[:max_rows_per_sheet]
        for idx, row in enumerate(selected_rows, start=1):
            cells = [str(cell).strip() for cell in row if str(cell).strip()]
            if cells:
                parts.append(f'Row {idx}: ' + ' | '.join(cells))
        if max_rows_per_sheet is not None and len(rows) > max_rows_per_sheet:
            parts.append(f'... {len(rows) - max_rows_per_sheet} more rows not shown')
    return '\n'.join(parts)


def read_export_context(file_entry: dict, max_chars: int = 70000) -> str:
    path = Path(file_entry.get('exportPath') or '')
    if not path.exists():
        return ''
    try:
        if path.suffix.lower() == '.json':
            text = flatten_sheet_payload(json.loads(path.read_text(encoding='utf-8')), max_rows_per_sheet=None)
        else:
            text = path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return ''
    text = re.sub(r'\n{4,}', '\n\n\n', text).strip()
    return text[:max_chars]


def term_weight(term: str, text: str) -> float:
    if not term:
        return 0.0
    lower = text.lower()
    freq = max(1, len(re.findall(rf'\b{re.escape(term)}\b', lower)))
    return min(12.0, 2.0 + len(term) * 0.7 + 10.0 / freq)


def ranked_evidence_snippets(text: str, terms: list[str], phrases: list[str], radius: int = 520, limit: int = 4) -> list[str]:
    if not text:
        return []
    lower = text.lower()
    candidates = []
    for phrase in phrases:
        if not phrase:
            continue
        start = 0
        phrase_lower = phrase.lower()
        while True:
            pos = lower.find(phrase_lower, start)
            if pos < 0:
                break
            candidates.append((pos, 30.0 + len(phrase), phrase_lower))
            start = pos + max(1, len(phrase_lower))
    for term in terms:
        if not term:
            continue
        weight = term_weight(term, text)
        for match in re.finditer(rf'\b{re.escape(term)}\b', lower):
            candidates.append((match.start(), weight, term))
    if not candidates:
        return [text[: radius * 2].strip()]

    rare_terms = {
        term for term in terms
        if len(term) >= 5 and len(re.findall(rf'\b{re.escape(term)}\b', lower)) <= 5
    }
    windows = []
    for pos, base_score, needle in candidates:
        start = max(0, pos - radius)
        end = min(len(text), pos + radius)
        window_lower = lower[start:end]
        score = base_score
        for phrase in phrases:
            if phrase and phrase.lower() in window_lower:
                score += 18.0 + len(phrase) * 0.5
        hit_terms = 0
        rare_hit = False
        for term in terms:
            if re.search(rf'\b{re.escape(term)}\b', window_lower):
                hit_terms += 1
                score += term_weight(term, text)
                if term in rare_terms:
                    rare_hit = True
                    score += 35.0
        if terms:
            score += 12.0 * (hit_terms / len(terms))
        windows.append((score, start, end, rare_hit))

    rare_windows = [item for item in windows if item[3]]
    other_windows = [item for item in windows if not item[3]]
    rare_windows.sort(key=lambda item: (-item[0], item[1]))
    other_windows.sort(key=lambda item: (-item[0], item[1]))
    windows = rare_windows + other_windows
    snippets = []
    used_ranges = []
    for _score, start, end, _rare_hit in windows:
        if any(not (end < u_start or start > u_end) for u_start, u_end in used_ranges):
            continue
        snippet = text[start:end].strip()
        if start > 0:
            snippet = '... ' + snippet
        if end < len(text):
            snippet = snippet + ' ...'
        if snippet:
            snippets.append(snippet)
            used_ranges.append((start, end))
        if len(snippets) >= limit:
            break
    return snippets


def evidence_snippet(text: str, terms: list[str], phrases: list[str], radius: int = 520) -> str:
    snippets = ranked_evidence_snippets(text, terms, phrases, radius=radius, limit=1)
    return snippets[0] if snippets else ''


def match_score(text: str, terms: list[str], phrases: list[str], *, title: bool = False, sheet: bool = False) -> float:
    if not text:
        return 0.0
    lower = text.lower()
    score = 0.0
    for phrase in phrases:
        if phrase and phrase in lower:
            score += 12.0 if sheet else 9.0
    hits = 0
    for term in terms:
        matches = len(re.findall(rf'\b{re.escape(term)}\b', lower))
        if matches:
            hits += 1
            score += min(5.0, matches * (1.3 if sheet else 1.0))
    if terms:
        score += 4.0 * (hits / len(terms))
    score += fuzzy_token_score(terms, text) * (1.5 if title else 0.8)
    if title:
        score *= 1.6
    return score


def sheet_row_text(row: list) -> str:
    return ' | '.join(str(cell).strip() for cell in row if str(cell).strip())


def search_export_file(query: str, plan: dict, file_entry: dict, max_matches: int = 10) -> dict | None:
    terms = list(dict.fromkeys([*query_terms(query), *plan_terms(plan)]))
    phrases = list(dict.fromkeys([
        *query_phrases(query, max_len=5),
        *query_phrases(' '.join(plan.get('entities') or []), max_len=5),
        *query_phrases(' '.join(plan.get('keywords') or []), max_len=4),
    ]))
    title_text = ' '.join([file_entry.get('name', ''), file_entry.get('path', '')])
    title_score = match_score(title_text, terms, phrases, title=True) + source_hint_score(title_text.lower(), plan)
    path = Path(file_entry.get('exportPath') or '')
    if not path.exists():
        return None
    matches = []
    try:
        if path.suffix.lower() == '.json':
            payload = json.loads(path.read_text(encoding='utf-8'))
            for sheet_title, rows in payload.get('values', {}).items():
                sheet_title_score = match_score(sheet_title, terms, phrases, title=True, sheet=True)
                for idx, row in enumerate(rows, start=1):
                    row_text = sheet_row_text(row)
                    if not row_text:
                        continue
                    haystack = f'{sheet_title} {row_text}'
                    score = sheet_title_score + match_score(haystack, terms, phrases, sheet=True)
                    if score <= 0:
                        continue
                    prev_text = sheet_row_text(rows[idx - 2]) if idx >= 2 else ''
                    next_text = sheet_row_text(rows[idx]) if idx < len(rows) else ''
                    context_lines = []
                    if prev_text:
                        context_lines.append(f'Row {idx - 1}: {prev_text}')
                    context_lines.append(f'Row {idx}: {row_text}')
                    if next_text:
                        context_lines.append(f'Row {idx + 1}: {next_text}')
                    matches.append({
                        'match_type': 'sheet_row',
                        'sheet_title': sheet_title,
                        'row_number': idx,
                        'score': round(score, 4),
                        'text': '\n'.join(context_lines),
                    })
        else:
            body = path.read_text(encoding='utf-8', errors='replace')
            body_score = match_score(body, terms, phrases)
            early_body = body[:2500].lower()
            body_score += sum(18.0 for phrase in phrases if phrase and phrase in early_body)
            snippets = ranked_evidence_snippets(body, terms, phrases, limit=5)
            if body_score > 0:
                for snippet_idx, snippet in enumerate(snippets or [body[:1000].strip()], start=1):
                    matches.append({
                        'match_type': 'document_text',
                        'section': file_entry.get('path') or file_entry.get('name'),
                        'snippet_number': snippet_idx,
                        'score': round(body_score - (snippet_idx - 1) * 0.25, 4),
                        'text': snippet,
                    })
    except Exception:
        return None
    matches.sort(key=lambda item: -item.get('score', 0))
    top_matches = matches[:max_matches]
    if not top_matches and title_score <= 0:
        return None
    aggregate = title_score
    if top_matches:
        aggregate += top_matches[0].get('score', 0)
        aggregate += 0.25 * sum(m.get('score', 0) for m in top_matches[1:5])
    item = dict(file_entry)
    item['document_score'] = round(aggregate, 4)
    item['search_matches'] = top_matches
    return item


def document_search(query: str, plan: dict | None = None, limit: int = 6) -> list[dict]:
    plan = plan or fallback_plan(query)
    results = []
    for file_entry in load_manifest_files():
        hit = search_export_file(query, plan, file_entry)
        if hit and hit.get('document_score', 0) > 0:
            results.append(hit)
    results.sort(key=lambda item: (-item.get('document_score', 0), item.get('name', '')))
    return results[:limit]


def select_documents(query: str, plan: dict, limit: int = 4) -> list[dict]:
    return document_search(query, plan, limit=limit)


@mcp.tool()
def lore_document_search(query: str, limit: int = 8) -> dict:
    clean_query = query.strip()
    plan = cached_plan_query(clean_query)
    results = []
    for doc in document_search(clean_query, plan, limit=max(1, min(int(limit or 8), 12))):
        results.append({
            'title': doc.get('name'),
            'path': doc.get('path') or doc.get('name'),
            'source_url': doc.get('webViewLink'),
            'relevance_score': doc.get('document_score'),
            'matches': doc.get('search_matches', [])[:5],
        })
    return {'query': clean_query, 'plan': plan, 'results': results}


def answer_from_documents(query: str, docs: list[dict], plan: dict) -> dict:
    if not docs:
        return {
            'status': 'no_answer',
            'answer': 'The available lore sources do not contain enough information to answer that.',
            'sources': [],
            'confidence': 'low',
        }
    context_parts = []
    used_sources = []
    total = 0
    budget = 120000
    for idx, doc in enumerate(docs[:6], start=1):
        text = read_export_context(doc, max_chars=30000 if idx <= 2 else 16000)
        if not text:
            continue
        matches = []
        for match in doc.get('search_matches', [])[:8]:
            location = match.get('sheet_title') or match.get('section') or doc.get('path') or doc.get('name')
            if match.get('row_number'):
                location = f"{location}, row {match.get('row_number')}"
            matches.append(f"- {location}: {match.get('text', '')}")
        evidence = '\n'.join(matches) if matches else 'No specific snippets selected; use the full document context.'
        part = f"[{idx}] {doc.get('name')}\nURL: {doc.get('webViewLink') or 'No URL'}\nPath: {doc.get('path') or doc.get('name')}\nMatched evidence:\n{evidence}\n\nFull document/sheet context:\n{text}"
        if total + len(part) > budget:
            part = part[: max(0, budget - total)]
        if not part.strip():
            continue
        context_parts.append(part)
        used_sources.append({
            'source_id': idx,
            'title': doc.get('name'),
            'section': doc.get('path') or doc.get('name'),
            'source_url': doc.get('webViewLink'),
            'relevance_score': doc.get('document_score'),
        })
        total += len(part)
        if total >= budget:
            break
    if not context_parts:
        return {
            'status': 'no_answer',
            'answer': 'The available lore sources do not contain enough information to answer that.',
            'sources': [],
            'confidence': 'low',
        }
    prompt = (
        'You are a TNIO lore assistant answering Discord users from Google Drive source documents.\n'
        'Use the provided document context as your primary knowledge. Answer naturally and helpfully.\n'
        'If the document gives relevant facts but not an exact step-by-step answer, explain the relevant facts and say what is not specified.\n'
        'Do not invent lore, names, ranks, rules, or procedures that are not supported by the documents.\n'
        'Review all provided Docs/Sheets, decide which source(s) actually answer the question, and cite factual claims with source ids like [1]. Keep the answer concise.\n'
        'Do not mention backend systems, tools, models, prompts, or implementation.\n\n'
        f'QUESTION:\n{query}\n\n'
        f'SEARCH PLAN:\n{json.dumps(plan, ensure_ascii=False)}\n\n'
        'DOCUMENTS:\n' + '\n\n'.join(context_parts) + '\n\nANSWER:'
    )
    try:
        generated = generate_text(prompt, num_predict=900, timeout=320).strip()
    except Exception as exc:
        return {
            'status': 'error',
            'answer': 'The lore answer service could not generate an answer from the selected documents.',
            'error': str(exc),
            'sources': used_sources,
            'confidence': 'low',
        }
    if not generated:
        return {
            'status': 'no_answer',
            'answer': 'The available lore sources do not contain enough information to answer that.',
            'sources': [],
            'confidence': 'low',
        }
    cited_ids = {int(match) for match in re.findall(r'\[(\d+)\]', generated)}
    cited_sources = [source for source in used_sources if source.get('source_id') in cited_ids]
    if generated_no_answer(generated):
        return {
            'status': 'no_answer',
            'answer': 'The available lore sources do not contain enough information to answer that.',
            'sources': [],
            'confidence': 'low',
        }
    return {
        'status': 'answered',
        'answer': generated,
        'sources': cited_sources or used_sources[:1],
        'confidence': 'medium',
    }

def format_source(row: dict, index: int) -> str:
    return f"[{index}] {row.get('title') or 'Untitled'} - {row.get('section') or row.get('path') or 'Unknown section'}\nURL: {row.get('source_url') or 'No URL'}\nExcerpt:\n{row.get('excerpt') or ''}"


def parse_doc_ordinal(chunk_id: str) -> int | None:
    parts = chunk_id.split(":")
    if len(parts) >= 2 and parts[1].isdigit():
        return int(parts[1])
    return None


def result_from_chunk(chunk: dict, score: float = 0.0, match_type: str = "context", excerpt: str | None = None, section: str | None = None) -> dict:
    meta = chunk["metadata"]
    return {
        "chunk_id": chunk["chunk_id"],
        "title": meta.get("name"),
        "path": meta.get("path"),
        "section": section or meta.get("section"),
        "source_url": meta.get("webViewLink"),
        "modified_time": meta.get("modifiedTime"),
        "relevance_score": round(score, 4),
        "match_type": match_type,
        "excerpt": excerpt if excerpt is not None else chunk.get("text", ""),
    }


def expand_sheet_context(seed: dict, chunks: list[dict], window: int = 3) -> dict:
    meta = seed["metadata"]
    file_id = meta.get("file_id")
    sheet_title = meta.get("sheet_title")
    row_number = int(meta.get("row_number") or 0)
    neighbors = []
    for chunk in chunks:
        cmeta = chunk["metadata"]
        if cmeta.get("chunk_type") != "sheet_row":
            continue
        if cmeta.get("file_id") != file_id or cmeta.get("sheet_title") != sheet_title:
            continue
        other_row = int(cmeta.get("row_number") or 0)
        if abs(other_row - row_number) <= window:
            neighbors.append((other_row, chunk))
    neighbors.sort(key=lambda item: item[0])
    if not neighbors:
        return result_from_chunk(seed)
    first_row = neighbors[0][0]
    last_row = neighbors[-1][0]
    column_values = {}
    for other_row, chunk in neighbors:
        for line in chunk.get("text", "").splitlines():
            if not line.startswith("- ") or ": " not in line:
                continue
            key, value = line[2:].split(": ", 1)
            key = key.strip().rstrip(":")
            value = value.strip()
            if key and value:
                column_values.setdefault(key, []).append((other_row, value))
    column_context = []
    paired_context = []
    nameish = re.compile(r"\b(?:Darth|Lord|Lady|Moff|Grand Moff|Captain|Minister|Acolyte|Apprentice|Sgt|Corporal)\b|^[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+)+")
    for key, values in sorted(column_values.items()):
        if len(values) < 2:
            continue
        joined = "; ".join(f"Row {row}: {value}" for row, value in values[:8])
        column_context.append(f"- {key}: {joined}")
        ordered = sorted(values, key=lambda item: item[0])
        for (row_a, value_a), (row_b, value_b) in zip(ordered, ordered[1:]):
            if row_b != row_a + 1:
                continue
            if len(value_a) <= 90 and nameish.search(value_a) and value_b:
                paired_context.append(f"- {key} rows {row_a}-{row_b}: {value_a} -> {value_b}")
    parts = []
    if paired_context:
        parts.append("Adjacent row pairings inferred from the sheet layout:\n" + "\n".join(paired_context[:10]))
    if column_context:
        parts.append("Column-oriented table context for the expanded row window:\n" + "\n".join(column_context))
    parts.extend(chunk.get("text", "") for _, chunk in neighbors)
    excerpt = "\n\n".join(parts)
    section = f"Sheet: {sheet_title} | Rows {first_row}-{last_row} (expanded from Row {row_number})"
    return result_from_chunk(seed, match_type="expanded_sheet", excerpt=excerpt, section=section)


def expand_doc_context(seed: dict, chunks: list[dict], window: int = 1) -> dict:
    meta = seed["metadata"]
    file_id = meta.get("file_id")
    ordinal = parse_doc_ordinal(seed["chunk_id"])
    if ordinal is None:
        return result_from_chunk(seed)
    neighbors = []
    for chunk in chunks:
        cmeta = chunk["metadata"]
        if cmeta.get("file_id") != file_id or cmeta.get("chunk_type") != "section":
            continue
        other = parse_doc_ordinal(chunk["chunk_id"])
        if other is not None and abs(other - ordinal) <= window:
            neighbors.append((other, chunk))
    neighbors.sort(key=lambda item: item[0])
    if not neighbors:
        return result_from_chunk(seed)
    first_chunk = neighbors[0][0]
    last_chunk = neighbors[-1][0]
    excerpt = "\n\n".join(chunk.get("text", "") for _, chunk in neighbors)
    section = f"{meta.get('section') or 'Document'} | Chunks {first_chunk}-{last_chunk} (expanded from Chunk {ordinal})"
    return result_from_chunk(seed, match_type="expanded_document", excerpt=excerpt, section=section)


def expand_result_context(results: list[dict], max_results: int = 5, broad: bool = False) -> list[dict]:
    chunks = load_chunks()
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    expanded = []
    seen = set()
    for row in results:
        seed = by_id.get(row.get("chunk_id"))
        if not seed:
            expanded.append(row)
            continue
        meta = seed["metadata"]
        if meta.get("chunk_type") == "sheet_row":
            context_row = expand_sheet_context(seed, chunks, window=8 if broad else 3)
            key = (meta.get("file_id"), meta.get("sheet_title"), context_row.get("section"))
        else:
            context_row = expand_doc_context(seed, chunks, window=3 if broad else 1)
            key = (meta.get("file_id"), context_row.get("section"))
        if key in seen:
            continue
        seen.add(key)
        context_row["relevance_score"] = row.get("relevance_score", context_row.get("relevance_score", 0.0))
        context_row["match_type"] = f"{row.get('match_type', 'match')}+{context_row.get('match_type', 'context')}"
        expanded.append(context_row)
        if len(expanded) >= max_results:
            break
    return expanded


def identity_target(query: str) -> str | None:
    q = query.lower().strip()
    match = re.search(r"\bwho(?:'s|\s+is|\s+are|\s+was|\s+were)\s+(?:the\s+|an?\s+)?(.+?)[?.!]*$", q)
    if not match:
        return None
    target = match.group(1).strip()
    target = re.sub(r"\b(in|from|of|for|on)\b.*$", "", target).strip()
    target = re.sub(r"[^a-z0-9' -]", "", target).strip()
    if target.endswith("s") and len(target) > 4:
        target = target[:-1]
    return target or None


def description_matches_target(description: str, target: str) -> bool:
    desc = description.lower()
    target = target.lower()
    if not target:
        return False
    if " " in target:
        return target in desc
    return bool(re.search(rf"\b{re.escape(target)}\b(?!['’]s)", desc))


def parse_structured_doc_entries(export_path: str) -> list[dict]:
    path = Path(export_path) if export_path else None
    if not path or not path.exists() or path.suffix.lower() != ".txt":
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries = []
    matches = list(re.finditer(r"\n\s*([^\n*][^\n]{1,100})\n(?=\*\s+[A-Za-z][^:]{1,50}:)", text))
    for index, match in enumerate(matches):
        name = " ".join(match.group(1).split())
        if not name or "title of" in name.lower():
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else min(len(text), start + 2500)
        block = text[start:end]
        fields = {}
        for field, value in re.findall(r"^\*\s+([^:\n]{1,80}):\s*(.+)$", block, flags=re.MULTILINE):
            fields[" ".join(field.split()).lower()] = " ".join(value.split())
        if fields:
            entries.append({"name": name, "fields": fields})
    return entries


def requested_control_value(query: str) -> str | None:
    q = query.lower()
    controls = {
        "imperial": "Imperial",
        "republic": "Republic",
        "neutral": "Neutral",
        "hutt": "Hutt Cartel",
        "contested": "Contested",
        "chiss": "Chiss Ascendency",
    }
    for token, label in controls.items():
        if re.search(rf"\b{token}\b", q):
            return label
    if re.search(r"\b(we|our|us|empire|tnio)\b", q) and re.search(r"\b(control|controlled|own|hold|holds)\b", q):
        return "Imperial"
    return None


def normalize_words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9']+", text.lower()) if len(word) > 2 and word not in STOPWORDS}


def query_group_target(query: str) -> str | None:
    q = query.lower()
    patterns = [
        r"\bmembers\s+of\s+(?:the\s+)?(.+?)[?.!]*$",
        r"\bwho\s+(?:are|is)\s+(?:the\s+)?(.+?)[?.!]*$",
        r"\blist\s+(?:the\s+)?(.+?)[?.!]*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            target = match.group(1).strip()
            target = re.sub(r"\b(current|members|member|people|persons|characters)\b", "", target).strip()
            return target or None
    return None


def sheet_title_matches_query(sheet_title: str, query: str) -> bool:
    title_words = normalize_words(sheet_title)
    target_words = normalize_words(query_group_target(query) or query)
    if not title_words or not target_words:
        return False
    return title_words.issubset(target_words) or target_words.issubset(title_words) or len(title_words & target_words) >= min(2, len(title_words))


def answer_from_sheet_roster(query: str, rows: list[dict], used_sources: list[dict]) -> dict | None:
    q = query.lower()
    if not re.search(r"\b(who are|list|members of|current members)\b", q):
        return None
    chunks = load_chunks()
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    nameish = re.compile(r"\b(?:Darth|Lord|Lady|Moff|Grand Moff|Captain|Minister|Acolyte|Apprentice|Sgt|Sergeant|Corporal|Knight|Master)\b|^[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+)+")
    for idx, row in enumerate(rows[: len(used_sources)], start=1):
        seed = by_id.get(row.get("chunk_id"))
        if not seed:
            continue
        meta = seed["metadata"]
        sheet_title = meta.get("sheet_title") or ""
        export_path = meta.get("exportPath") or ""
        if meta.get("chunk_type") != "sheet_row" or not sheet_title_matches_query(sheet_title, query):
            continue
        path = Path(export_path)
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_rows = payload.get("values", {}).get(sheet_title, [])
        normalized = [["" if cell is None else str(cell).strip() for cell in raw] for raw in raw_rows]
        width = max((len(raw) for raw in normalized), default=0)
        normalized = [raw + [""] * (width - len(raw)) for raw in normalized]
        entries = []
        for col in range(width):
            values = [(i + 1, raw[col]) for i, raw in enumerate(normalized) if raw[col]]
            for (row_a, value_a), (row_b, value_b) in zip(values, values[1:]):
                if row_b - row_a > 3:
                    continue
                if len(value_a) > 100 or not nameish.search(value_a):
                    continue
                description_is_name = bool(re.match(r"^(?:Darth|Lord|Lady|Moff|Grand Moff|Captain|Minister|Acolyte|Apprentice|Sgt|Sergeant|Corporal)\s+\S+", value_b)) and len(value_b.split()) <= 5
                if description_is_name:
                    continue
                if len(value_b) < 3:
                    continue
                entries.append({"name": value_a, "description": value_b})
        deduped = []
        seen = set()
        for entry in entries:
            key = (entry["name"].lower(), entry["description"].lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(entry)
        if not deduped:
            continue
        rendered = "; ".join(f"{entry['name']} ({entry['description']}) [{idx}]" for entry in deduped[:25])
        more = f" Plus {len(deduped) - 25} more entries." if len(deduped) > 25 else ""
        return {
            "status": "answered",
            "answer": f"The current entries I found for {sheet_title} are: {rendered}.{more}",
            "sources": used_sources,
            "confidence": "high",
        }
    return None


def answer_from_structured_fields(query: str, rows: list[dict], used_sources: list[dict]) -> dict | None:
    q = query.lower()
    if not re.search(r"\b(how many|count|list|which)\b", q):
        return None
    if not re.search(r"\b(planet|planets|world|worlds)\b", q):
        return None
    control_value = requested_control_value(query)
    if not control_value:
        return None
    for idx, row in enumerate(rows[: len(used_sources)], start=1):
        if "planet" not in (row.get("title") or "").lower():
            continue
        seed_export = None
        chunks = load_chunks()
        by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
        seed = by_id.get(row.get("chunk_id"))
        if seed:
            seed_export = seed["metadata"].get("exportPath")
        entries = parse_structured_doc_entries(seed_export or "")
        if not entries:
            continue
        matched = []
        for entry in entries:
            control = entry["fields"].get("control", "")
            if control.lower() == control_value.lower():
                matched.append(entry["name"])
        unique = []
        seen = set()
        for name in matched:
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(name)
        if not unique:
            continue
        if re.search(r"\b(how many|count)\b", q):
            sample = ", ".join(unique[:12])
            more = f", plus {len(unique) - 12} more" if len(unique) > 12 else ""
            answer = f"The codex lists {len(unique)} unique planets with Control: {control_value} [${idx}]. Examples: {sample}{more}.".replace("[$", "[")
        else:
            answer = f"Planets with Control: {control_value}: " + "; ".join(f"{name} [{idx}]" for name in unique[:40]) + "."
        return {
            "status": "answered",
            "answer": answer,
            "sources": used_sources,
            "confidence": "high",
        }
    return None


def wants_identity_list(query: str) -> bool:
    q = query.lower()
    return bool(re.search(r"\bwho\s+are\b", q) or re.search(r"\blist\b|\bwhich\b", q))


def answer_from_named_entries(query: str, rows: list[dict], used_sources: list[dict]) -> dict | None:
    target = identity_target(query)
    if not target or not wants_identity_list(query):
        return None
    pattern = re.compile(rf"\b{re.escape(target)}\s+[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+)*", re.IGNORECASE)
    entries = []
    for idx, row in enumerate(rows[: len(used_sources)], start=1):
        for match in pattern.finditer(row.get("excerpt") or ""):
            name = match.group(0).strip()
            name = re.split(r"\s{2,}|\s+-\s+|\s+\|\s+", name)[0].strip()
            lowered_name = name.lower()
            if lowered_name == target or any(word in lowered_name for word in ["ability", "abilities", "forms", "points", "stars"]):
                continue
            entries.append({"name": name, "source_id": idx})
    deduped = []
    seen = set()
    for item in entries:
        key = item["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    if not deduped:
        return None
    rendered = "; ".join(f"{item['name']} [{item['source_id']}]" for item in deduped[:20])
    return {
        "status": "answered",
        "answer": f"The {target} entries I found are: {rendered}.",
        "sources": used_sources,
        "confidence": "high",
    }


def answer_from_table_pairings(query: str, rows: list[dict], used_sources: list[dict]) -> dict | None:
    target = identity_target(query)
    if not target:
        return None
    matches = []
    for idx, row in enumerate(rows[: len(used_sources)], start=1):
        for line in (row.get("excerpt") or "").splitlines():
            match = re.match(r"- (?P<column>.+?) rows (?P<rows>\d+-\d+): (?P<name>.+?) -> (?P<description>.+)$", line.strip())
            if not match:
                continue
            name = match.group("name").strip()
            description = match.group("description").strip()
            description_is_name = bool(re.match(r"^(?:Darth|Lord|Lady|Moff|Grand Moff|Captain|Minister|Acolyte|Apprentice|Sgt|Corporal)\s+\S+", description)) and len(description.split()) <= 4
            if description_is_name:
                continue
            if description_matches_target(description, target):
                matches.append({"name": name, "description": description, "source_id": idx})
    if not matches:
        return None
    deduped = []
    seen = set()
    for item in matches:
        key = (item["name"].lower(), item["description"].lower(), item["source_id"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    if len(deduped) == 1:
        item = deduped[0]
        answer = f"The {target} is {item['name']} [${item['source_id']}]."
        answer = answer.replace("[$", "[")
    else:
        entries = "; ".join(f"{item['name']} ({item['description']}) [{item['source_id']}]" for item in deduped[:12])
        answer = f"The matching entries for {target} are: {entries}."
    return {
        "status": "answered",
        "answer": answer,
        "sources": used_sources,
        "confidence": "high",
    }




def diverse_results(results: list[dict], limit: int, per_source: int = 2) -> list[dict]:
    selected = []
    counts = Counter()
    for row in results:
        section = row.get("section") or ""
        major_section = re.split(r"\s*[|]\s*", section)[0]
        key = (row.get("title") or "", major_section)
        if counts[key] >= per_source:
            continue
        selected.append(row)
        counts[key] += 1
        if len(selected) >= limit:
            return selected
    for row in results:
        if row not in selected:
            selected.append(row)
            if len(selected) >= limit:
                break
    return selected


def select_answer_evidence(query: str, results: list[dict], max_sources: int = 5) -> list[dict]:
    candidates = [row for row in results if row.get("excerpt")][:10]
    if len(candidates) <= max_sources:
        return candidates
    source_lines = []
    for idx, row in enumerate(candidates, start=1):
        excerpt = re.sub(r"\s+", " ", row.get("excerpt", "")).strip()[:900]
        source_lines.append(
            f"[{idx}] title={row.get('title') or ''} section={row.get('section') or ''} excerpt={excerpt}"
        )
    prompt = (
        "You are selecting evidence for a lore QA system. Pick only sources that directly help answer the question. "
        "Ignore sources that merely share generic words but answer a different topic. Return JSON only, with this shape: "
        "{\"use\":[1,2],\"enough\":true}. If none directly help, return {\"use\":[],\"enough\":false}.\n\n"
        f"QUESTION: {query}\n\nSOURCES:\n" + "\n".join(source_lines)
    )
    try:
        text = generate_text(prompt, num_predict=160, timeout=180)
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return candidates[:max_sources]
        data = json.loads(match.group(0))
        use = []
        for value in data.get("use", []):
            try:
                pos = int(value) - 1
            except Exception:
                continue
            if 0 <= pos < len(candidates):
                use.append(candidates[pos])
        pinned = candidates[: min(3, max_sources)]
        merged = []
        for row in [*pinned, *use]:
            if row not in merged:
                merged.append(row)
        return merged[:max_sources]
    except Exception:
        return candidates[:max_sources]


def answer_from_sources(query: str, results: list[dict]) -> dict:
    strong = [row for row in results if row.get("relevance_score", 0) >= MIN_ANSWER_SCORE]
    if not strong:
        return {
            "status": "no_answer",
            "answer": "The available lore sources do not contain enough information to answer that.",
            "sources": [],
            "confidence": "low",
        }
    selected = select_answer_evidence(query, strong, max_sources=5)
    if not selected:
        return {
            "status": "no_answer",
            "answer": "The available lore sources do not contain enough information to answer that.",
            "sources": [],
            "confidence": "low",
        }
    strong = selected

    context_parts = []
    used_sources = []
    total = 0
    for idx, row in enumerate(strong[:5], start=1):
        part = format_source(row, idx)
        remaining = MAX_CONTEXT_CHARS - total
        if remaining <= 0:
            break
        if len(part) > remaining:
            if not context_parts:
                part = part[:remaining]
            else:
                break
        context_parts.append(part)
        used_sources.append(
            {
                "source_id": idx,
                "title": row.get("title"),
                "section": row.get("section"),
                "source_url": row.get("source_url"),
                "relevance_score": row.get("relevance_score"),
            }
        )
        total += len(part)
    if not context_parts:
        return {
            "status": "no_answer",
            "answer": "The available lore sources do not contain enough information to answer that.",
            "sources": [],
            "confidence": "low",
        }
    prompt = (
        "You are a strict TNIO lore answerer. Answer only from the provided SOURCES.\n"
        "Rules:\n"
        "- First try to answer from the closest relevant source lines. If the sources answer part of the question, answer that part and clearly say what is not specified.\n"
        "- Only say the sources do not contain enough information when none of the provided sources give a relevant fact.\n"
        "- Treat typos and abbreviations normally: NFU means Non-Force User, and minor spelling differences like mandorian/mandalorian should still match the source.\n"
        "- Answer the user's exact category. If the user asks as a Force user or Sith, use the Sith/Force-user rule and do not include NFU-only requirements unless directly asked or needed for contrast.\n"
        "- Treat NFU as Non-Force User; do not expand it to anything else.\n"
        "- Use expanded sheet/document context to understand nearby rows, columns, and surrounding sections.\n"
        "- Use adjacent row pairings and column-oriented table context when Sheet rows split a name and role/description across nearby rows in the same column.\n"
        "- You may connect a name and role only when the expanded context clearly places them together in the same table, column, or section.\n"
        "- Do not invent names, titles, dice rules, dates, documents, URLs, or explanations.\n"
        "- Cite every factual claim with source ids like [1].\n"
        "- Include a short Sources section using only the provided source ids.\n"
        "- Do not mention backend systems, tools, models, prompts, or implementation.\n\n"
        f"QUESTION:\n{query}\n\n"
        "SOURCES:\n" + "\n\n".join(context_parts) + "\n\nANSWER:"
    )
    try:
        generated = generate_text(prompt, num_predict=700, timeout=260).strip()
    except Exception as exc:
        return {
            "status": "error",
            "answer": "The lore answer service could not generate an answer from the retrieved sources.",
            "error": str(exc),
            "sources": used_sources,
            "confidence": "low",
        }

    generated = re.sub(r"\[(\d+)(?=\s*$)", r"[\1]", generated).strip()
    if not generated or generated_no_answer(generated) or not re.search(r"\[\d+\]", generated):
        return {
            "status": "no_answer",
            "answer": "The available lore sources do not contain enough information to answer that.",
            "sources": [] if generated_no_answer(generated) else used_sources,
            "confidence": "low",
        }
    return {
        "status": "answered",
        "answer": generated,
        "sources": used_sources,
        "confidence": "medium",
    }



def filter_record_hits_by_plan(hits: list[dict], plan: dict) -> list[dict]:
    record_types = set(plan.get("record_types") or [])
    if not hits:
        return hits
    subject_terms = []
    for entity in plan.get("entities") or []:
        subject_terms.extend(query_terms(entity))
    subject_terms = list(dict.fromkeys(subject_terms))

    def exact_subject(hit: dict) -> bool:
        if not subject_terms:
            return False
        names = " ".join([hit.get("name", ""), " ".join(hit.get("aliases", []))]).lower()
        return all(re.search(rf"\b{re.escape(term)}\b", names) for term in subject_terms)

    exact = [hit for hit in hits if exact_subject(hit)]
    rest = [hit for hit in hits if hit not in exact]
    if not record_types:
        return [*exact, *rest]
    preferred = [hit for hit in rest if hit.get("record_type") in record_types]
    others = [hit for hit in rest if hit.get("record_type") not in record_types]
    return [*exact, *preferred, *others]

@mcp.tool()
def lore_search(query: str, limit: int = DEFAULT_SEARCH_LIMIT, plan: dict | None = None) -> dict:
    """Search the synced Google Drive lore index for relevant canon context."""
    clean_query = query.strip()
    if not clean_query:
        return {"query": query, "results": [], "message": "Empty query."}
    limit = max(1, min(int(limit or DEFAULT_SEARCH_LIMIT), 20))
    corpus = cache_namespace()
    cache_key = f"{corpus}::{clean_query.lower()}::{limit}::{json.dumps(plan or {}, sort_keys=True)}"
    cached = cache_get(SEARCH_CACHE, cache_key)
    if cached is not None:
        return cached
    coll = get_collection()
    chroma_count = int(coll.count())
    if chroma_count == 0 and not load_chunks():
        return {
            "query": clean_query,
            "results": [],
            "message": "Lore index is empty. Run /usr/bin/python3 /home/REDACTED_DEPLOYMENT_USER/lore-rag/sync_lore.py --sync.",
        }

    plan = plan or cached_plan_query(clean_query)
    search_query = plan_search_text(clean_query, plan)
    merged = lexical_candidates(search_query, 50, plan=plan)
    for chunk_id, entry in source_title_candidates(plan, limit=20).items():
        existing = merged.get(chunk_id)
        if existing:
            existing["lexical_score"] = max(existing.get("lexical_score", 0), entry.get("lexical_score", 0) + 8.0)
        else:
            entry["lexical_score"] = entry.get("lexical_score", 0) + 8.0
            merged[chunk_id] = entry
    fallback = fallback_plan(clean_query)
    variants = [clean_query]
    compact_terms = query_terms(clean_query)[:6]
    if compact_terms:
        variants.append(" ".join(compact_terms))
    for variant in variants:
        for chunk_id, entry in lexical_candidates(variant, 30, plan=fallback).items():
            existing = merged.get(chunk_id)
            if existing:
                existing["lexical_score"] = max(existing.get("lexical_score", 0), entry.get("lexical_score", 0) + 5.0)
            else:
                entry["lexical_score"] = entry.get("lexical_score", 0) + 5.0
                merged[chunk_id] = entry
    vector = embed_query(search_query) if chroma_count > 0 else None
    if vector is not None:
        result = coll.query(query_embeddings=[vector], n_results=max(limit, 20), include=["documents", "metadatas", "distances"])
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for chunk_id, doc, meta, distance in zip(ids, docs, metas, distances):
            vector_score = max(0.0, 1.0 - float(distance))
            entry = merged.setdefault(
                chunk_id,
                {"chunk_id": chunk_id, "doc": doc, "meta": meta, "vector_score": 0.0, "lexical_score": 0.0},
            )
            entry["vector_score"] = max(entry["vector_score"], vector_score)

    rows = []
    record_hits = filter_record_hits_by_plan(search_records(clean_query, limit=80), plan)
    for record_row in records_to_results(record_hits[:20]):
        record_row = enrich_result(record_row, "structured record")
        record_row["relevance_score"] = round((record_row.get("relevance_score") or 0) + 4.0, 4)
        rows.append(record_row)
    for entry in merged.values():
        meta = entry["meta"]
        combined = entry["lexical_score"] + entry["vector_score"]
        rows.append(
            {
                "chunk_id": entry["chunk_id"],
                "title": meta.get("name"),
                "path": meta.get("path"),
                "section": meta.get("section"),
                "source_url": meta.get("webViewLink"),
                "modified_time": meta.get("modifiedTime"),
                "relevance_score": round(combined, 4),
                "match_type": "hybrid" if entry["lexical_score"] and entry["vector_score"] else ("keyword" if entry["lexical_score"] else "semantic"),
                "chunk_type": meta.get("chunk_type"),
                "sheet_title": meta.get("sheet_title"),
                "row_number": meta.get("row_number"),
                "entity_name": meta.get("row_primary"),
                "match_reason": "keyword+semantic" if entry["lexical_score"] and entry["vector_score"] else ("keyword/source" if entry["lexical_score"] else "semantic"),
                "excerpt": entry["doc"],
            }
        )
    rows.sort(key=lambda row: (-row["relevance_score"], row.get("title") or "", parse_doc_ordinal(row.get("chunk_id", "")) if parse_doc_ordinal(row.get("chunk_id", "")) is not None else 999999))
    rows = [enrich_result(row) for row in rows[:limit]]
    response = {
        "query": clean_query,
        "results": rows,
        "plan": plan,
        "retrieval_mode": retrieval_mode(plan, rows),
        "confidence": result_confidence(rows),
        "corpus_version": corpus,
        "vector_available": bool(vector is not None and chroma_count > 0),
        "guidance": "Use only these excerpts as lore context. If they do not directly answer the question, say the sources do not contain enough information.",
    }
    return cache_set(SEARCH_CACHE, cache_key, response)


@mcp.tool()
def lore_answer(query: str, limit: int = 5) -> dict:
    """Answer from staged Google Drive lore retrieval with structured-record fast paths."""
    clean_query = query.strip()
    if not clean_query:
        return {"query": query, "status": "no_answer", "answer": "Ask a lore question first.", "sources": [], "confidence": "low"}
    if non_lore_persona_query(clean_query):
        return {
            "query": clean_query,
            "status": "no_answer",
            "answer": "That is not a TNIO archive question; answer it through the Librarian persona rather than the Google Drive lore index.",
            "sources": [],
            "confidence": "high",
            "retrieval_mode": "non_lore_persona",
            "evidence": {"route": "non_lore_persona_guard"},
            "corpus_version": cache_namespace(),
        }
    answer_limit = max(1, min(int(limit or 5), 8))
    corpus = cache_namespace()
    cache_key = f"answer::{corpus}::{clean_query.lower()}::{answer_limit}"
    cached = cache_get(ANSWER_CACHE, cache_key)
    if cached is not None:
        cached = dict(cached)
        cached["cached"] = True
        return cached

    plan = cached_plan_query(clean_query)
    planned_query = plan_search_text(clean_query, plan)

    # Deep retrieval always runs, but cheap structured sources are evaluated before model generation.
    record_hits = filter_record_hits_by_plan(search_records(clean_query, limit=max(80, answer_limit * 10)), plan)
    record_results = [enrich_result(row, "structured record") for row in records_to_results(record_hits[: max(answer_limit, 8)])]
    chunk_search = lore_search(clean_query, limit=max(12, answer_limit * 2), plan=plan)
    chunk_results = chunk_search.get("results", [])

    docs = select_documents(clean_query, plan, limit=max(4, min(answer_limit, 6)))
    document_results = []
    for doc in docs:
        preview = read_export_context(doc, max_chars=1400)
        document_results.append(enrich_result({
            "title": doc.get("name"),
            "path": doc.get("path") or doc.get("name"),
            "source_url": doc.get("webViewLink"),
            "source_file": doc.get("exportPath"),
            "relevance_score": doc.get("document_score"),
            "match_type": "document_context",
            "excerpt": preview[:1400],
            "matches": doc.get("search_matches", [])[:5],
        }, "source document export"))

    record_answer = answer_from_records(clean_query, record_hits)
    if record_answer and record_answer.get("status") == "answered" and record_answer.get("confidence") == "high":
        response = {
            "query": clean_query,
            "search": chunk_search,
            "record_results": record_results,
            "document_results": document_results,
            "expanded_results": [*record_results, *document_results, *chunk_results],
            "plan": plan,
            "corpus_version": corpus,
            "retrieval_mode": retrieval_mode(plan, [*record_results, *chunk_results]),
            "evidence": {
                "record_count": len(record_hits),
                "document_count": len(docs),
                "chunk_count": len(chunk_results),
                "route": "structured_record_fast_path",
                "planned_query": planned_query,
            },
            **record_answer,
        }
        return cache_set(ANSWER_CACHE, cache_key, response)

    answer = answer_from_documents(clean_query, docs, plan)
    if answer.get("status") != "answered" and record_answer:
        answer = record_answer
    response = {
        "query": clean_query,
        "search": {
            **chunk_search,
            "results": [*record_results[:5], *chunk_results[:10], *document_results[:5]][:20],
            "guidance": "Staged retrieval searched structured records, chunks, and likely full Google Drive exports before answering.",
        },
        "record_results": record_results,
        "document_results": document_results,
        "expanded_results": [*record_results, *document_results, *chunk_results],
        "plan": plan,
        "corpus_version": corpus,
        "retrieval_mode": retrieval_mode(plan, [*record_results, *chunk_results]),
        "evidence": {
            "record_count": len(record_hits),
            "document_count": len(docs),
            "chunk_count": len(chunk_results),
            "route": "staged_records_chunks_documents",
            "planned_query": planned_query,
        },
        **answer,
    }
    return cache_set(ANSWER_CACHE, cache_key, response)

if __name__ == "__main__":
    mcp.run()
