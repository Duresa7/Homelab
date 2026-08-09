#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import chromadb

from lore_config import (
    CHUNKS_PATH,
    COLLECTION_NAME,
    DOC_MIME,
    EMBED_MODEL,
    EXPORT_DIR,
    FOLDER_MIME,
    GWS_BIN,
    INDEX_DIR,
    LOG_DIR,
    MANIFEST_PATH,
    RECORDS_DIR,
    RECORD_MANIFEST_PATH,
    MAX_CHARS,
    OLLAMA_BASE_URL,
    OVERLAP_CHARS,
    ROOT_DIR,
    ROOT_FOLDER_ID,
    ROOT_FOLDER_NAME,
    SHEET_MIME,
    STATE_DIR,
    SOURCE_MAP_PATH,
)
from lore_records import rebuild_record_files
from lore_source_map import build_source_map


SYNC_STATUS_PATH = STATE_DIR / "sync_status.json"
INGESTION_VERSION = "2026-05-09-doc-tables-v1"


def ensure_dirs() -> None:
    for path in [
        ROOT_DIR,
        EXPORT_DIR / "docs",
        EXPORT_DIR / "sheets",
        EXPORT_DIR / "metadata",
        STATE_DIR,
        INDEX_DIR,
        LOG_DIR,
        RECORDS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    print(f"{stamp} {message}", flush=True)


def clean_json_stdout(stdout: str) -> str:
    lines = [line for line in stdout.splitlines() if not line.startswith("Using keyring backend:")]
    text = "\n".join(lines).strip()
    if not text:
        return text
    first = min([i for i in [text.find("{"), text.find("[")] if i >= 0] or [0])
    return text[first:].strip()


def run_gws(*args: str, output: Path | None = None) -> str:
    env = os.environ.copy()
    env.setdefault("HOME", "/home/REDACTED_DEPLOYMENT_USER")
    env.setdefault("GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND", "file")
    cmd = [str(GWS_BIN), *args]
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--output", str(output)])
    last_error = None
    for attempt in range(1, 5):
        proc = subprocess.run(cmd, text=True, capture_output=True, env=env)
        if proc.returncode == 0:
            return clean_json_stdout(proc.stdout)
        last_error = (
            f"gws failed ({proc.returncode}) for {' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
        retryable = any(token in proc.stdout + proc.stderr for token in ["503", "429", "500", "temporarily", "unavailable"])
        if not retryable or attempt == 4:
            break
        log(f"gws transient failure; retrying attempt {attempt + 1}/4")
        time.sleep(2 * attempt)
    raise RuntimeError(last_error)


def gws_json(*args: str) -> dict:
    text = run_gws(*args)
    if not text:
        return {}
    return json.loads(text)


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"root_folder_id": ROOT_FOLDER_ID, "files": {}}
    return json.loads(MANIFEST_PATH.read_text())


def save_manifest(manifest: dict) -> None:
    tmp = MANIFEST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    tmp.replace(MANIFEST_PATH)


def save_json_atomic(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
    tmp.replace(path)


def corpus_version(manifest: dict, record_manifest: dict, chunk_count: int) -> str:
    files = manifest.get("files", {})
    parts = [
        str(chunk_count),
        str(record_manifest.get("total_records", "")),
        str(record_manifest.get("extraction_version", "")),
    ]
    for file_id in sorted(files):
        file_entry = files[file_id]
        parts.extend([
            file_id,
            file_entry.get("modifiedTime", ""),
            file_entry.get("contentHash", ""),
            file_entry.get("mimeType", ""),
        ])
    raw = "\n".join(parts)
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:20]


def ollama_embedding_health() -> dict:
    payload = json.dumps({"model": EMBED_MODEL, "input": "health check"}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        ok = bool(data.get("embeddings"))
        return {"ok": ok, "model": EMBED_MODEL, "base_url": OLLAMA_BASE_URL, "latency_ms": round((time.time() - start) * 1000)}
    except Exception as exc:
        return {"ok": False, "model": EMBED_MODEL, "base_url": OLLAMA_BASE_URL, "error": str(exc)}


def drive_list_children(folder_id: str) -> list[dict]:
    files: list[dict] = []
    page_token = None
    while True:
        params = {
            "pageSize": 1000,
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True,
            "q": f"'{folder_id}' in parents and trashed=false",
            "fields": "nextPageToken,files(id,name,mimeType,modifiedTime,webViewLink,parents,driveId)",
            "orderBy": "folder,name",
        }
        if page_token:
            params["pageToken"] = page_token
        page = gws_json("drive", "files", "list", "--params", json.dumps(params))
        files.extend(page.get("files", []))
        page_token = page.get("nextPageToken")
        if not page_token:
            return files


def discover_files() -> list[dict]:
    root = {
        "id": ROOT_FOLDER_ID,
        "name": ROOT_FOLDER_NAME,
        "mimeType": FOLDER_MIME,
        "path": ROOT_FOLDER_NAME,
    }
    queue = [root]
    found: list[dict] = []
    while queue:
        folder = queue.pop(0)
        for item in drive_list_children(folder["id"]):
            item["path"] = f"{folder['path']}/{item['name']}"
            if item.get("mimeType") == FOLDER_MIME:
                queue.append(item)
            elif item.get("mimeType") in {DOC_MIME, SHEET_MIME}:
                found.append(item)
    return found


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")[:80] or "untitled"


def export_doc(file: dict) -> tuple[str, Path]:
    out = EXPORT_DIR / "docs" / f"{file['id']}_{safe_name(file['name'])}.txt"
    params = {"fileId": file["id"], "mimeType": "text/plain"}
    plain_text = ""
    try:
        run_gws("drive", "files", "export", "--params", json.dumps(params), output=out)
        plain_text = out.read_text(errors="replace")
    except RuntimeError as exc:
        log(f"Drive export failed for {file['path']}; trying Docs API fallback: {exc}")
    try:
        doc = gws_json("docs", "documents", "get", "--params", json.dumps({"documentId": file["id"]}))
        api_text = google_doc_to_text(doc)
        # Prefer Docs API text because it preserves embedded tables. Plain export
        # often drops table structure, which caused rank/allowance chart misses.
        if api_text.strip():
            text = api_text
        else:
            text = plain_text
    except Exception as exc:
        log(f"Docs API rich export failed for {file['path']}; using plain export: {exc}")
        text = plain_text
    out.write_text(text)
    return text, out


def _paragraph_text(paragraph: dict) -> str:
    parts = []
    for element in paragraph.get("elements", []):
        run = element.get("textRun")
        if run and run.get("content"):
            parts.append(run["content"])
    return "".join(parts).rstrip("\n")


def _cell_text(cell: dict) -> str:
    pieces: list[str] = []
    for block in cell.get("content", []):
        paragraph = block.get("paragraph")
        if paragraph:
            text = _paragraph_text(paragraph).strip()
            if text:
                pieces.append(text)
            continue
        table = block.get("table")
        if table:
            rows = _table_rows(table)
            for row in rows:
                line = " | ".join(cell for cell in row if cell).strip()
                if line:
                    pieces.append(line)
    return " ".join(pieces).strip()


def _table_rows(table: dict) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.get("tableRows", []):
        cells = [_cell_text(cell) for cell in row.get("tableCells", [])]
        if any(cells):
            rows.append(cells)
    return rows


def rows_to_markdown_table(rows: list[list[str]]) -> str:
    normalized = [["" if cell is None else str(cell) for cell in row] for row in rows]
    width = max((len(row) for row in normalized), default=0)
    if width == 0:
        return "(empty table)"
    normalized = [row + [""] * (width - len(row)) for row in normalized]
    output = []
    for idx, row in enumerate(normalized):
        escaped = [cell.replace("|", "\\|").replace("\n", " ") for cell in row]
        output.append("| " + " | ".join(escaped) + " |")
        if idx == 0:
            output.append("| " + " | ".join(["---"] * width) + " |")
    return "\n".join(output)


def google_doc_to_text(doc: dict) -> str:
    lines: list[str] = []
    table_number = 0
    for block in doc.get("body", {}).get("content", []):
        paragraph = block.get("paragraph")
        if paragraph:
            text = _paragraph_text(paragraph)
            style = paragraph.get("paragraphStyle", {}).get("namedStyleType", "")
            if text and style.startswith("HEADING_"):
                level = {"HEADING_1": "#", "HEADING_2": "##", "HEADING_3": "###"}.get(style, "####")
                lines.append(f"{level} {text.strip()}")
            else:
                lines.append(text)
            continue
        table = block.get("table")
        if table:
            table_number += 1
            rows = _table_rows(table)
            if rows:
                lines.append(f"\n### Table {table_number}")
                lines.append(rows_to_markdown_table(rows))
    return "\n".join(lines).strip() + "\n"


def google_doc_table_chunks(file: dict, export_path: Path, h: str) -> list[dict]:
    try:
        doc = gws_json("docs", "documents", "get", "--params", json.dumps({"documentId": file["id"]}))
    except Exception as exc:
        log(f"warning: could not read Docs API tables for {file.get('path', file.get('name'))}: {exc}")
        return []
    chunks: list[dict] = []
    table_number = 0
    for block in doc.get("body", {}).get("content", []):
        table = block.get("table")
        if not table:
            continue
        table_number += 1
        rows = _table_rows(table)
        if not rows:
            continue
        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        headers = rows[0]
        header_like = sum(1 for cell in headers if cell and len(cell) <= 80) >= max(1, min(2, width))
        data_rows = list(enumerate(rows[1:] if header_like else rows, start=2 if header_like else 1))
        for row_number, row in data_rows:
            pairs = []
            search_parts = []
            for idx, value in enumerate(row):
                value = (value or "").strip()
                if not value:
                    continue
                header = headers[idx].strip() if header_like and idx < len(headers) and headers[idx].strip() else f"Column {column_name(idx)}"
                pairs.append(f"- {header}: {value}")
                search_parts.append(f"{header} {value}")
            if not pairs:
                continue
            primary = next((value for value in row if value), f"Table {table_number} row {row_number}")
            text = "\n".join([
                f"Source: {file['name']}",
                f"Table: {table_number}",
                f"Row: {row_number}",
                f"Primary: {primary}",
                *pairs,
            ])
            digest = hashlib.sha1(f"doctable:{table_number}:{row_number}:{text}".encode()).hexdigest()[:12]
            chunk_id = f"{file['id']}:doctable:{table_number}:{row_number}:{digest}"
            metadata = {
                "file_id": file["id"],
                "name": file["name"],
                "path": file.get("path", file["name"]),
                "section": f"Table {table_number} | Row {row_number}",
                "mimeType": file["mimeType"],
                "modifiedTime": file.get("modifiedTime", ""),
                "webViewLink": file.get("webViewLink", ""),
                "exportPath": str(export_path),
                "contentHash": h,
                "chunk_type": "doc_table_row",
                "table_number": table_number,
                "row_number": row_number,
                "row_primary": primary,
                "search_text": " ".join(search_parts),
                "ingestion_version": INGESTION_VERSION,
            }
            chunks.append({"chunk_id": chunk_id, "text": text, "metadata": metadata})
    return chunks


def quote_sheet_range(title: str) -> str:
    return "'" + title.replace("'", "''") + "'"


def export_sheet(file: dict) -> tuple[str, Path]:
    meta_params = {
        "spreadsheetId": file["id"],
        "fields": "spreadsheetId,spreadsheetUrl,sheets(properties(title,sheetId,index))",
    }
    meta = gws_json("sheets", "spreadsheets", "get", "--params", json.dumps(meta_params))
    titles = [s["properties"]["title"] for s in meta.get("sheets", [])]
    ranges = [quote_sheet_range(title) for title in titles]
    values = {}
    if ranges:
        value_params = {
            "spreadsheetId": file["id"],
            "ranges": ranges,
            "majorDimension": "ROWS",
            "valueRenderOption": "FORMATTED_VALUE",
            "dateTimeRenderOption": "FORMATTED_STRING",
        }
        batch = gws_json("sheets", "spreadsheets", "values", "batchGet", "--params", json.dumps(value_params))
        for title, value_range in zip(titles, batch.get("valueRanges", [])):
            values[title] = value_range.get("values", [])

    out = EXPORT_DIR / "sheets" / f"{file['id']}_{safe_name(file['name'])}.json"
    payload = {"metadata": meta, "values": values}
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    text_parts = [f"# {file['name']}"]
    for title in titles:
        rows = values.get(title, [])
        text_parts.append(f"\n## Sheet: {title}")
        if not rows:
            text_parts.append("(empty)")
            continue
        text_parts.append(rows_to_markdown(rows))
    return "\n".join(text_parts), out


def rows_to_markdown(rows: list[list[object]]) -> str:
    normalized = [["" if cell is None else str(cell) for cell in row] for row in rows]
    width = max((len(row) for row in normalized), default=0)
    if width == 0:
        return "(empty)"
    normalized = [row + [""] * (width - len(row)) for row in normalized]
    output = []
    for idx, row in enumerate(normalized):
        escaped = [cell.replace("|", "\\|").replace("\n", " ") for cell in row]
        output.append("| " + " | ".join(escaped) + " |")
        if idx == 0:
            output.append("| " + " | ".join(["---"] * width) + " |")
    return "\n".join(output)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


# Detects table-of-contents pages (3+ numbered headers in close succession,
# or many "Page N" markers, or many short heading-like lines).
_TOC_RE = re.compile(r"\b\d+[\.\)]\s*[A-Z][a-zA-Z\-' ]{3,}")
_PAGE_MARKER_RE = re.compile(r"\bpage\s+\d+\b|\b\d+\s*/\s*\d+\b", re.I)


def _is_toc_chunk(chunk_text: str) -> bool:
    """Heuristic: chunk is mostly a table-of-contents / index / section list.

    These chunks are pure noise for retrieval — they match many keywords
    (because they list every section) but contain no actual answers. Skip
    them at sync time so they never enter the index.
    """
    sample = chunk_text[:2000]
    toc_hits = len(_TOC_RE.findall(sample))
    if toc_hits >= 4:
        # Lots of "1.Intro 2.Materials 3.Forms" style markers.
        return True
    page_hits = len(_PAGE_MARKER_RE.findall(sample))
    if page_hits >= 4 and len(sample) < 1500:
        # Many "Page 1", "Page 2" markers in short text.
        return True
    # If the chunk is mostly very short lines (like a TOC list), flag it.
    lines = [ln.strip() for ln in chunk_text.splitlines() if ln.strip()]
    if len(lines) >= 6:
        short_lines = sum(1 for ln in lines if len(ln) < 60)
        if short_lines / len(lines) > 0.75:
            # ≥75% of non-empty lines are short — looks like a list/index.
            # But bail if it has actual sentence punctuation.
            sentences = sum(1 for ln in lines if ln.endswith((".", "!", "?")))
            if sentences / len(lines) < 0.2:
                return True
    return False


def _detect_repeated_boilerplate(chunks: list[tuple[str, str]]) -> set[str]:
    """Find lines that repeat across many chunks of the same doc — typically
    headers, footers, or repeated copyright/disclaimer text. Returns the set
    of boilerplate lines (verbatim) so we can strip them.
    """
    if len(chunks) < 4:
        return set()
    line_counts: dict[str, int] = {}
    for _, body in chunks:
        # Track unique lines per chunk so a single chunk's repetition doesn't
        # falsely flag a line.
        seen_in_chunk: set[str] = set()
        for ln in body.splitlines():
            ln_stripped = ln.strip()
            if not ln_stripped or len(ln_stripped) < 10 or len(ln_stripped) > 120:
                continue
            if ln_stripped in seen_in_chunk:
                continue
            seen_in_chunk.add(ln_stripped)
            line_counts[ln_stripped] = line_counts.get(ln_stripped, 0) + 1
    # A line is boilerplate if it appears in ≥40% of chunks and ≥3 chunks.
    threshold = max(3, int(len(chunks) * 0.4))
    return {line for line, count in line_counts.items() if count >= threshold}


def split_text(text: str) -> list[tuple[str, str]]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    if not text:
        return []
    sections: list[tuple[str, str]] = []
    current_title = "Document"
    current_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        is_heading = stripped.startswith("#") or (
            4 <= len(stripped) <= 100
            and stripped.upper() == stripped
            and any(ch.isalpha() for ch in stripped)
            and not stripped.endswith((".", ",", ";", ":"))
        )
        if stripped and is_heading:
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = stripped.lstrip("#").strip()
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))
    if not sections:
        sections = [("Document", text)]

    chunks: list[tuple[str, str]] = []
    for title, body in sections:
        body = body.strip()
        if not body:
            continue
        start = 0
        while start < len(body):
            end = min(start + MAX_CHARS, len(body))
            chunk = body[start:end].strip()
            if chunk:
                chunks.append((title, chunk))
            if end >= len(body):
                break
            start = max(0, end - OVERLAP_CHARS)

    # Smart filter pass: drop TOC-like chunks and strip repeated boilerplate.
    boilerplate = _detect_repeated_boilerplate(chunks)
    cleaned: list[tuple[str, str]] = []
    for title, body in chunks:
        if _is_toc_chunk(body):
            # Skip TOC/index pages entirely — they only confuse retrieval.
            continue
        if boilerplate:
            kept_lines = [
                ln for ln in body.splitlines()
                if ln.strip() not in boilerplate
            ]
            body = "\n".join(kept_lines).strip()
        if not body or len(body) < 40:
            continue
        cleaned.append((title, body))
    return cleaned


def column_name(index: int) -> str:
    name = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def sheet_row_chunks(file: dict, export_path: Path, h: str) -> list[dict]:
    if not export_path.exists():
        return []
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    values = payload.get("values", {})
    chunks: list[dict] = []
    for sheet_title, rows in values.items():
        indexed_rows = [
            (idx, ["" if cell is None else str(cell).strip() for cell in row])
            for idx, row in enumerate(rows, start=1)
            if any("" if cell is None else str(cell).strip() for cell in row)
        ]
        if not indexed_rows:
            continue
        width = max(len(row) for _, row in indexed_rows)
        indexed_rows = [(idx, row + [""] * (width - len(row))) for idx, row in indexed_rows]
        normalized = [row for _, row in indexed_rows]
        headers = normalized[0]
        header_like = sum(1 for cell in headers if cell and len(cell) <= 80) >= max(1, min(3, width))
        data_rows = indexed_rows[1:] if header_like else indexed_rows
        if not data_rows:
            continue
        for original_row_number, row in data_rows:
            pairs = []
            search_parts = []
            for idx, value in enumerate(row):
                if not value:
                    continue
                header = headers[idx] if header_like and headers[idx] else f"Column {column_name(idx)}"
                pairs.append(f"- {header}: {value}")
                search_parts.append(f"{header} {value}")
            if not pairs:
                continue
            primary = next((value for value in row if value), f"Row {original_row_number}")
            text = "\n".join(
                [
                    f"Source: {file['name']}",
                    f"Sheet: {sheet_title}",
                    f"Row: {original_row_number}",
                    f"Primary: {primary}",
                    *pairs,
                ]
            )
            digest = hashlib.sha1(f"{sheet_title}:{original_row_number}:{text}".encode()).hexdigest()[:12]
            chunk_id = f"{file['id']}:sheetrow:{safe_name(sheet_title)}:{original_row_number}:{digest}"
            metadata = {
                "file_id": file["id"],
                "name": file["name"],
                "path": file.get("path", file["name"]),
                "section": f"Sheet: {sheet_title} | Row {original_row_number}",
                "mimeType": file["mimeType"],
                "modifiedTime": file.get("modifiedTime", ""),
                "webViewLink": file.get("webViewLink", ""),
                "exportPath": str(export_path),
                "contentHash": h,
                "chunk_type": "sheet_row",
                "ingestion_version": INGESTION_VERSION,
                "sheet_title": sheet_title,
                "row_number": original_row_number,
                "row_primary": primary,
                "search_text": " ".join(search_parts),
            }
            chunks.append({"chunk_id": chunk_id, "text": text, "metadata": metadata})
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    payload = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        if "embeddings" in data:
            return data["embeddings"]
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        pass

    vectors = []
    for text in texts:
        payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            vectors.append(data["embedding"])
        except Exception as exc:
            log(f"embedding unavailable; skipping vector update for this batch: {exc}")
            return []
    return vectors


def collection():
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def rebuild_chunk_file(all_chunks: list[dict]) -> None:
    tmp = CHUNKS_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        for chunk in all_chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    tmp.replace(CHUNKS_PATH)


def load_chunks() -> list[dict]:
    if not CHUNKS_PATH.exists():
        return []
    chunks = []
    with CHUNKS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def stale_export_paths(active_files: dict) -> list[str]:
    active_paths = {str(entry.get("exportPath")) for entry in active_files.values() if entry.get("exportPath")}
    stale = []
    for folder in (EXPORT_DIR / "docs", EXPORT_DIR / "sheets"):
        if not folder.exists():
            continue
        for path in folder.iterdir():
            if path.is_file() and str(path) not in active_paths:
                stale.append(str(path))
    return sorted(stale)


def index_file_chunks(coll, file_id: str, chunks: list[dict]):
    if os.environ.get("LORE_SYNC_DISABLE_VECTORS") == "1":
        log(f"skipping Chroma vector update for {file_id}; vector updates disabled for this sync run")
        return coll
    # Chroma can segfault in-process on very large file rewrites in this environment.
    # Keep the authoritative JSONL/records updated and let lexical retrieval handle
    # oversized sheets/docs instead of risking the whole sync job.
    if len(chunks) > 350:
        log(f"skipping Chroma vector update for {file_id}; {len(chunks)} chunks is over the safe per-file vector rewrite limit")
        return coll
    if coll is None:
        coll = collection()
    if not chunks:
        try:
            if coll is None:
                coll = collection()
            coll.delete(where={"file_id": file_id})
        except Exception:
            pass
        return coll
    documents = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts(documents)
    if not embeddings:
        log(f"skipping Chroma vector update for {file_id}; lexical chunks and records are still updated")
        return coll
    try:
        coll.delete(where={"file_id": file_id})
    except Exception:
        pass
    coll.add(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=documents,
        embeddings=embeddings,
        metadatas=[chunk["metadata"] for chunk in chunks],
    )
    return coll


def sync() -> int:
    ensure_dirs()
    manifest = load_manifest()
    old_files = manifest.setdefault("files", {})
    coll = None

    log("discovering Google Drive lore files")
    discovered = discover_files()
    seen_ids = {file["id"] for file in discovered}
    log(f"found {len(discovered)} Google Docs/Sheets under {ROOT_FOLDER_NAME}")

    all_chunks = [chunk for chunk in load_chunks() if chunk["metadata"]["file_id"] in seen_ids]
    changed = 0
    skipped = 0

    for file in discovered:
        file_id = file["id"]
        previous = old_files.get(file_id, {})
        if (
            previous.get("modifiedTime") == file.get("modifiedTime")
            and previous.get("mimeType") == file.get("mimeType")
            and previous.get("ingestionVersion") == INGESTION_VERSION
        ):
            skipped += 1
            continue

        log(f"exporting {file['path']}")
        if file["mimeType"] == DOC_MIME:
            text, export_path = export_doc(file)
        elif file["mimeType"] == SHEET_MIME:
            text, export_path = export_sheet(file)
        else:
            continue

        h = content_hash(text)
        file_chunks = []
        for idx, (section, chunk_text) in enumerate(split_text(text)):
            chunk_id = f"{file_id}:{idx}:{hashlib.sha1(chunk_text.encode()).hexdigest()[:12]}"
            metadata = {
                "file_id": file_id,
                "name": file["name"],
                "path": file.get("path", file["name"]),
                "section": section,
                "mimeType": file["mimeType"],
                "modifiedTime": file.get("modifiedTime", ""),
                "webViewLink": file.get("webViewLink", ""),
                "exportPath": str(export_path),
                "contentHash": h,
                "chunk_type": "section",
                "ingestion_version": INGESTION_VERSION,
            }
            file_chunks.append({"chunk_id": chunk_id, "text": chunk_text, "metadata": metadata})
        if file["mimeType"] == SHEET_MIME:
            file_chunks.extend(sheet_row_chunks(file, export_path, h))
        elif file["mimeType"] == DOC_MIME:
            file_chunks.extend(google_doc_table_chunks(file, export_path, h))

        all_chunks = [chunk for chunk in all_chunks if chunk["metadata"]["file_id"] != file_id]
        all_chunks.extend(file_chunks)
        coll = index_file_chunks(coll, file_id, file_chunks)
        old_files[file_id] = {
            "id": file_id,
            "name": file["name"],
            "path": file.get("path", file["name"]),
            "mimeType": file["mimeType"],
            "modifiedTime": file.get("modifiedTime", ""),
            "webViewLink": file.get("webViewLink", ""),
            "exportPath": str(export_path),
            "contentHash": h,
            "chunkCount": len(file_chunks),
            "ingestionVersion": INGESTION_VERSION,
        }
        changed += 1

    removed_ids = set(old_files) - seen_ids
    for file_id in removed_ids:
        log(f"removing deleted/out-of-scope file {file_id}")
        try:
            if coll is None:
                coll = collection()
            coll.delete(where={"file_id": file_id})
        except Exception:
            pass
        old_files.pop(file_id, None)

    rebuild_chunk_file(all_chunks)
    record_manifest = rebuild_record_files(list(old_files.values()))
    manifest["recordCount"] = record_manifest.get("total_records", 0)
    manifest["lastSync"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    manifest["root_folder_id"] = ROOT_FOLDER_ID
    manifest["root_folder_name"] = ROOT_FOLDER_NAME
    manifest["fileCount"] = len(old_files)
    manifest["chunkCount"] = len(all_chunks)
    manifest["recordExtractionVersion"] = record_manifest.get("extraction_version")
    manifest["ingestionVersion"] = INGESTION_VERSION
    manifest["corpusVersion"] = corpus_version(manifest, record_manifest, len(all_chunks))
    source_map = build_source_map(manifest, CHUNKS_PATH, RECORDS_DIR, SOURCE_MAP_PATH)
    chroma_count = 0
    try:
        if coll is not None:
            chroma_count = int(coll.count())
        else:
            previous_status = json.loads(SYNC_STATUS_PATH.read_text()) if SYNC_STATUS_PATH.exists() else {}
            chroma_count = int(previous_status.get("validation", {}).get("chroma_count") or 0)
    except Exception:
        chroma_count = 0
    embedding_health = ollama_embedding_health()
    validation = {
        "ok": bool(old_files) and len(all_chunks) > 0 and manifest.get("recordCount", 0) > 0,
        "file_count": len(old_files),
        "chunk_count": len(all_chunks),
        "record_count": manifest.get("recordCount", 0),
        "chroma_count": chroma_count,
        "vectors_available": chroma_count > 0,
        "embedding": embedding_health,
        "corpus_version": manifest["corpusVersion"],
        "record_manifest_path": str(RECORD_MANIFEST_PATH),
        "source_map_path": str(SOURCE_MAP_PATH),
        "source_map_document_count": source_map.get("document_count", 0),
        "source_map_alias_count": len(source_map.get("alias_index") or []),
        "ingestion_version": INGESTION_VERSION,
        "warnings": [],
        "notices": [],
    }
    if chroma_count <= 0:
        validation["warnings"].append("Chroma vector index is empty; retrieval will use lexical chunks and structured records only.")
    if not embedding_health.get("ok"):
        validation["warnings"].append("Embedding service is unavailable; vector index cannot be refreshed.")
    stale_exports = stale_export_paths(old_files)
    if stale_exports:
        validation["stale_exports"] = stale_exports[:50]
        validation["notices"].append(f"{len(stale_exports)} exported files are not in the active manifest; they may be old sheet/doc versions or removed Drive files.")
    save_manifest(manifest)
    save_json_atomic(SYNC_STATUS_PATH, {
        "last_sync": manifest["lastSync"],
        "changed": changed,
        "skipped": skipped,
        "removed": len(removed_ids),
        "removed_ids": sorted(removed_ids),
        "validation": validation,
    })
    for warning in validation["warnings"]:
        log(f"warning: {warning}")
    log(f"sync complete: changed={changed} skipped={skipped} removed={len(removed_ids)} chunks={len(all_chunks)} records={manifest.get('recordCount', 0)} vectors={chroma_count} corpus={manifest['corpusVersion']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Google Drive lore into a local Chroma index.")
    parser.add_argument("--sync", action="store_true", help="Run the sync job")
    parser.add_argument("--force", action="store_true", help="Force every discovered file to re-export and re-index")
    args = parser.parse_args()
    if not args.sync:
        parser.error("expected --sync")
    if args.force and MANIFEST_PATH.exists():
        MANIFEST_PATH.unlink()
    if args.force and CHUNKS_PATH.exists():
        CHUNKS_PATH.unlink()
    return sync()


if __name__ == "__main__":
    raise SystemExit(main())
