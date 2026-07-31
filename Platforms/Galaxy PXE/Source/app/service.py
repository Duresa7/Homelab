import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from registry import ATTEMPT_PHASES, MachineRegistry
from rendering import (
    find_mac_address,
    normalize_mac,
    read_public_keys,
    render_answer,
    render_boot_script,
    render_first_boot,
    summarize_installer_result,
)


def stream_file_response(handler, path, content_type, chunk_size=1024 * 1024):
    file_size = path.stat().st_size
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(file_size))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    if handler.command == "HEAD":
        return
    with path.open("rb") as source:
        while chunk := source.read(chunk_size):
            handler.wfile.write(chunk)


def validate_runtime_inputs(root_hash_path, root_ssh_keys_path, join_key_path):
    for label, path in (
        ("root password hash", Path(root_hash_path)),
        ("root SSH keys", Path(root_ssh_keys_path)),
        ("cluster join key", Path(join_key_path)),
    ):
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"{label} file is missing or empty")
    read_public_keys(root_ssh_keys_path)


class ProvisioningHandler(BaseHTTPRequestHandler):
    server_version = "GalaxyPXE/2.0"

    def _send(self, status, body=b"", content_type="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _query_value(self, name):
        query = parse_qs(urlparse(self.path).query)
        values = query.get(name, [])
        if len(values) != 1:
            raise ValueError(f"one {name} parameter is required")
        return unquote(values[0])

    def _request_mac(self):
        return normalize_mac(self._query_value("mac"))

    def _request_attempt(self):
        return self._query_value("attempt")

    def _json_body(self, maximum=1024 * 1024, *, required=True):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0 and not required:
            return {}
        if content_length < 1 or content_length > maximum:
            raise ValueError("invalid content length")
        value = json.loads(self.rfile.read(content_length))
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def _serve_asset(self, request_path):
        relative = request_path.removeprefix("/assets/")
        candidate = (self.server.asset_dir / relative).resolve()
        asset_root = self.server.asset_dir.resolve()
        if asset_root not in candidate.parents or not candidate.is_file():
            self._send(HTTPStatus.NOT_FOUND)
            return
        content_type = "application/octet-stream"
        if candidate.suffix in {".ipxe", ".txt"}:
            content_type = "text/plain; charset=utf-8"
        stream_file_response(self, candidate, content_type)

    def _require_attempt(self, mac, attempt_id, allowed_phases=None):
        record = self.server.registry.record(mac)
        if record.get("attempt_id") != attempt_id:
            raise ValueError("attempt identifier does not match")
        if allowed_phases and record["phase"] not in allowed_phases:
            raise ValueError("attempt is not in an allowed phase")
        return record

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/health":
                self._send(HTTPStatus.OK, "ok\n")
            elif parsed.path == "/v1/boot":
                mac = self._request_mac()
                attempt = self.server.registry.claim_install(mac)
                self._send(
                    HTTPStatus.OK,
                    render_boot_script(self.server.base_url, bool(attempt)),
                    "text/plain; charset=utf-8",
                )
            elif parsed.path == "/v1/status":
                record = self.server.registry.record(self._request_mac())
                self._send(
                    HTTPStatus.OK,
                    json.dumps(record, indent=2, sort_keys=True) + "\n",
                    "application/json",
                )
            elif parsed.path == "/v1/bootstrap":
                mac = self._request_mac()
                attempt_id = self._request_attempt()
                record = self._require_attempt(
                    mac,
                    attempt_id,
                    {
                        "answer_served",
                        "bootstrap_fetched",
                        "installer_succeeded",
                        "first_boot_started",
                    },
                )
                if record["phase"] == "answer_served":
                    self.server.registry.transition(
                        mac, attempt_id, "bootstrap_fetched"
                    )
                machine = self.server.registry.machine(mac)
                self._send(
                    HTTPStatus.OK,
                    render_first_boot(
                        mac, machine, self.server.base_url, attempt_id
                    ),
                    "text/x-shellscript; charset=utf-8",
                )
            elif parsed.path == "/v1/join-key":
                mac = self._request_mac()
                attempt_id = self._request_attempt()
                self._require_attempt(mac, attempt_id, ATTEMPT_PHASES)
                self._send(
                    HTTPStatus.OK,
                    self.server.join_key_path.read_bytes(),
                    "application/octet-stream",
                )
            elif parsed.path.startswith("/assets/"):
                self._serve_asset(parsed.path)
            else:
                self._send(HTTPStatus.NOT_FOUND)
        except (KeyError, ValueError):
            self._send(HTTPStatus.CONFLICT)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/v1/answer":
                payload = self._json_body()
                mac = find_mac_address(payload, self.server.registry.machines)
                if not mac:
                    self._send(HTTPStatus.NOT_FOUND)
                    return
                record = self.server.registry.record(mac)
                if record["phase"] == "installer_claimed":
                    detail = {
                        "fetch_schema": (
                            payload.get("$schema") or payload.get("schema") or {}
                        ).get("version"),
                        "dmi": payload.get("sysinfo", {}).get("dmi"),
                    }
                    record = self.server.registry.transition(
                        mac,
                        record["attempt_id"],
                        "answer_served",
                        detail,
                    )
                elif record["phase"] != "answer_served":
                    self._send(HTTPStatus.CONFLICT)
                    return
                password_hash = self.server.root_hash_path.read_text(
                    encoding="utf-8"
                ).strip()
                answer = render_answer(
                    mac,
                    self.server.registry.machine(mac),
                    password_hash,
                    self.server.base_url,
                    record["attempt_id"],
                    read_public_keys(self.server.root_ssh_keys_path),
                )
                self._send(
                    HTTPStatus.OK, answer, "application/toml; charset=utf-8"
                )
            elif parsed.path == "/v1/installer-complete":
                mac = self._request_mac()
                attempt_id = self._request_attempt()
                self._require_attempt(
                    mac,
                    attempt_id,
                    {"answer_served", "bootstrap_fetched"},
                )
                summary = summarize_installer_result(self._json_body())
                machine = self.server.registry.machine(mac)
                expected_disk = f"/dev/{machine['install_disk']}"
                if summary["boot_disks"] != [expected_disk]:
                    self.server.registry.transition(
                        mac,
                        attempt_id,
                        "failed",
                        {
                            "reason": "unexpected boot disk in installer result",
                            "installer_result": summary,
                        },
                    )
                    self._send(HTTPStatus.CONFLICT)
                    return
                self.server.registry.transition(
                    mac,
                    attempt_id,
                    "installer_succeeded",
                    {"installer_result": summary},
                )
                self._send(HTTPStatus.NO_CONTENT)
            elif parsed.path.startswith("/v1/state/"):
                phase = parsed.path.removeprefix("/v1/state/")
                mac = self._request_mac()
                attempt_id = self._request_attempt()
                detail = self._json_body(required=False)
                self.server.registry.transition(
                    mac, attempt_id, phase, detail or None
                )
                self._send(HTTPStatus.NO_CONTENT)
            else:
                self._send(HTTPStatus.NOT_FOUND)
        except (json.JSONDecodeError, KeyError, ValueError):
            self._send(HTTPStatus.CONFLICT)

    def log_message(self, format_string, *args):
        path = urlparse(self.path).path
        print(f"{self.address_string()} {self.command} {path}", flush=True)


def build_server(args):
    validate_runtime_inputs(
        args.root_hash, args.root_ssh_keys, args.join_key
    )
    server = ThreadingHTTPServer((args.listen, args.port), ProvisioningHandler)
    server.registry = MachineRegistry(args.machines, args.state)
    server.base_url = args.base_url.rstrip("/")
    server.asset_dir = Path(args.assets)
    server.root_hash_path = Path(args.root_hash)
    server.root_ssh_keys_path = Path(args.root_ssh_keys)
    server.join_key_path = Path(args.join_key)
    return server
