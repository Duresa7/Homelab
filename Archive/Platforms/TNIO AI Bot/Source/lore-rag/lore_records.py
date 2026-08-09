#!/usr/bin/env python3
import hashlib
import json
import math
import re
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from lore_config import DOC_MIME, RECORD_MANIFEST_PATH, RECORDS_DIR, SHEET_MIME

EXTRACTION_VERSION = "records-v5"
RECORD_KINDS = {
    "entity": "entities.jsonl",
    "roster": "rosters.jsonl",
    "planet": "planets.jsonl",
    "rule": "rules.jsonl",
    "asset": "assets.jsonl",
}
STOPWORDS = {
    "about", "after", "all", "and", "are", "can", "current", "does", "for", "from", "have", "how",
    "hey", "into", "is", "list", "many", "member", "members", "my", "of", "our", "the", "there", "tell",
    "that", "this", "what", "when", "where", "which", "who", "with", "your",
}
ROLE_WORDS = {
    "emperor", "empress", "king", "queen", "lord", "darth", "master", "apprentice", "acolyte", "commander",
    "captain", "major", "colonel", "general", "admiral", "marshal", "director", "minister", "governor",
    "council", "overseer", "inquisitor", "praetor", "agent", "officer", "trooper", "knight", "sith", "imperial",
}
PLANET_FIELDS = {"control", "climate", "location", "routes", "landscape", "terrain", "notable locations", "sector"}
RULE_FIELDS = {"rank", "roll", "dice", "requirement", "requirements", "restriction", "restrictions", "progression", "ability", "abilities", "bonus", "dc", "hp", "health", "form", "forms"}
ASSET_FIELDS = {"class", "type", "style", "model", "manufacturer", "crew", "passengers", "speed", "armament", "weapons", "hull", "shield", "hyperdrive", "starship", "vehicle", "ship", "droid", "beast", "crystal", "equipment"}
PROFILE_FIELDS = {"name", "full_name", "aliases", "age", "birthplace", "homeworld", "species", "height", "weight", "title", "titles", "rank", "factions", "allegiances", "occupation_s", "profile_type"}
CHARACTER_SECTION_FIELDS = {
    "titles": "titles",
    "allegiances": "allegiances",
    "factions": "factions",
    "equipment": "equipment",
    "items": "artifacts",
    "weapons and armor": "equipment",
    "ships": "ships",
    "droids": "droids",
    "droids and pets": "droids_and_pets",
    "beasts": "beasts",
}
ASSET_SECTION_SUBTYPES = {
    "equipment": "equipment",
    "items": "artifact",
    "weapons and armor": "equipment",
    "ships": "ship",
    "droids": "droid",
    "droids and pets": "droid_or_pet",
    "beasts": "beast",
}
GENERIC_RECORD_NAMES = {
    "master",
    "level of mastery",
    "further examples",
    "introduction",
    "cost",
    "notes",
    "additional notes",
    "requirements",
    "restrictions",
    "overview",
    "document",
    "sheet",
}


def norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def norm_key(text: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", norm(text).lower()).strip("_")


def toks(text: str) -> list[str]:
    words = []
    for token in re.findall(r"[A-Za-z0-9']+", text.lower()):
        if len(token) <= 2 or token in STOPWORDS:
            continue
        words.append(token)
        if token.endswith("s") and len(token) > 4:
            words.append(token[:-1])
    return words


def stable_id(*parts: Any) -> str:
    raw = "|".join(norm(part).lower() for part in parts if part is not None)
    return hashlib.sha1(raw.encode("utf-8", errors="replace")).hexdigest()[:20]


def source_for(file_entry: dict, **extra: Any) -> dict:
    source = {
        "file_id": file_entry.get("id"),
        "title": file_entry.get("name"),
        "url": file_entry.get("webViewLink"),
        "path": file_entry.get("path") or file_entry.get("name"),
        "modified_time": file_entry.get("modifiedTime"),
    }
    source.update({k: v for k, v in extra.items() if v not in (None, "", [])})
    return source


def make_record(record_type: str, name: str, fields: dict | None, source: dict, summary: str = "", aliases: list[str] | None = None, confidence: float = 0.7) -> dict:
    clean_name = norm(name)
    clean_fields = {norm_key(k): norm(v) for k, v in (fields or {}).items() if norm(v)}
    alias_values = []
    for alias in aliases or []:
        alias = norm(alias)
        if alias and alias.lower() != clean_name.lower():
            alias_values.append(alias)
    search_text = " ".join([
        clean_name,
        " ".join(alias_values),
        record_type,
        summary,
        " ".join(f"{k} {v}" for k, v in clean_fields.items()),
        source.get("title", ""), source.get("path", ""), source.get("sheet_title", ""), source.get("section", ""),
    ])
    row_bits = ",".join(str(x) for x in source.get("row_numbers", []))
    rid = stable_id(source.get("file_id"), source.get("sheet_title") or source.get("section"), row_bits, record_type, clean_name, clean_fields)
    return {
        "record_id": rid,
        "record_type": record_type,
        "name": clean_name,
        "aliases": alias_values,
        "summary": summary or summarize_fields(clean_fields),
        "fields": clean_fields,
        "source": source,
        "search_text": search_text,
        "confidence": round(float(confidence), 3),
    }


def summarize_identity_fields(fields: dict) -> str:
    parts = []
    for key in ("full_name", "name", "title", "titles", "rank", "notes", "species_gender", "factions", "allegiances", "homeworld", "birthplace", "species"):
        value = fields.get(key)
        if value:
            label = key.replace("_", " ")
            parts.append(f"{label}: {value}")
        if len(parts) >= 6:
            break
    return "; ".join(parts)


def summarize_fields(fields: dict) -> str:
    if not fields:
        return ""
    preferred = []
    for key in ("full_name", "role_or_description", "role", "rank", "title", "titles", "notes", "factions", "allegiances", "homeworld", "birthplace", "species", "name", "starship", "ship", "ships", "vehicle", "droid", "droids", "beast", "beasts", "artifact", "artifacts", "equipment", "style", "class", "type", "model", "description", "requirements", "restricted_ownership", "control", "climate", "location", "phase", "outcome", "hyperlane_route_s", "landscape", "roll", "rolls", "bonus", "hull", "hyperdrive", "additional_notes"):
        if fields.get(key):
            label = {"role_or_description": "role"}.get(key, key.replace("_", " "))
            preferred.append(f"{label}: {fields[key]}")
    if preferred:
        return "; ".join(preferred[:6])
    parts = []
    for key, value in fields.items():
        if re.fullmatch(r"column(?:_\d+)?", key):
            continue
        parts.append(f"{key.replace('_', ' ')}: {value}")
        if len(parts) >= 6:
            break
    return "; ".join(parts)


def classify_record(name: str, fields: dict, title: str, section: str = "") -> str:
    hay = " ".join([name, title, section, " ".join(fields.keys()), " ".join(str(v) for v in fields.values())]).lower()
    keys = {norm_key(k).replace("_", " ") for k in fields}
    planet_signal = ("codex of planets" in title.lower() or "planet" in title.lower()) and (keys & PLANET_FIELDS or "control" in keys)
    if planet_signal or ({"control", "climate", "location"} <= keys):
        return "planet"
    if fields.get("profile_type") == "character":
        return "entity"
    if keys & ASSET_FIELDS or re.search(r"\b(ship|starship|vehicle|droid|beast|crystal|equipment|lightsaber|artifact|weapon|armor|registry)\b", hay):
        return "asset"
    if keys & RULE_FIELDS or re.search(r"\b(rank|dice|rolls?|progression|requirement|restriction|ability|forms?|hp|health|trial)\b", hay):
        return "rule"
    if re.search(r"\b(council|roster|members?|faction|academy|inquisition|military|intelligence|legion|praetorian)\b", hay):
        return "roster"
    return "entity"


def should_skip_name(name: str) -> bool:
    n = norm(name).lower()
    if not n or len(n) < 2 or len(n) > 120:
        return True
    if n in {"name", "planet name", "title", "document", "sheet", "row", "primary", "(guide)", "open", "[empty]"}:
        return True
    if "title of" in n or n.startswith("field ") or n.startswith("column "):
        return True
    return False


def generic_record_name(record: dict) -> bool:
    name = norm(record.get("name", "")).lower()
    if name.startswith(("*", "-", "•")):
        return True
    if re.search(r"\bdc\s*\d+\b", name):
        return True
    return name in GENERIC_RECORD_NAMES or bool(re.fullmatch(r"(cost|rank|tier|level|phase|part|step)\s*\d*", name))


def clean_record_name(name: str) -> str:
    cleaned = norm(name).lstrip("\ufeff").strip()
    cleaned = re.sub(r"^\s*[-*•]\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s*[✶★*]+\s*$", "", cleaned).strip()
    return cleaned


def compact_join(values: list[str], limit: int = 8) -> str:
    seen = []
    for value in values:
        cleaned = norm(value).strip("-*• \t")
        if cleaned and cleaned.lower() not in {v.lower() for v in seen}:
            seen.append(cleaned)
        if len(seen) >= limit:
            break
    return "; ".join(seen)


def document_title_aliases(title: str, full_name: str = "") -> list[str]:
    aliases = [title, full_name]
    for value in [title, full_name]:
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z'’-]*", value or "") if w.lower() not in {"the", "of", "and"}]
        if len(words) >= 2:
            aliases.append(" ".join(words[-2:]))
            if words[0].lower() in {"darth", "lord", "moff", "emperor"}:
                aliases.append(f"{words[0]} {words[-1]}")
            if len(words) >= 3 and words[0].lower() in {"grand"}:
                aliases.append(" ".join(words[:2] + words[-1:]))
    return [a for a in aliases if norm(a)]


def section_key(line: str) -> str:
    return re.sub(r"[^a-z0-9 &]+", "", clean_record_name(line).lower()).strip()


def section_like(line: str) -> bool:
    stripped = clean_record_name(line)
    if not stripped or len(stripped) > 90 or stripped.endswith((".", ",", ";", ":")):
        return False
    key = section_key(stripped)
    return key in CHARACTER_SECTION_FIELDS or bool(re.search(r"\b(abilities|statistics|stats|background|personality|skills|forms|campaign|phase)\b", key))


def parse_doc_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = defaultdict(list)
    current = ""
    for line in lines:
        stripped = clean_record_name(line.strip().strip("#").strip())
        if not stripped:
            continue
        key = section_key(stripped)
        if key in CHARACTER_SECTION_FIELDS or section_like(stripped):
            current = key
            continue
        if current:
            sections[current].append(stripped)
    return sections


def field_match(line: str) -> tuple[str, str] | None:
    m = re.match(r"^\s*(?:[-*•]\s*)?([A-Za-z][A-Za-z0-9 /&'()\-]{1,50})\s*:\s*(.+?)\s*$", line)
    if not m:
        return None
    return norm(m.group(1)), norm(m.group(2))


def extract_character_profile_records(file_entry: dict, lines: list[str]) -> list[dict]:
    title = file_entry.get("name", "")
    profile_fields: dict[str, str] = {}
    profile_key_hits = 0
    early_nonempty = [clean_record_name(line) for line in lines if clean_record_name(line)][:120]
    for line in early_nonempty:
        matched = field_match(line)
        if not matched:
            continue
        key, value = matched
        key_norm = norm_key(key)
        if key_norm in PROFILE_FIELDS or key_norm in {"eye_color", "eye_colour", "family", "markings", "sex", "occupation_s", "hit_points", "dice_roll"}:
            profile_fields[key] = value
            if key_norm in PROFILE_FIELDS:
                profile_key_hits += 1
    if profile_key_hits < 3:
        return []

    sections = parse_doc_sections(lines)
    for sec_key, field_name in CHARACTER_SECTION_FIELDS.items():
        values = sections.get(sec_key, [])
        if not values:
            continue
        extracted = []
        for value in values:
            matched = field_match(value)
            extracted.append(matched[1] if matched and sec_key not in {"items", "weapons and armor"} else value)
        joined = compact_join(extracted, limit=10)
        if joined:
            profile_fields[field_name.replace("_", " ")] = joined

    clean_fields = {norm_key(k): v for k, v in profile_fields.items()}
    full_name = clean_fields.get("name") or clean_fields.get("full_name") or early_nonempty[0] or title
    aliases = document_title_aliases(title, full_name)
    if clean_fields.get("aliases"):
        aliases.extend([part.strip() for part in re.split(r"[,;/]", clean_fields["aliases"]) if part.strip()])
    clean_fields["profile_type"] = "character"
    clean_fields["document_title"] = title
    src = source_for(file_entry, section="Character Profile", row_numbers=[1, min(len(lines), 120)])
    records = [make_record("entity", full_name, clean_fields, src, aliases=aliases, confidence=0.96)]

    records.extend(extract_character_asset_records(file_entry, lines, full_name, aliases))
    return records


def extract_character_asset_records(file_entry: dict, lines: list[str], owner: str, owner_aliases: list[str]) -> list[dict]:
    sections = parse_doc_sections(lines)
    records: list[dict] = []
    for sec_key, subtype in ASSET_SECTION_SUBTYPES.items():
        values = sections.get(sec_key, [])
        if not values:
            continue
        current_name = ""
        current_fields: dict[str, str] = {}
        start = 1

        def flush_asset() -> None:
            nonlocal current_name, current_fields, start
            name = clean_record_name(current_name)
            if not name or should_skip_name(name):
                current_name = ""
                current_fields = {}
                return
            fields = {"owner": owner, "asset_subtype": subtype, **current_fields}
            src = source_for(file_entry, section=sec_key.replace("_", " ").title(), row_numbers=[start])
            records.append(make_record("asset", name, fields, src, aliases=[*owner_aliases, owner, sec_key, f"{name} {subtype}"], confidence=0.9))
            current_name = ""
            current_fields = {}

        for idx, raw in enumerate(values, start=1):
            line = clean_record_name(raw)
            if not line:
                continue
            matched = field_match(line)
            bullet = raw.lstrip().startswith(("-", "*", "•"))
            if matched and (not current_name or sec_key in {"items", "weapons and armor", "equipment"}):
                flush_asset()
                current_name, desc = matched
                current_fields = {"description": desc}
                start = idx
                continue
            ship_component = sec_key == "ships" and re.search(r"\b(hyperdrive|cannon|turret|launcher|torpedo|torpedoes|beam|tether|tethers|railgun|turbolaser|turbolasers|neutralizer|missile)\b", line, re.I)
            if current_name and ship_component:
                key = "details"
                current_fields[key] = compact_join([current_fields.get(key, ""), line], limit=20)
                continue
            if not bullet and len(line) <= 90 and not line.endswith((".", ",", ";", ":")):
                flush_asset()
                current_name = line
                current_fields = {}
                start = idx
                continue
            if current_name:
                key = "details"
                current_fields[key] = compact_join([current_fields.get(key, ""), line], limit=20)
        flush_asset()
    return records


def extract_beast_profile_records(file_entry: dict, lines: list[str]) -> list[dict]:
    if "beast" not in file_entry.get("name", "").lower():
        return []
    records: list[dict] = []
    current_name = ""
    current_fields: dict[str, str] = {}
    notes: list[str] = []
    start_line = 1
    heading_re = re.compile(r"^\s*(?![-*•])(.{2,90}?)\s*[-–]\s*[✶★*]{1,5}\s*$")

    def flush(end_line: int) -> None:
        nonlocal current_name, current_fields, notes, start_line
        name = clean_record_name(current_name)
        if name and not should_skip_name(name) and len(current_fields) >= 3:
            fields = {"asset_subtype": "beast", "beast": name, **current_fields}
            if notes:
                fields["description"] = " ".join(notes)[:1200]
            src = source_for(file_entry, section=name, row_numbers=[start_line, end_line])
            records.append(make_record("asset", name, fields, src, aliases=["beast", file_entry.get("name", "")], confidence=0.94))
        current_name = ""
        current_fields = {}
        notes = []
        start_line = 1

    for idx, raw in enumerate(lines, start=1):
        raw_line = norm(raw)
        line = clean_record_name(raw_line)
        if not line:
            continue
        m = heading_re.match(raw_line)
        if m:
            flush(idx - 1)
            current_name = clean_record_name(m.group(1))
            current_fields = {}
            notes = []
            start_line = idx
            continue
        if not current_name:
            continue
        matched = field_match(line)
        if matched:
            key, value = matched
            current_fields[key] = value
        elif re.match(r"^(DISTINCTIVE FEATURES|IN THE WILD|Notes from Handlers?)$", line, re.I):
            continue
        elif len(" ".join(notes)) < 1200 and not re.match(r"^[A-Z][A-Z /&'-]{2,60}$", line):
            notes.append(line)
    flush(len(lines))
    return records


def extract_named_dash_records(file_entry: dict, lines: list[str]) -> list[dict]:
    title = file_entry.get("name", "")
    if "beast" in title.lower() or not re.search(r"\b(crystals?|forge|forging|saber|lightsaber|item)\b", title, re.I):
        return []
    records: list[dict] = []
    for idx, raw in enumerate(lines, start=1):
        line = clean_record_name(raw)
        m = re.match(r"^(.{2,80}?)\s+-\s+(.{20,})$", line)
        if not m:
            continue
        name, desc = clean_record_name(m.group(1)), norm(m.group(2))
        if should_skip_name(name):
            continue
        subtype = "crystal" if re.search(r"\b(crystal|white|black|kyber)\b", name + " " + title, re.I) else "item"
        fields = {"asset_subtype": subtype, "description": desc}
        src = source_for(file_entry, section="Named Items", row_numbers=[idx])
        records.append(make_record("asset", name, fields, src, aliases=[title, subtype, f"{name} {subtype}"], confidence=0.88))
    return records


def extract_heading_paragraph_records(file_entry: dict, lines: list[str]) -> list[dict]:
    title = file_entry.get("name", "")
    records: list[dict] = []
    interesting = re.compile(r"\b(crystal|alchemy|campaign|phase|trial|forge|hunt|event|knowledge|empire|enemy)\b", re.I)
    nonempty = [(idx, clean_record_name(line)) for idx, line in enumerate(lines, start=1) if clean_record_name(line)]
    for pos, (idx, line) in enumerate(nonempty[:-1]):
        if len(line) > 80 or line.endswith((".", ",", ";", ":")) or not interesting.search(line + " " + title):
            continue
        next_line = nonempty[pos + 1][1]
        if len(next_line) < 40:
            continue
        rtype = "asset" if re.search(r"\b(crystal|alchemy|forge|hunt)\b", line + " " + title, re.I) else "entity"
        fields = {"description": next_line[:1500], "document_title": title}
        src = source_for(file_entry, section=line, row_numbers=[idx, nonempty[pos + 1][0]])
        records.append(make_record(rtype, line, fields, src, aliases=[title], confidence=0.78))
    return records


def extract_event_log_records(file_entry: dict, lines: list[str]) -> list[dict]:
    title = file_entry.get("name", "")
    if not re.search(r"\b(campaign|complete|history|archives? entry|consumption)\b", title + " " + "\n".join(lines[:8]), re.I):
        return []
    records: list[dict] = []
    nonempty = [(idx, clean_record_name(line)) for idx, line in enumerate(lines, start=1) if clean_record_name(line)]
    for pos, (idx, line) in enumerate(nonempty):
        m = re.match(r"^(Phase\s+[A-Za-z0-9]+|Battle Report|Aggressors|Defenders|Outcome|Result)\s*:\s*(.+)$", line, re.I)
        if not m:
            continue
        label, value = norm(m.group(1)), norm(m.group(2))
        context = []
        for _, next_line in nonempty[pos + 1:pos + 4]:
            if re.match(r"^(Phase\s+[A-Za-z0-9]+|Battle Report|Aggressors|Defenders|Outcome|Result)\s*:", next_line, re.I):
                break
            context.append(next_line)
        fields = {"event_type": label, "phase": value, "description": " ".join(context)[:1500], "document_title": title}
        src = source_for(file_entry, section=label, row_numbers=[idx])
        records.append(make_record("entity", f"{title} - {label}: {value}", fields, src, aliases=[title, value, "event log"], confidence=0.86))
    return records


def extract_doc_table_records(file_entry: dict, lines: list[str]) -> list[dict]:
    records: list[dict] = []
    section = file_entry.get("name", "Document")
    i = 0
    header_tokens = {"species", "gender", "title", "notes", "status", "rank", "role", "position", "office", "description", "faction"}
    while i < len(lines):
        raw = lines[i]
        stripped = clean_record_name(raw.strip().strip("#").strip())
        if stripped and not raw.startswith(("\t", " ")) and not field_match(stripped) and not stripped.endswith((".", ",", ";", ":")):
            section = stripped
        if stripped.lower() != "name":
            i += 1
            continue

        cells: list[tuple[int, str]] = []
        j = i + 1
        while j < len(lines):
            raw_cell = lines[j]
            cell = clean_record_name(raw_cell)
            if raw_cell.startswith(("\t", " ")) and not cell:
                cells.append((j + 1, ""))
                j += 1
                continue
            if not cell:
                if cells:
                    nxt = j + 1
                    while nxt < len(lines) and not clean_record_name(lines[nxt]):
                        nxt += 1
                    if nxt < len(lines) and lines[nxt].startswith(("\t", " ")):
                        j += 1
                        continue
                    break
                j += 1
                continue
            if set(cell) == {"_"}:
                break
            if raw_cell.startswith(("\t", " ")):
                cells.append((j + 1, cell))
                j += 1
                continue
            break

        headers = ["Name"]
        pos = 0
        while pos < len(cells):
            key = norm_key(cells[pos][1])
            key_terms = set(key.split("_"))
            if len(cells[pos][1]) <= 60 and (key_terms & header_tokens):
                headers.append(cells[pos][1])
                pos += 1
                continue
            break
        if len(headers) < 2:
            i += 1
            continue

        width = len(headers)
        data = cells[pos:]
        for start in range(0, len(data) - width + 1, width):
            group = data[start:start + width]
            values = [cell for _, cell in group]
            name = values[0]
            if should_skip_name(name):
                continue
            fields = {headers[idx]: values[idx] for idx in range(1, width) if values[idx]}
            if not fields:
                continue
            rtype = classify_record(name, fields, file_entry.get("name", ""), section)
            if rtype == "entity" and re.search(r"\b(council|military|academy|intelligence|inquisition|legion|faction|roster|empire|enemy)\b", section + " " + file_entry.get("name", ""), re.I):
                rtype = "roster"
            src = source_for(file_entry, section=section, row_numbers=[group[0][0], group[-1][0]])
            aliases = [section, file_entry.get("name", "")]
            records.append(make_record(rtype, name, fields, src, aliases=aliases, confidence=0.9))
            if rtype != "entity":
                records.append(make_record("entity", name, fields, src, aliases=[rtype, *aliases], confidence=0.74))
        i = max(j, i + 1)
    return records


def extract_doc_records(file_entry: dict, text: str) -> list[dict]:
    records: list[dict] = []
    raw_lines = text.replace("\r\n", "\n").splitlines()
    lines = [line.rstrip() for line in raw_lines]
    records.extend(extract_character_profile_records(file_entry, raw_lines))
    records.extend(extract_beast_profile_records(file_entry, raw_lines))
    records.extend(extract_named_dash_records(file_entry, raw_lines))
    records.extend(extract_heading_paragraph_records(file_entry, raw_lines))
    records.extend(extract_event_log_records(file_entry, raw_lines))
    records.extend(extract_doc_table_records(file_entry, raw_lines))
    current_section = file_entry.get("name", "Document")
    block_name = ""
    fields: dict[str, str] = {}
    start_line = 0

    def flush(end_line: int) -> None:
        nonlocal block_name, fields, start_line
        if block_name and fields and not should_skip_name(block_name):
            rtype = classify_record(block_name, fields, file_entry.get("name", ""), current_section)
            src = source_for(file_entry, section=current_section, row_numbers=[start_line, end_line])
            records.append(make_record(rtype, block_name, fields, src, aliases=[current_section], confidence=0.82))
            if rtype != "entity":
                records.append(make_record("entity", block_name, fields, src, aliases=[rtype, current_section], confidence=0.68))
        block_name = ""
        fields = {}
        start_line = 0

    field_re = re.compile(r"^\s*(?:[-*•]\s*)?([A-Za-z][A-Za-z0-9 /&'()\-]{1,50})\s*:\s*(.+?)\s*$")
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip().strip("#").strip()
        if not stripped:
            continue
        if line.lstrip().startswith("#"):
            flush(idx - 1)
            current_section = stripped
            continue
        m = field_re.match(line)
        if m:
            key, value = norm(m.group(1)), norm(m.group(2))
            if not block_name:
                # Use section as a fallback only for short, concrete section titles.
                block_name = current_section if 2 <= len(current_section) <= 90 else file_entry.get("name", "Document")
                start_line = idx
            fields[key] = value
            continue
        if len(stripped) <= 90 and not stripped.endswith(('.', ',', ';', ':')):
            # A new compact line before fields is usually the entity/block name in TNIO docs.
            if block_name and fields:
                flush(idx - 1)
            if not re.search(r"\b(control|climate|location|routes|notes|requirements?)\b\s*:", stripped, re.I):
                block_name = stripped
                fields = {}
                start_line = idx
    flush(len(lines))
    return records


def normalize_rows(rows: list[list[Any]]) -> list[list[str]]:
    normalized = [[norm(cell) for cell in row] for row in rows]
    normalized = [row for row in normalized if any(row)]
    if not normalized:
        return []
    width = max(len(row) for row in normalized)
    return [row + [""] * (width - len(row)) for row in normalized]


def normalize_indexed_rows(rows: list[list[Any]]) -> list[tuple[int, list[str]]]:
    indexed = [
        (idx, [norm(cell) for cell in row])
        for idx, row in enumerate(rows, start=1)
        if any(norm(cell) for cell in row)
    ]
    if not indexed:
        return []
    width = max(len(row) for _, row in indexed)
    return [(idx, row + [""] * (width - len(row))) for idx, row in indexed]


def header_like(row: list[str]) -> bool:
    filled = [c for c in row if c]
    if not filled:
        return False
    return len(filled) >= min(3, max(1, len(row))) or any(re.search(r"\b(name|rank|role|member|title|planet|control|type|description|notes?)\b", c, re.I) for c in filled)


def row_name(row: list[str], headers: list[str]) -> str:
    for preferred in ("name", "member", "character", "planet", "title", "asset", "item"):
        for idx, header in enumerate(headers):
            if preferred in norm_key(header).split("_") and idx < len(row) and row[idx]:
                return row[idx]
    return next((cell for cell in row if cell), "")


def looks_like_person_name(value: str) -> bool:
    clean = norm(value)
    words = re.findall(r"[A-Za-z][A-Za-z'’-]*", clean)
    if not words or len(words) > 6:
        return False
    if re.search(r"\b(Darth|Lord|Moff|Grand Moff|Emperor|Darth|Master|Inquisitor|Watcher|Agent|Captain|Commander)\b", clean, re.I):
        return True
    return len(words) >= 2 and all(w[:1].isupper() for w in words[: min(3, len(words))])


def extract_sheet_records(file_entry: dict, payload: dict) -> list[dict]:
    records: list[dict] = []
    for sheet_title, raw_rows in payload.get("values", {}).items():
        indexed_rows = normalize_indexed_rows(raw_rows)
        if not indexed_rows:
            continue
        rows = [row for _, row in indexed_rows]
        headers = rows[0] if header_like(rows[0]) else [f"Column {i + 1}" for i in range(len(rows[0]))]
        data = indexed_rows[1:] if headers == rows[0] and header_like(rows[0]) else indexed_rows
        for pos, row in data:
            if not any(row):
                continue
            fields = {headers[i] if i < len(headers) and headers[i] else f"Column {i + 1}": v for i, v in enumerate(row) if v}
            name = row_name(row, headers)
            if should_skip_name(name):
                continue
            rtype = classify_record(name, fields, file_entry.get("name", ""), sheet_title)
            if rtype == "entity" and re.search(r"\b(council|military|academy|intelligence|inquisition|legion|faction|roster)\b", sheet_title + " " + file_entry.get("name", ""), re.I):
                rtype = "roster"
            src = source_for(file_entry, sheet_title=sheet_title, row_numbers=[pos])
            records.append(make_record(rtype, name, fields, src, aliases=[sheet_title, file_entry.get("name", "")], confidence=0.74))
            if rtype != "entity":
                records.append(make_record("entity", name, fields, src, aliases=[rtype, sheet_title], confidence=0.62))

        # Adjacent pair extraction for visually structured roster tabs: name in a cell, role/description below it.
        for col in range(len(rows[0])):
            col_cells = [(original_idx, row[col] if col < len(row) else "") for original_idx, row in indexed_rows]
            nonempty = [(r, c) for r, c in col_cells if c]
            for (r1, c1), (r2, c2) in zip(nonempty, nonempty[1:]):
                if r2 - r1 > 4 or should_skip_name(c1) or should_skip_name(c2):
                    continue
                c1_words = toks(c1)
                c2_words = set(toks(c2))
                looks_name = len(c1_words) <= 5 and (any(w in c1.lower() for w in ["darth", "lord"]) or not (c2_words & ROLE_WORDS))
                looks_role = bool(c2_words & ROLE_WORDS) or re.search(r"\b(male|female|emperor|council|minister|director|commander|overseer|inquisitor|lord)\b", c2, re.I)
                if looks_like_person_name(c2) and not re.search(r"\b(council|minister|director|commander|overseer|inquisitor|emperor|sphere|moff|officer|legatus|praefectus)\b", c2, re.I):
                    continue
                if not looks_name or not looks_role:
                    continue
                fields = {"group": sheet_title, "role_or_description": c2, "column": str(col + 1)}
                src = source_for(file_entry, sheet_title=sheet_title, row_numbers=[r1, r2])
                records.append(make_record("roster", c1, fields, src, aliases=[sheet_title, c2], confidence=0.86))
                records.append(make_record("entity", c1, fields, src, aliases=[sheet_title, c2], confidence=0.72))
    return records


def extract_records_from_file(file_entry: dict) -> list[dict]:
    export_path = Path(file_entry.get("exportPath", ""))
    if not export_path.exists():
        return []
    if file_entry.get("mimeType") == DOC_MIME:
        return extract_doc_records(file_entry, export_path.read_text(encoding="utf-8", errors="replace"))
    if file_entry.get("mimeType") == SHEET_MIME:
        return extract_sheet_records(file_entry, json.loads(export_path.read_text(encoding="utf-8")))
    return []


def write_jsonl_atomic(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
    with open(fd, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    Path(tmp_name).replace(path)


def rebuild_record_files(file_entries: list[dict]) -> dict:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    grouped = {kind: {} for kind in RECORD_KINDS}
    counts_by_file = defaultdict(Counter)
    for file_entry in file_entries:
        for record in extract_records_from_file(file_entry):
            kind = record.get("record_type", "entity")
            if kind not in grouped:
                kind = "entity"
                record["record_type"] = "entity"
            grouped[kind][record["record_id"]] = record
            counts_by_file[file_entry.get("id")][kind] += 1
    counts_by_type = {}
    for kind, filename in RECORD_KINDS.items():
        rows = sorted(grouped[kind].values(), key=lambda r: (r.get("source", {}).get("title") or "", r.get("name") or ""))
        write_jsonl_atomic(RECORDS_DIR / filename, rows)
        counts_by_type[kind] = len(rows)
    manifest = {
        "extraction_version": EXTRACTION_VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "counts_by_type": counts_by_type,
        "total_records": sum(counts_by_type.values()),
        "source_files": len(file_entries),
        "counts_by_file": {fid: dict(counter) for fid, counter in counts_by_file.items()},
    }
    tmp = RECORD_MANIFEST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(RECORD_MANIFEST_PATH)
    return manifest


def load_records() -> list[dict]:
    records = []
    for filename in RECORD_KINDS.values():
        path = RECORDS_DIR / filename
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
    return records


def bm25_record_scores(records: list[dict], terms: list[str]) -> dict[str, float]:
    if not records or not terms:
        return {}
    doc_counts = {}
    lengths = []
    dfs = Counter()
    for record in records:
        text = record_to_text(record)
        ts = toks(text)
        counts = Counter(ts)
        doc_counts[record["record_id"]] = counts
        lengths.append(len(ts) or 1)
        for term in set(ts):
            dfs[term] += 1
    avgdl = sum(lengths) / max(1, len(lengths))
    scores = {}
    for record, dl in zip(records, lengths):
        score = 0.0
        counts = doc_counts[record["record_id"]]
        for term in terms:
            tf = counts.get(term, 0)
            if not tf:
                continue
            idf = math.log(1 + (len(records) - dfs[term] + 0.5) / (dfs[term] + 0.5))
            score += idf * (tf * 2.5) / (tf + 1.5 * (0.25 + 0.75 * dl / avgdl))
        if score:
            scores[record["record_id"]] = score
    return scores


def record_to_text(record: dict) -> str:
    source = record.get("source", {})
    fields = record.get("fields", {})
    return " ".join([
        record.get("name", ""), " ".join(record.get("aliases", [])), record.get("record_type", ""), record.get("summary", ""),
        " ".join(f"{k} {v}" for k, v in fields.items()), source.get("title", ""), source.get("path", ""), source.get("sheet_title", ""), source.get("section", ""), record.get("search_text", ""),
    ])


def search_records(query: str, limit: int = 20, records: list[dict] | None = None) -> list[dict]:
    records = records if records is not None else load_records()
    terms = toks(query)
    if not records or not terms:
        return []
    q = query.lower()
    subject = query_subject(query)
    desired_asset = asset_subtype_query(query)
    bm25 = bm25_record_scores(records, terms)
    hits = []
    for record in records:
        text = record_to_text(record).lower()
        name_text = " ".join([record.get("name", ""), " ".join(record.get("aliases", []))]).lower()
        term_hits = sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", text))
        if not term_hits and record["record_id"] not in bm25 and q not in text:
            continue
        name_hits = sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", name_text))
        phrase = 3.5 if q in text else 0.0
        score = phrase + bm25.get(record["record_id"], 0.0) + name_hits * 1.5 + term_hits / max(1, len(terms)) + record.get("confidence", 0.5)
        kind = record.get("record_type")
        source_title = record.get("source", {}).get("title", "")
        noisy_tracking_source = bool(re.search(r"\b(Saber Mastery|Combat Form Tracking|Master Ability List)\b", source_title, re.I))
        if kind == "roster" and re.search(r"\b(who|member|members|council|roster|faction|academy|inquisition|military|intelligence|legion)\b", q):
            score += 1.0
        if kind == "planet" and re.search(r"\b(planet|world|control|imperial|controlled|planets)\b", q):
            score += 1.0
        if kind == "rule" and re.search(r"\b(dice|roll|rank|rule|progression|ability|forms?|requirement)\b", q):
            score += 1.0
        if kind == "asset" and re.search(r"\b(ship|vehicle|droid|beast|crystal|saber|equipment|asset|artifact|item|weapon|armor|forge)\b", q):
            score += 1.0
        if subject and source_title_matches_subject(record, subject):
            score += 8.0
        if subject and exact_source_title_matches_subject(record, subject):
            score += 18.0
        if subject:
            record_name = str(record.get("name") or "").strip().lower()
            subject_norm = subject.strip().lower()
            if record_name == subject_norm or record_name.startswith(subject_norm + ",") or record_name.startswith(subject_norm + " -"):
                score += 34.0
            if re.match(r"^[\u201c\"']", str(record.get("name") or "")) and record_name != subject_norm:
                score -= 16.0
        if desired_asset:
            if kind != "asset":
                score -= 10.0
            elif asset_subtype_matches(record, desired_asset):
                score += 14.0
            else:
                score -= 8.0
        if noisy_tracking_source and (person_lookup_query(query) or asset_detail_query(query)) and not re.search(r"\b(saber|form|forms|combat|ability|abilities|mastery|rank|training|rule|rules)\b", q):
            score -= 22.0
        if person_lookup_query(query) and profile_record_score(record) >= 4:
            score += 18.0
        if re.search(r"\bpraetorian officers?\b", q):
            rank_text = " ".join([record.get("name", ""), record.get("summary", ""), " ".join(str(v) for v in record.get("fields", {}).values())]).lower()
            if re.search(r"\b(legatus|praefectus|tribune|prefect)\b", rank_text):
                score += 24.0
            if profile_record_score(record) >= 4:
                score -= 18.0
        if generic_record_name(record):
            score -= 2.5
        if person_lookup_query(query) and not asset_detail_query(query) and asset_record_score(record) >= 2:
            score -= 35.0
        item = dict(record)
        item["relevance_score"] = round(score, 4)
        hits.append(item)
    if subject:
        for item in hits:
            item_name_norm = str(item.get("name") or "").strip().lower()
            subject_norm = subject.strip().lower()
            if item_name_norm == subject_norm or item_name_norm.startswith(subject_norm + ",") or item_name_norm.startswith(subject_norm + " -"):
                item["relevance_score"] = round(item.get("relevance_score", 0) + 45.0, 4)
            if re.match(r"^[\u201c\"']", str(item.get("name") or "")) and item_name_norm != subject_norm:
                item["relevance_score"] = round(item.get("relevance_score", 0) - 24.0, 4)
            if exact_name_matches_subject(item, subject):
                boost = 80.0
                if desired_asset and not asset_subtype_matches(item, desired_asset):
                    boost = 8.0
                item["relevance_score"] = round(item.get("relevance_score", 0) + boost, 4)
            elif source_title_matches_subject(item, subject) and (profile_record_score(item) >= 2 or exact_source_title_matches_subject(item, subject)):
                item["relevance_score"] = round(item.get("relevance_score", 0) + 55.0, 4)
            elif name_matches_subject(item, subject):
                boost = 30.0
                if desired_asset and not asset_subtype_matches(item, desired_asset):
                    boost = 4.0
                item["relevance_score"] = round(item.get("relevance_score", 0) + boost, 4)
            elif all(term in record_to_text(item).lower() for term in toks(subject)):
                item["relevance_score"] = round(item.get("relevance_score", 0) - 12.0, 4)
            if person_lookup_query(query) and generic_record_name(item):
                item["relevance_score"] = round(item.get("relevance_score", 0) - 18.0, 4)
            if person_lookup_query(query) and item.get("record_type") == "rule" and not re.search(r"\b(rule|rules|ability|abilities|form|forms|combat|saber|rank|requirement|requirements|roll|dice)\b", q):
                item["relevance_score"] = round(item.get("relevance_score", 0) - 25.0, 4)
    hits.sort(key=lambda r: r["relevance_score"], reverse=True)
    return hits[:limit]



def query_subject(query: str) -> str:
    q = query.strip()
    patterns = [
        r"what do (?:you|we) know about\s+([^?.!]+)[?.!]*$",
        r"tell me about\s+([^?.!]+)[?.!]*$",
        r"what\s+(?:ships?|starships?|vehicles?|droids?|beasts?|assets?|items?|equipment|weapons?)\s+does\s+(.+?)\s+have[?.!]*$",
        r"what(?:'s|\s+is|\s+are)\s+(?:the\s+)?([^?.!]+)[?.!]*$",
        r"(?:rules?|requirements?|details|info|information)\s+(?:for|on|about)\s+([^?.!]+)[?.!]*$",
        r"what (?:are|is) (?:the )?(?:rules?|requirements?|details|info|information)\s+(?:for|on|about)\s+([^?.!]+)[?.!]*$",
        r"who(?:'s|\s+is|\s+are|\s+was|\s+were)\s+(.+?)[?.!]*$",
    ]
    for pattern in patterns:
        m = re.search(pattern, q, re.I)
        if m:
            subject = re.sub(r"^(?:the|a|an)\s+", "", m.group(1).strip(), flags=re.I)
            return re.sub(r"[^A-Za-z0-9' -]+", " ", subject).strip()
    return ""


def name_matches_subject(record: dict, subject: str) -> bool:
    if not subject:
        return False
    subject_terms = toks(subject)
    if not subject_terms:
        return False
    names = [record.get("name", ""), *record.get("aliases", [])]
    for name in names:
        name_text = name.lower()
        if all(re.search(rf"\b{re.escape(term)}\b", name_text) for term in subject_terms):
            return True
    fields = record.get("fields", {})
    for key in ("member_name", "name"):
        value = fields.get(key, "").lower()
        if value and all(re.search(rf"\b{re.escape(term)}\b", value) for term in subject_terms):
            return True
    return False


def primary_name_matches_subject(record: dict, subject: str) -> bool:
    subject_terms = toks(subject)
    if not subject_terms:
        return False
    name_text = record.get("name", "").lower()
    return all(re.search(rf"\b{re.escape(term)}\b", name_text) for term in subject_terms)


def exact_name_or_field_match(record: dict, subject: str) -> bool:
    wanted = norm(subject).lower()
    if not wanted:
        return False
    values = [record.get("name", ""), *record.get("aliases", [])]
    fields = record.get("fields", {})
    values.extend(fields.get(key, "") for key in ("name", "full_name", "member_name", "owner"))
    for value in values:
        if norm(value).lower() == wanted:
            return True
    return False


def exact_name_matches_subject(record: dict, subject: str) -> bool:
    if not subject:
        return False
    normalized_subject = re.sub(r"\s+", " ", subject.lower()).strip()
    normalized_name = re.sub(r"\s+", " ", record.get("name", "").lower()).strip()
    return normalized_name == normalized_subject


def source_title_matches_subject(record: dict, subject: str) -> bool:
    subject_terms = toks(subject)
    if not subject_terms:
        return False
    source = record.get("source", {})
    title_text = " ".join([source.get("title", ""), source.get("path", "")]).lower()
    return all(re.search(rf"\b{re.escape(term)}\b", title_text) for term in subject_terms)


def exact_source_title_matches_subject(record: dict, subject: str) -> bool:
    source = record.get("source", {})
    normalized_subject = re.sub(r"[^a-z0-9]+", " ", subject.lower()).strip()
    for value in (source.get("title", ""), source.get("path", "")):
        normalized_title = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
        if normalized_title == normalized_subject or normalized_title.endswith(" " + normalized_subject):
            return True
    return False


def profile_record_score(record: dict) -> int:
    fields = record.get("fields", {})
    profile_keys = {"name", "age", "birthplace", "species", "height", "weight", "title", "titles", "rank", "faction"}
    score = sum(1 for key in fields if key in profile_keys or key in PROFILE_FIELDS)
    if fields.get("profile_type") == "character":
        score += 4
    return score


def asset_record_score(record: dict) -> int:
    fields = record.get("fields", {})
    return sum(1 for key in fields if key in ASSET_FIELDS or key.startswith("mod_slot"))


def asset_subtype_query(query: str) -> str:
    q = query.lower()
    if re.search(r"\bships?|starships?|fleet|hyperdrive|hull\b", q):
        return "ship"
    if re.search(r"\bdroids?\b", q):
        return "droid"
    if re.search(r"\bbeasts?|pets?\b", q):
        return "beast"
    if re.search(r"\bcrystals?|kyber\b", q):
        return "crystal"
    if re.search(r"\bartifacts?|items?\b", q):
        return "artifact"
    if re.search(r"\bweapons?|armor|equipment\b", q):
        return "equipment"
    return ""


def asset_subtype_matches(record: dict, subtype: str) -> bool:
    if not subtype:
        return True
    if record.get("record_type") != "asset":
        return False
    fields = record.get("fields", {})
    hay = " ".join([
        record.get("name", ""),
        " ".join(record.get("aliases", [])),
        record.get("summary", ""),
        fields.get("asset_subtype", ""),
        " ".join(fields.keys()),
        " ".join(str(v) for v in fields.values()),
    ]).lower()
    if subtype == "ship":
        return bool(re.search(r"\b(ship|starship|vehicle|fleet|hyperdrive|hull)\b", hay))
    if subtype == "droid":
        return "droid" in hay
    if subtype == "beast":
        return bool(re.search(r"\b(beast|pet|creature)\b", hay))
    if subtype == "crystal":
        return bool(re.search(r"\b(crystal|kyber|white|black)\b", hay))
    if subtype == "artifact":
        return bool(re.search(r"\b(artifact|item|ring|scepter|medal|crown|sword|necklace)\b", hay))
    if subtype == "equipment":
        return bool(re.search(r"\b(equipment|weapon|armor|saber|rifle|sword|gauntlet)\b", hay))
    return subtype in hay


def person_lookup_query(query: str) -> bool:
    return bool(re.search(r"\b(who(?:'s|\s+is|\s+was)?|tell me about|what do (?:you|we) know about)\b", query.lower()))


def document_overview_query(query: str) -> bool:
    q = query.lower()
    if not re.search(r"\b(tell me about|what is|what are|explain|overview|summarize)\b", q):
        return False
    return bool(re.search(r"\b(codex|guide|manual|compendium|forging|forge|war forge|know your|rules|system|program|faction|academy|inquisition|enclave|legion|ministry)\b", q))


def asset_detail_query(query: str) -> bool:
    return bool(re.search(r"\b(ship|starship|vehicle|droid|beast|crystal|saber|equipment|asset|artifact|item|weapon|armor|hull|hyperdrive|fleet|forge)\b", query.lower()))


def unique_records_by_name(records: list[dict]) -> list[dict]:
    unique = []
    seen = set()
    for record in records:
        key = norm(record.get("name", "")).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def control_value(query: str) -> str | None:
    q = query.lower()
    if re.search(r"\b(imperial|empire|we control|our control|controlled by us|controlled planets)\b", q):
        return "imperial"
    if "republic" in q:
        return "republic"
    if "neutral" in q:
        return "neutral"
    if "hutt" in q:
        return "hutt"
    if "contested" in q:
        return "contested"
    return None


def group_terms(query: str) -> set[str]:
    return set(toks(query)) - {"member", "members", "officer", "officers", "current", "list", "count", "many"}


def group_phrase(query: str) -> str:
    q = query.lower()
    for pattern in [
        r"members of (?:the )?(.+?)[?.!]*$",
        r"who are (?:the )?(?:current )?members of (?:the )?(.+?)[?.!]*$",
        r"who are (?:the )?(?:current )?(.+?)[?.!]*$",
        r"list (?:the )?(.+?)[?.!]*$",
    ]:
        m = re.search(pattern, q)
        if m:
            return re.sub(r"[^a-z0-9 ]+", " ", m.group(1)).strip()
    if "grand council" in q:
        return "grand council"
    return ""


def record_source(record: dict) -> dict:
    source = record.get("source", {})
    return {
        "title": source.get("title"),
        "section": source.get("sheet_title") or source.get("section") or source.get("path"),
        "source_url": source.get("url"),
        "path": source.get("path"),
        "modified_time": source.get("modified_time"),
    }


def records_to_results(records: list[dict]) -> list[dict]:
    rows = []
    for record in records:
        source = record.get("source", {})
        fields = record.get("fields", {})
        excerpt = f"Record: {record.get('name')}\nType: {record.get('record_type')}\n" + "\n".join(f"- {k.replace('_', ' ')}: {v}" for k, v in list(fields.items())[:12])
        rows.append({
            "record_id": record.get("record_id"),
            "record_type": record.get("record_type"),
            "title": source.get("title"),
            "path": source.get("path"),
            "section": source.get("sheet_title") or source.get("section"),
            "source_url": source.get("url"),
            "modified_time": source.get("modified_time"),
            "relevance_score": record.get("relevance_score", 0),
            "match_type": "structured_record",
            "excerpt": excerpt,
        })
    return rows


def answer_from_records(query: str, hits: list[dict]) -> dict | None:
    q = query.lower()
    if not hits:
        return None
    top = hits[0]
    if top.get("relevance_score", 0) < 2.2:
        return None
    wants_count = bool(re.search(r"\b(how many|count|number of)\b", q))
    wants_list = bool(re.search(r"\b(list|who are|which|what are all|members of|current members)\b", q))
    planet_query = bool(re.search(r"\b(planet|planets|world|worlds|control|controlled|imperial planets|republic planets|hutt planets|neutral planets|contested planets|hyperlane|climate|landscape)\b", q))
    sources = []
    seen_sources = set()

    def add_source(record: dict) -> str:
        src = record_source(record)
        key = (src.get("title"), src.get("section"), src.get("source_url"))
        if key not in seen_sources:
            seen_sources.add(key)
            sources.append(src)
        return f"[{len(sources)}]"

    planet_control = control_value(query)
    if wants_count and planet_query:
        records = [h for h in load_records() if h.get("record_type") == "planet" and h.get("fields", {}).get("control")]
        if planet_control:
            records = [r for r in records if planet_control in (r.get("fields", {}).get("control", "") + " " + r.get("summary", "")).lower()]
        records = unique_records_by_name(records)
        if records:
            cite = add_source(records[0])
            label = f" {planet_control}" if planet_control else ""
            names = ", ".join(r.get("name", "") for r in records[:20])
            extra = f" They are: {names}." if len(records) <= 20 else ""
            return {"status": "answered", "answer": f"The sources list {len(records)}{label} planet records.{extra} {cite}", "sources": sources, "confidence": "high"}

    if wants_list and planet_query:
        records = [h for h in load_records() if h.get("record_type") == "planet" and h.get("fields", {}).get("control")]
        if planet_control:
            records = [r for r in records if planet_control in (r.get("fields", {}).get("control", "") + " " + r.get("summary", "")).lower()]
        records = unique_records_by_name(records)
        if records:
            cite = add_source(records[0])
            names = ", ".join(r.get("name", "") for r in records[:40])
            return {"status": "answered", "answer": f"The matching planet records are: {names}. {cite}", "sources": sources, "confidence": "high"}

    if wants_list and any(h.get("record_type") == "roster" for h in hits) and not re.search(r"\bpraetorian officers?\b", q):
        phrase = group_phrase(query)
        phrase_terms = set(toks(phrase))
        rosters = [h for h in load_records() if h.get("record_type") == "roster"]
        filtered = []
        for r in rosters:
            src = r.get("source", {})
            sheet_path = " ".join([src.get("sheet_title", ""), src.get("title", ""), src.get("path", "")]).lower()
            if phrase_terms and not all(t in sheet_path for t in phrase_terms):
                continue
            if phrase and r.get("name", "").lower() == phrase:
                continue
            # Prefer generated adjacent-pair records for visual rosters; they carry the paired role/description.
            if phrase_terms and not r.get("fields", {}).get("role_or_description"):
                continue
            filtered.append(r)
        if not filtered:
            if phrase_terms and not re.search(r"\bpraetorian officers?\b", q):
                return None
            filtered = [h for h in hits if h.get("record_type") == "roster" and h.get("fields", {}).get("role_or_description")][:20]
        if len(filtered) >= 2:
            parts = []
            for r in filtered[:25]:
                cite = add_source(r)
                desc = r.get("fields", {}).get("role_or_description") or r.get("fields", {}).get("role") or r.get("summary", "")
                parts.append(f"{r.get('name')}" + (f" - {desc}" if desc else "") + f" {cite}")
            return {"status": "answered", "answer": "The matching roster entries are: " + "; ".join(parts) + ".", "sources": sources, "confidence": "high"}

    if wants_list and re.search(r"\bpraetorian officers?\b", q):
        officer_records = []
        for record in load_records():
            text = record_to_text(record).lower()
            fields = record.get("fields", {})
            rank_text = " ".join([record.get("name", ""), fields.get("rank", ""), fields.get("title", ""), fields.get("description", ""), fields.get("notes", "")]).lower()
            if not re.search(r"\b(legatus|praefectus|tribune|prefect)\b", rank_text):
                continue
            source_title = record.get("source", {}).get("title") or ""
            if source_title != "Know Your Empire" and not ("officer" in rank_text and "praetorian" in text):
                continue
            officer_records.append(record)
        officer_records = unique_records_by_name(officer_records)
        if officer_records:
            parts = []
            for record in officer_records[:12]:
                cite = add_source(record)
                fields = record.get("fields", {})
                rank = fields.get("rank") or fields.get("title") or record.get("name")
                desc = fields.get("notes") or fields.get("description") or record.get("summary", "")
                parts.append(f"{record.get('name')} - {rank}" + (f": {desc}" if desc and desc != rank else "") + f" {cite}")
            return {"status": "answered", "answer": "The Praetorian officer records include: " + "; ".join(parts) + ".", "sources": sources, "confidence": "high"}

    if wants_count and any(h.get("record_type") == "roster" for h in hits):
        terms = group_terms(query)
        rosters = [r for r in load_records() if r.get("record_type") == "roster" and all(t in record_to_text(r).lower() for t in terms)]
        if rosters:
            cite = add_source(rosters[0])
            return {"status": "answered", "answer": f"The sources contain {len(rosters)} matching roster records. {cite}", "sources": sources, "confidence": "high"}

    subject = query_subject(query)
    desired_asset = asset_subtype_query(query)
    if subject and desired_asset:
        subject_terms = toks(subject)
        assets = [
            h for h in hits
            if h.get("record_type") == "asset"
            and asset_subtype_matches(h, desired_asset)
            and (not subject_terms or all(re.search(rf"\b{re.escape(t)}\b", record_to_text(h).lower()) for t in subject_terms))
        ]
        if assets:
            strict_assets = [record for record in assets if exact_name_or_field_match(record, subject)]
            if strict_assets:
                assets = strict_assets
            else:
                exact_assets = [record for record in assets if name_matches_subject(record, subject)]
                if exact_assets:
                    assets = exact_assets
            parts = []
            for record in assets[:8]:
                cite = add_source(record)
                detail = summarize_fields(record.get("fields", {})) or record.get("summary", "")
                parts.append(f"{record.get('name')}" + (f" - {detail}" if detail else "") + f" {cite}")
            return {"status": "answered", "answer": "The matching asset records are: " + "; ".join(parts) + ".", "sources": sources, "confidence": "high"}

    if subject:
        direct_hits = [h for h in hits if name_matches_subject(h, subject)]
        if direct_hits:
            if person_lookup_query(query) and not asset_detail_query(query):
                def identity_rank(record: dict) -> tuple:
                    fields = record.get("fields", {})
                    has_title = bool(fields.get("title") or fields.get("titles") or fields.get("rank"))
                    has_affiliation = bool(fields.get("factions") or fields.get("allegiances") or fields.get("occupation_s"))
                    is_character = fields.get("profile_type") == "character"
                    return (has_title, has_affiliation, is_character, profile_record_score(record), record.get("relevance_score", 0))
                direct_hits.sort(key=identity_rank, reverse=True)
            top = direct_hits[0]
        else:
            return None
    else:
        return None

    if top.get("record_type") in {"planet", "rule", "asset", "roster", "entity"} and top.get("relevance_score", 0) >= 3.0:
        desired_asset = asset_subtype_query(query)
        top_source = top.get("source", {}).get("title", "")
        if document_overview_query(query) and source_title_matches_subject(top, subject) and not primary_name_matches_subject(top, subject):
            return None
        if desired_asset:
            if top.get("record_type") != "asset" or not asset_subtype_matches(top, desired_asset):
                return None
        if (person_lookup_query(query) or asset_detail_query(query)) and re.search(r"\b(Saber Mastery|Combat Form Tracking|Master Ability List)\b", top_source, re.I) and not re.search(r"\b(saber|form|forms|combat|ability|abilities|mastery|rank|training|rule|rules)\b", q):
            return None
        if person_lookup_query(query) and generic_record_name(top):
            return None
        if person_lookup_query(query) and not asset_detail_query(query) and asset_record_score(top) >= 2:
            return None
        if person_lookup_query(query) and top.get("record_type") == "rule" and not re.search(r"\b(rule|rules|ability|abilities|form|forms|combat|saber|rank|requirement|requirements|roll|dice)\b", q):
            return None
        if person_lookup_query(query) and profile_record_score(top) < 2 and not re.search(r"\b(roster|officer|member|rank|title)\b", q):
            fields_for_identity = top.get("fields", {})
            if not (fields_for_identity.get("title") or fields_for_identity.get("titles") or fields_for_identity.get("rank") or fields_for_identity.get("notes")):
                return None
        terms = toks(subject or query)
        text = record_to_text(top).lower()
        coverage = sum(1 for t in terms if re.search(rf"\b{re.escape(t)}\b", text)) / max(1, len(terms))
        if coverage < 0.55:
            return None
        fields = top.get("fields", {})
        if person_lookup_query(query) and not asset_detail_query(query):
            detail = summarize_identity_fields(fields) or summarize_fields(fields) or top.get("summary")
        else:
            detail = summarize_fields(fields) or top.get("summary")
        display_name = fields.get("name") or fields.get("full_name") or top.get("name")
        if not detail or detail.strip().lower() in {"a matching source record exists", "a matching source record exists."}:
            return None
        normalized_detail = re.sub(r"\s+", " ", detail.strip().lower()).rstrip(".")
        normalized_name = re.sub(r"\s+", " ", top.get("name", "").strip().lower())
        normalized_subject = re.sub(r"\s+", " ", (subject or "").strip().lower())
        if normalized_detail in {f"role: {normalized_name}", f"role: {normalized_subject}"}:
            return None
        cite = add_source(top)
        return {"status": "answered", "answer": f"{display_name}: {detail}. {cite}", "sources": sources, "confidence": "high"}
    return None
