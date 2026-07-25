#!/usr/bin/env python3
"""Derived source map for TNIO Drive retrieval.

This file does not decide whether a user is asking a TNIO question. It only
helps route archive-like questions toward likely Drive sources once the normal
persona/archive router has chosen archive mode.
"""
from __future__ import annotations

import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from lore_config import CHUNKS_PATH, MANIFEST_PATH, RECORDS_DIR, SOURCE_MAP_PATH
except Exception:  # pragma: no cover - useful for ad-hoc CLI execution
    ROOT = Path("/home/REDACTED_DEPLOYMENT_USER/lore-rag")
    CHUNKS_PATH = ROOT / "state" / "chunks.jsonl"
    MANIFEST_PATH = ROOT / "state" / "manifest.json"
    RECORDS_DIR = ROOT / "state" / "records"
    SOURCE_MAP_PATH = ROOT / "state" / "source_map.json"

SOURCE_MAP_VERSION = "source-map-v1"

STOPWORDS = {
    "about", "after", "all", "also", "and", "any", "are", "ask", "can", "could", "does", "for", "from",
    "get", "give", "had", "has", "have", "how", "into", "its", "many", "much", "need", "of", "on", "one",
    "own", "rank", "tell", "that", "the", "their", "them", "there", "this", "through", "to", "was", "were",
    "what", "when", "where", "which", "who", "with", "would", "you", "your", "tnio", "imperial", "new", "order",
    "document", "doc", "sheet", "guide", "codex", "list", "table", "source", "archive", "archives",
}

DOMAIN_TOPICS: dict[str, dict[str, Any]] = {
    "starship": {
        "triggers": ["starship", "starships", "ship", "ships", "vessel", "vessels", "destroyer", "frigate", "corvette", "freighter", "fighter", "bomber"],
        "docs": ["starship codex"],
        "expansions": ["personal starship rank requirement", "ship types available by rank", "destroyer corvette frigate freighter"],
    },
    "droid": {
        "triggers": ["droid", "droids", "function", "functions", "assassin function", "registry"],
        "docs": ["droid codex", "universal registry"],
        "expansions": ["droid ownership laws rank allowance", "droid function catalog", "functions per droid"],
    },
    "vehicle": {
        "triggers": ["vehicle", "vehicles", "speeder", "walker", "mount"],
        "docs": ["vehicle codex", "universal registry"],
        "expansions": ["vehicle ownership rank allowance", "vehicle codex"],
    },
    "character_progression": {
        "triggers": ["apprentice", "lord", "darth", "marks", "mark", "mog", "promotion", "progression", "rank up", "high lord"],
        "docs": ["character progression"],
        "expansions": ["road to darth", "road to lord", "character progression ranks marks"],
    },
    "intelligence": {
        "triggers": ["intelligence", "intel", "cipher", "watcher", "minder", "fixer", "shadowhand", "adjustments", "analysis", "advancements", "death trooper"],
        "docs": ["intel faction guide", "imperial intelligence roster", "know your empire"],
        "expansions": ["imperial intelligence rank structure divisions", "intel faction guide watcher minder fixer shadowhand"],
    },
    "inquisition": {
        "triggers": ["inquisition", "inquisitor", "inquisitorius", "purge", "neophyte", "dedicant", "warden"],
        "docs": ["the inquisition", "inquisitorius specializations"],
        "expansions": ["inquisition rank requirements purge trooper", "inquisitorius specializations"],
    },
    "sithspawn": {
        "triggers": ["sithspawn", "sith spawn", "alchemy", "alchemical", "ritualist"],
        "docs": ["praetorian legion specializations", "master ability list", "praetorian compendium"],
        "expansions": ["sithspawn alchemy specialization", "Sith Alchemy 2 Sith Alchemy 3", "creation of Sithspawn"],
    },
    "beasts": {
        "triggers": ["beast", "beasts", "creature", "creatures", "tame", "taming", "companion", "pet"],
        "docs": ["codex to the beasts", "beastmaster"],
        "expansions": ["beast codex restrictions rank points", "beast taming companion rules"],
    },
    "planets": {
        "triggers": ["planet", "planets", "world", "sector", "climate", "terrain", "hyperlane"],
        "docs": ["codex of planets"],
        "expansions": ["planet codex control climate location", "codex of planets"],
    },
    "combat": {
        "triggers": ["combat", "duel", "dueling", "saber", "lightsaber", "form", "forms", "dice", "roll", "dc"],
        "docs": ["combat", "saber mastery", "ability list"],
        "expansions": ["saber forms combat rules", "dice roll combat guide", "master ability list"],
    },
    "crystals": {
        "triggers": ["crystal", "crystals", "kyber", "bled", "bleeding", "lightsaber crystal"],
        "docs": ["guide to crystals"],
        "expansions": ["kyber crystal guide bled crystals", "guide to crystals"],
    },
    "storyline": {
        "triggers": ["operation", "campaign", "recap", "bulletin", "story", "storyline", "narrative"],
        "docs": ["storyline", "narrative"],
        "expansions": ["storyline narrative campaign recap", "imperial news bulletin"],
    },
    "org_reference": {
        "triggers": ["top members", "specialty heads", "specialty head", "high ranking", "named officers", "named officer", "leaders", "leadership", "who runs", "in charge", "chief", "heads"],
        "docs": ["know your empire"],
        "expansions": ["Know Your Empire organizational reference", "named officers specialty heads high ranking members", "leadership ranks notes"],
    },
    "military": {
        "triggers": ["military", "captain", "sergeant", "colonel", "general", "cadre", "academy cadre", "drill instructor"],
        "docs": ["military faction", "know your empire"],
        "expansions": ["imperial military faction ranks", "military academy cadre"],
    },
}

AUTHORITY_HINTS = [
    (re.compile(r"\b(rule|rules|policy|policies|requirement|requirements|progression|ownership|codex|guide|manual|faction|specialization|specializations)\b", re.I), 2.4),
    (re.compile(r"\b(roster|registry|tracking|log)\b", re.I), 1.55),
    (re.compile(r"\b(storyline|narrative|history|bulletin|recap)\b", re.I), 1.25),
]


def norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def terms(text: str) -> list[str]:
    out = []
    for token in re.findall(r"[a-z0-9][a-z0-9'\-]*", (text or "").lower()):
        token = token.strip("-'_")
        if len(token) < 3 or token in STOPWORDS:
            continue
        out.append(token)
        if token.endswith("s") and len(token) > 4:
            out.append(token[:-1])
    return list(dict.fromkeys(out))


def title_aliases(title: str) -> list[str]:
    title = norm(title)
    aliases = [title]
    cleaned = re.sub(r"^tnio[:\s-]+", "", title, flags=re.I)
    if cleaned != title:
        aliases.append(cleaned)
    for part in re.split(r"[:\-–—]", title):
        part = norm(part)
        if len(part) >= 4:
            aliases.append(part)
    words = terms(title)
    if len(words) >= 2:
        aliases.append(" ".join(words[:5]))
    return list(dict.fromkeys(a for a in aliases if a))[:12]


def doc_kind(title: str, mime_type: str) -> str:
    t = title.lower()
    if "roster" in t or "registry" in t or "tracking" in t or "log" in t:
        return "ledger"
    if "codex" in t or "guide" in t or "faction" in t or "progression" in t or "specialization" in t or "rules" in t:
        return "rulebook"
    if "storyline" in t or "narrative" in t or "history" in t:
        return "chronicle"
    if mime_type.endswith("spreadsheet"):
        return "ledger"
    return "record"


def authority_score(title: str, mime_type: str) -> float:
    score = 1.0
    hay = f"{title} {mime_type}"
    for pattern, boost in AUTHORITY_HINTS:
        if pattern.search(hay):
            score = max(score, boost)
    return score


def infer_topics(title: str, text: str = "") -> list[str]:
    # Keep topic tags conservative. Large TNIO records mention many domains in
    # passing, so using body text here makes unrelated sources look authoritative.
    # Body tokens still become weak keywords; topics should identify the shelf.
    hay = title.lower()
    topics = []
    for topic, cfg in DOMAIN_TOPICS.items():
        if any(doc_hint in hay for doc_hint in cfg["docs"]):
            topics.append(topic)
            continue
        if any(trigger in hay for trigger in cfg["triggers"]):
            topics.append(topic)
    return topics[:5]


def chunk_lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def build_source_map(
    manifest_path: Path | dict = MANIFEST_PATH,
    chunks_path: Path = CHUNKS_PATH,
    records_dir: Path = RECORDS_DIR,
    output_path: Path = SOURCE_MAP_PATH,
) -> dict:
    if isinstance(manifest_path, dict):
        manifest = manifest_path
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"files": {}}
    files = manifest.get("files") or {}
    chunks = chunk_lines(chunks_path)
    by_file: dict[str, list[dict]] = defaultdict(list)
    for chunk in chunks:
        meta = chunk.get("metadata") or {}
        fid = meta.get("file_id")
        if fid:
            by_file[str(fid)].append(chunk)

    documents = []
    alias_index = []
    for fid, entry in sorted(files.items(), key=lambda item: (item[1].get("name") or "").lower()):
        title = norm(entry.get("name") or entry.get("title") or fid)
        related = by_file.get(str(fid), [])
        sample_text = "\n".join(str(c.get("text") or "")[:2500] for c in related[:12])
        headings = []
        table_sections = []
        token_counter: Counter[str] = Counter()
        chunk_types = Counter()
        for chunk in related:
            meta = chunk.get("metadata") or {}
            section = norm(meta.get("section"))
            if section and section.lower() not in {"document", title.lower()}:
                headings.append(section)
            ctype = meta.get("chunk_type") or "section"
            chunk_types[ctype] += 1
            if "table" in ctype or "row" in ctype:
                table_sections.append(section)
            for token in terms(" ".join([str(chunk.get("text") or "")[:1800], section, norm(meta.get("search_text")), norm(meta.get("row_primary"))])):
                token_counter[token] += 1
        topics = infer_topics(title, sample_text)
        aliases = title_aliases(title)
        for topic in topics:
            cfg = DOMAIN_TOPICS.get(topic) or {}
            for doc_hint in cfg.get("docs", []):
                if doc_hint in title.lower():
                    aliases.append(doc_hint)
        aliases = list(dict.fromkeys(a for a in aliases if a))[:18]
        keywords = [token for token, _count in token_counter.most_common(80)]
        doc = {
            "id": fid,
            "name": title,
            "path": entry.get("path") or title,
            "mimeType": entry.get("mimeType"),
            "webViewLink": entry.get("webViewLink"),
            "modifiedTime": entry.get("modifiedTime"),
            "exportPath": entry.get("exportPath"),
            "chunkCount": entry.get("chunkCount") or len(related),
            "kind": doc_kind(title, str(entry.get("mimeType") or "")),
            "authority": authority_score(title, str(entry.get("mimeType") or "")),
            "aliases": aliases,
            "topics": topics,
            "keywords": keywords,
            "headings": list(dict.fromkeys(headings))[:80],
            "has_tables": bool(table_sections),
            "table_sections": list(dict.fromkeys(s for s in table_sections if s))[:40],
            "chunk_types": dict(chunk_types),
        }
        documents.append(doc)
        for alias in aliases:
            alias_index.append({"term": alias.lower(), "file_id": fid, "title": title, "weight": 10.0, "kind": "alias"})
        for topic in topics:
            alias_index.append({"term": topic.replace("_", " "), "file_id": fid, "title": title, "weight": 6.0, "kind": "topic"})
        for kw in keywords[:30]:
            alias_index.append({"term": kw, "file_id": fid, "title": title, "weight": 1.0, "kind": "keyword"})

    # Add entity/record aliases as low-cost source hints back to their source titles.
    for record_file in records_dir.glob("*.jsonl") if records_dir.exists() else []:
        for line in record_file.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rec = json.loads(line)
            except Exception:
                continue
            title = norm(rec.get("source_title") or rec.get("title"))
            fid = norm(rec.get("source_file_id") or rec.get("file_id"))
            names = [rec.get("name"), *(rec.get("aliases") or [])]
            for name in names:
                name = norm(name)
                if len(name) >= 4 and title:
                    alias_index.append({"term": name.lower(), "file_id": fid, "title": title, "weight": 7.0, "kind": "record_alias"})

    # Preserve any prior LLM-enrichment fields when the doc's enrichment
    # inputs haven't changed. enrich_source_map.py computes its own hash
    # over title+headings+exportPath mtime/size; here we don't replicate that
    # — we just copy the prior fields forward keyed by file id. The next
    # enrichment run will recompute its hash and re-process anything stale.
    prior_by_id: dict[str, dict] = {}
    prior_topic_index: dict[str, list[str]] = {}
    try:
        if output_path.exists():
            prior_payload = json.loads(output_path.read_text(encoding="utf-8"))
            for d in (prior_payload.get("documents") or []):
                fid = str(d.get("id") or "")
                if fid:
                    prior_by_id[fid] = d
            prior_topic_index = prior_payload.get("topic_index") or {}
    except Exception:
        prior_by_id = {}
        prior_topic_index = {}
    preserved_fields = (
        "description", "topics_enriched", "canonical_for",
        "key_entities", "enrichment_hash", "enriched_at",
    )
    for doc in documents:
        prior = prior_by_id.get(str(doc.get("id") or ""))
        if not prior:
            continue
        for field in preserved_fields:
            if field in prior:
                doc[field] = prior[field]
        # Merge enriched topics into the auto-derived topics list (dedup).
        enriched_topics = list(prior.get("topics_enriched") or [])
        if enriched_topics:
            merged: list[str] = []
            seen: set[str] = set()
            for t in (doc.get("topics") or []) + enriched_topics:
                tl = (t or "").lower().strip()
                if tl and tl not in seen:
                    seen.add(tl)
                    merged.append(tl)
            doc["topics"] = merged

    # Rebuild topic_index from the (possibly merged) documents.
    rebuilt_topic_index: dict[str, list[str]] = defaultdict(list)
    for d in documents:
        title = d.get("name") or ""
        if not title:
            continue
        for t in (d.get("canonical_for") or []):
            tl = (t or "").lower().strip()
            if tl and title not in rebuilt_topic_index[tl]:
                rebuilt_topic_index[tl].append(title)
        for t in (d.get("topics") or []):
            tl = (t or "").lower().strip()
            if tl and title not in rebuilt_topic_index[tl]:
                rebuilt_topic_index[tl].append(title)

    payload = {
        "version": SOURCE_MAP_VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "corpus_version": manifest.get("corpusVersion"),
        "document_count": len(documents),
        "documents": documents,
        "alias_index": alias_index[:20000],
        "topic_index": dict(sorted(rebuilt_topic_index.items())) or prior_topic_index,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(output_path)
    return payload

_SOURCE_MAP_CACHE: tuple[float, dict] | None = None


def load_source_map(path: Path = SOURCE_MAP_PATH) -> dict:
    global _SOURCE_MAP_CACHE
    try:
        mtime = path.stat().st_mtime
    except Exception:
        return {"documents": [], "alias_index": []}
    if _SOURCE_MAP_CACHE and _SOURCE_MAP_CACHE[0] == mtime:
        return _SOURCE_MAP_CACHE[1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {"documents": [], "alias_index": []}
    _SOURCE_MAP_CACHE = (mtime, data)
    return data


def source_authority_for_title(title: str, path: Path = SOURCE_MAP_PATH) -> float:
    low = (title or "").lower()
    if not low:
        return 1.0
    for doc in load_source_map(path).get("documents") or []:
        name = str(doc.get("name") or "").lower()
        if name == low or low in name or name in low:
            return float(doc.get("authority") or 1.0)
    return 1.0


def route_question(question: str, path: Path = SOURCE_MAP_PATH, limit: int = 6) -> list[dict]:
    q = norm(question).lower()
    if not q:
        return []
    q_terms = set(terms(q))
    if not q_terms:
        return []
    data = load_source_map(path)
    docs = {str(doc.get("id")): doc for doc in data.get("documents") or []}
    scores: dict[str, float] = defaultdict(float)
    reasons: dict[str, set[str]] = defaultdict(set)

    # Domain topic routing catches user phrasing that may not appear in the doc title.
    for topic, cfg in DOMAIN_TOPICS.items():
        matched_triggers = [trigger for trigger in cfg.get("triggers", []) if trigger in q]
        if not matched_triggers:
            continue
        for doc_id, doc in docs.items():
            name_low = str(doc.get("name") or "").lower()
            doc_topics = set(doc.get("topics") or [])
            direct_title_match = any(doc_hint in name_low for doc_hint in cfg.get("docs", []))
            if topic in doc_topics or direct_title_match:
                scores[doc_id] += (16.0 if direct_title_match else 10.0) + float(doc.get("authority") or 1.0)
                reasons[doc_id].add(topic)
                for trigger in matched_triggers[:3]:
                    reasons[doc_id].add(trigger)

    # Alias/keyword index: exact phrase aliases are strong, ordinary keywords are weak.
    for item in data.get("alias_index") or []:
        term = str(item.get("term") or "").lower().strip()
        if not term:
            continue
        hit = False
        if " " in term and term in q:
            hit = True
        elif term in q_terms:
            hit = True
        if not hit:
            continue
        fid = str(item.get("file_id") or "")
        if fid not in docs:
            # record aliases may only know title; map by title if needed
            title = str(item.get("title") or "").lower()
            for doc_id, doc in docs.items():
                if str(doc.get("name") or "").lower() == title:
                    fid = doc_id
                    break
        if fid not in docs:
            continue
        weight = float(item.get("weight") or 1.0)
        if item.get("kind") == "keyword":
            if len(term) < 6:
                continue
            weight = min(weight, 0.55)
        scores[fid] += weight
        reasons[fid].add(term)

    ranked = []
    for fid, score in scores.items():
        doc = docs.get(fid)
        if not doc:
            continue
        # Require either a strong topic/alias signal or multiple weak keyword signals.
        reason_terms = sorted(reasons[fid])
        if score < 4.0 and len(reason_terms) < 2:
            continue
        ranked.append({
            "file_id": fid,
            "title": doc.get("name"),
            "path": doc.get("path"),
            "score": round(score, 3),
            "authority": doc.get("authority"),
            "kind": doc.get("kind"),
            "topics": doc.get("topics") or [],
            "aliases": doc.get("aliases") or [],
            "has_tables": bool(doc.get("has_tables")),
            "reason_terms": reason_terms[:10],
            "webViewLink": doc.get("webViewLink"),
        })
    ranked.sort(key=lambda row: (-row["score"], -float(row.get("authority") or 1), str(row.get("title") or "")))
    return ranked[:limit]


def expand_queries(question: str, limit: int = 4) -> list[str]:
    routed = route_question(question, limit=limit)
    expanded = [norm(question)]
    q_low = question.lower()
    seen = {expanded[0].lower()} if expanded[0] else set()
    for route in routed[:3]:
        title = route.get("title") or ""
        if title:
            phrase = f"{question} {title}"
            if phrase.lower() not in seen:
                expanded.append(phrase)
                seen.add(phrase.lower())
        for topic in route.get("topics") or []:
            for extra in DOMAIN_TOPICS.get(topic, {}).get("expansions", [])[:2]:
                phrase = f"{extra} {title}".strip()
                if phrase and phrase.lower() not in seen and extra.lower() not in q_low:
                    expanded.append(phrase)
                    seen.add(phrase.lower())
        if len(expanded) >= limit:
            break
    return expanded[:limit]


def source_hints_for_question(question: str, limit: int = 8) -> list[str]:
    hints = []
    seen = set()
    for route in route_question(question, limit=limit):
        for value in [route.get("title"), *(route.get("aliases") or [])[:3]]:
            value = norm(value)
            if value and value.lower() not in seen:
                seen.add(value.lower())
                hints.append(value)
        if len(hints) >= limit:
            break
    return hints[:limit]



# --------------------------------------------------------------------------- #
# Topic-index routing (data-driven)
# --------------------------------------------------------------------------- #
#
# The enrichment pass writes a top-level `topic_index` map of the shape:
#     {topic: [doc_title, ...]}
# Each doc also carries `canonical_for: [...]` so we can rank the actual
# canonical source for a topic ahead of merely-related docs.
#
# topic_routes() walks every topic key in the index and asks: does this topic
# phrase appear in the user's question? If yes, the doc(s) registered under
# that topic become hint candidates. We dedup, rank by canonical-first, then
# by doc authority.


_TOPIC_TOKEN_RE = re.compile(r"[a-z][a-z'\-]+")


def _topic_appears_in(topic: str, q_low: str, q_terms: set[str]) -> bool:
    """Does this enrichment-topic match the user question?

    Multi-word topics: tokenize and accept a partial overlap. A topic like
    "grand council membership" should fire on a question about "grand
    council" — requiring the full multi-word phrase rules out the most
    natural phrasings. We require at least 2 significant topic words
    (>=4 chars) to appear in the question, or all of them when the topic
    has only one significant word.

    Single-token topics: must be a whole-word match (in q_terms).
    """
    if not topic:
        return False
    topic_low = topic.lower().strip()
    # Fast path: full phrase appears literally.
    if " " in topic_low or "-" in topic_low:
        if topic_low in q_low:
            return True
    # Token-overlap path (multi- or single-word).
    topic_tokens = _TOPIC_TOKEN_RE.findall(topic_low)
    sig_tokens = [t for t in topic_tokens if len(t) >= 4]
    if not sig_tokens:
        # Topic is entirely short stopword-ish tokens — fall back to phrase.
        return topic_low in q_low
    hits = sum(1 for t in sig_tokens if t in q_terms)
    if len(sig_tokens) == 1:
        return hits == 1
    # Multi-word topic: need >= 2 overlapping significant tokens.
    return hits >= 2


def _expand_topic_query_terms(question: str) -> tuple[str, set[str]]:
    """Normalize common Discord phrasing before matching enrichment topics.

    Source-map topics are generated from archive titles/descriptions and tend
    to say "Imperial Intelligence" and "joining"; users often say "Intel" and
    "join". Expanding the query terms here lets the enriched map route broad
    new phrasings to the right shelf without adding one-off question fixes.
    """
    q_low = (question or "").lower()
    terms = set(_TOPIC_TOKEN_RE.findall(q_low))
    expansions: list[str] = []

    def add_phrase(phrase: str) -> None:
        expansions.append(phrase)
        terms.update(_TOPIC_TOKEN_RE.findall(phrase.lower()))

    if re.search(r"\bintel\b", q_low):
        add_phrase("imperial intelligence")
    if "intelligence" in terms:
        add_phrase("intel")
    if "join" in terms:
        add_phrase("joining eligibility requirement requirements")
    if "joining" in terms:
        add_phrase("join eligible eligibility")
    if terms.intersection({"require", "required", "requires", "requirement", "requirements"}):
        add_phrase("eligible eligibility minimum rank")
    if terms.intersection({"eligible", "eligibility"}):
        add_phrase("requirement requirements minimum")
    if terms.intersection({"sith", "apprentice"}):
        add_phrase("sith apprentice rank")
    if terms.intersection({"nfu", "nonforce", "non", "force"}):
        add_phrase("nfu non force user")

    expanded_low = q_low
    if expansions:
        expanded_low = q_low + " " + " ".join(expansions)
    return expanded_low, terms


def topic_routes(question: str, path: Path = SOURCE_MAP_PATH, limit: int = 6) -> list[dict]:
    """Return doc titles whose registered topics appear in the question.

    Output is a ranked list of dicts:
        [{title, score, canonical, matched_topics, authority, kind, ...}, ...]

    score = (# canonical-for matches) * 4 + (# topic matches) * 1 + authority
    """
    q_low = (question or "").lower()
    if not q_low.strip():
        return []
    q_low, q_terms = _expand_topic_query_terms(question)
    if not q_terms:
        return []
    data = load_source_map(path)
    topic_index = data.get("topic_index") or {}
    if not topic_index:
        return []

    # Pre-build doc lookup by title for canonical/authority lookups.
    by_title: dict[str, dict] = {}
    for doc in data.get("documents") or []:
        title = doc.get("name") or doc.get("title")
        if title:
            by_title[title] = doc

    matched_topics_for: dict[str, set[str]] = defaultdict(set)
    canonical_topics_for: dict[str, set[str]] = defaultdict(set)
    for topic, titles in topic_index.items():
        if not _topic_appears_in(topic, q_low, q_terms):
            continue
        for title in titles:
            matched_topics_for[title].add(topic)
            doc = by_title.get(title) or {}
            if topic in (doc.get("canonical_for") or []):
                canonical_topics_for[title].add(topic)

    ranked: list[dict] = []
    for title, topics in matched_topics_for.items():
        doc = by_title.get(title) or {}
        canonical = canonical_topics_for.get(title, set())
        score = len(canonical) * 4 + len(topics) * 1 + float(doc.get("authority") or 1.0)
        ranked.append({
            "title": title,
            "score": round(score, 3),
            "canonical": sorted(canonical),
            "matched_topics": sorted(topics),
            "authority": doc.get("authority"),
            "kind": doc.get("kind"),
            "webViewLink": doc.get("webViewLink"),
            "description": doc.get("description") or "",
        })
    ranked.sort(key=lambda row: (-row["score"], -float(row.get("authority") or 1), row["title"]))
    return ranked[:limit]


def topic_hint_titles(question: str, path: Path = SOURCE_MAP_PATH, limit: int = 4) -> list[str]:
    """Convenience: return ranked doc titles only, for cheap hint-list use."""
    return [r["title"] for r in topic_routes(question, path=path, limit=limit)]


if __name__ == "__main__":
    payload = build_source_map()
    print(json.dumps({"path": str(SOURCE_MAP_PATH), "documents": payload.get("document_count"), "aliases": len(payload.get("alias_index") or [])}, indent=2))
