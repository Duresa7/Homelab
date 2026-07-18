#!/usr/bin/env python3
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, "/home/REDACTED_DEPLOYMENT_USER/lore-rag")

from lore_mcp_server import health_status, lore_answer, lore_search  # noqa: E402


HOST = "127.0.0.1"
PORT = 19731


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
        if self.path not in {"/search", "/answer"}:
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
            else:
                self.send_json(200, lore_search(query, limit))
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
