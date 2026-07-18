#!/usr/bin/env python3
import json
import os
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, "/home/REDACTED_DEPLOYMENT_USER/lore-rag")

from lore_mcp_server import health_status, lore_agent_answer, lore_answer, lore_search  # noqa: E402


HOST = "127.0.0.1"
PORT = 19731

REQUEST_LOG_PATH = Path(os.environ.get("LORE_REQUEST_LOG", "/home/REDACTED_DEPLOYMENT_USER/lore-rag/logs/agent-requests.log"))


def log_event(payload: dict) -> None:
    try:
        REQUEST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({"ts": datetime.now(timezone.utc).isoformat(), **payload}, ensure_ascii=False)
        with REQUEST_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        # Logging must never break a request.
        pass


def public_body(body):
    if not isinstance(body, dict):
        return body
    public = dict(body)
    public.pop("tool_results", None)
    public.pop("agent_plan", None)
    return public


def _normalize_session_context(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for entry in raw[-12:]:
        if not isinstance(entry, dict):
            continue
        role = str(entry.get("role") or "").strip()[:48] or "User"
        content = str(entry.get("content") or "").strip()
        if not content:
            continue
        ts = entry.get("ts")
        try:
            ts = int(ts) if ts is not None else None
        except (TypeError, ValueError):
            ts = None
        out.append({"role": role, "content": content[:1000], "ts": ts})
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "LoreSearch/1.0"

    def log_message(self, fmt, *args):
        return

    def send_json(self, status, body):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            health = health_status()
            self.send_json(200 if health.get("ok") else 503, health)
            return
        self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path not in {"/search", "/answer", "/agent-answer"}:
            self.send_json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
            query = str(data.get("query", "")).strip()
            limit = int(data.get("limit", 8))
            if not query:
                self.send_json(400, {"error": "query_required"})
                return
            if self.path == "/answer":
                self.send_json(200, lore_answer(query, limit))
            elif self.path == "/agent-answer":
                max_seconds = int(data.get("max_seconds", 18))
                session_context = _normalize_session_context(data.get("session_context"))
                t0 = time.time()
                result = lore_agent_answer(
                    query, limit,
                    max_seconds=max_seconds,
                    session_context=session_context,
                )
                elapsed_ms = int((time.time() - t0) * 1000)
                log_event({
                    "kind": "server_agent_answer",
                    "query": query,
                    "mode": result.get("mode"),
                    "status": result.get("status"),
                    "confidence": result.get("confidence"),
                    "retrieval_mode": result.get("retrieval_mode"),
                    "route": (result.get("evidence") or {}).get("route"),
                    "plan": ((result.get("evidence") or {}).get("plan") or {}).get("reason"),
                    "candidate_count": (result.get("evidence") or {}).get("candidate_count"),
                    "source_titles": [s.get("title") for s in (result.get("sources") or [])][:5],
                    "elapsed_ms": elapsed_ms,
                    "answer_preview": (result.get("answer") or "")[:240],
                    "session_context_messages": len(session_context),
                    "cached": bool(result.get("cached")),
                })
                self.send_json(200, public_body(result))
            else:
                self.send_json(200, lore_search(query, limit))
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
