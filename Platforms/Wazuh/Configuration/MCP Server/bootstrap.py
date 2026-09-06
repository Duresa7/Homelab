#!/usr/bin/env python3
"""Provision least-privilege Wazuh MCP identities and deploy the container.

Run this script as root on the Wazuh host after staging docker-compose.yml,
wazuh-ca-bundle.pem, and a mode-0600 .env in STAGING_DIR.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml


STAGING_DIR = Path("/home/dkadi/wazuh-mcp-bootstrap")
LIVE_DIR = Path("/opt/docker/wazuh-mcp-server")
ENV_PATH = STAGING_DIR / ".env"
MANAGER_API = "https://localhost:55000"
INDEXER_API = "https://127.0.0.1:9200"
MANAGER_CA = "/var/ossec/api/configuration/ssl/server.crt"
INDEXER_CA = "/etc/wazuh-indexer/certs/root-ca.pem"
INDEXER_ADMIN_CERT = "/etc/wazuh-indexer/certs/admin.pem"
INDEXER_ADMIN_KEY = "/etc/wazuh-indexer/certs/admin-key.pem"
DASHBOARD_WAZUH_CONFIG = Path("/usr/share/wazuh-dashboard/data/wazuh/config/wazuh.yml")


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not key:
            fail(f"Invalid environment entry for {key or '<empty key>'}")
        values[key] = value

    required = {
        "WAZUH_USER",
        "WAZUH_PASS",
        "WAZUH_INDEXER_USER",
        "WAZUH_INDEXER_PASS",
        "MCP_API_KEY",
        "AUTH_SECRET_KEY",
    }
    missing = sorted(required - values.keys())
    if missing:
        fail(f"Missing required environment keys: {', '.join(missing)}")
    if values["WAZUH_USER"] != "wazuh-mcp-api":
        fail("Unexpected Wazuh Manager API username")
    if values["WAZUH_INDEXER_USER"] != "wazuh-mcp-indexer":
        fail("Unexpected Wazuh Indexer username")
    if not values["MCP_API_KEY"].startswith("wazuh_") or len(values["MCP_API_KEY"]) != 49:
        fail("MCP_API_KEY does not match the upstream wazuh_<43-character-token> format")
    if len(values["AUTH_SECRET_KEY"]) < 32:
        fail("AUTH_SECRET_KEY must be at least 32 characters")
    return values


def basic_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def request(
    url: str,
    *,
    context: ssl.SSLContext,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> tuple[int, str]:
    request_headers = {"Accept": "application/json", **(headers or {})}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        request_headers["Content-Type"] = "application/json"
    req = Request(url, data=data, method=method, headers=request_headers)
    try:
        with urlopen(req, context=context, timeout=30) as response:
            return response.status, response.read().decode()
    except HTTPError as exc:
        exc.read()
        fail(f"{method} {url} returned HTTP {exc.code}")
    except URLError as exc:
        fail(f"{method} {url} failed: {exc.reason}")


def request_json(*args: Any, **kwargs: Any) -> dict[str, Any]:
    status, raw = request(*args, **kwargs)
    if status < 200 or status >= 300:
        fail(f"Request returned unexpected HTTP {status}")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        fail("Endpoint returned invalid JSON")
    if not isinstance(parsed, dict):
        fail("Endpoint returned an unexpected JSON shape")
    return parsed


def dashboard_api_credentials() -> tuple[str, str]:
    config = yaml.safe_load(DASHBOARD_WAZUH_CONFIG.read_text(encoding="utf-8"))
    hosts = config.get("hosts", []) if isinstance(config, dict) else []
    candidates: list[dict[str, Any]] = []
    if isinstance(hosts, list):
        for entry in hosts:
            if isinstance(entry, dict):
                candidates.extend(value for value in entry.values() if isinstance(value, dict))
    elif isinstance(hosts, dict):
        candidates.extend(value for value in hosts.values() if isinstance(value, dict))
    for candidate in candidates:
        username = candidate.get("username")
        password = candidate.get("password")
        if isinstance(username, str) and isinstance(password, str) and username and password:
            return username, password
    fail("Could not locate Wazuh dashboard API bootstrap credentials")


def manager_token(username: str, password: str, context: ssl.SSLContext) -> str:
    _, raw = request(
        f"{MANAGER_API}/security/user/authenticate?raw=true",
        context=context,
        method="POST",
        headers={"Authorization": basic_header(username, password)},
    )
    token = raw.strip().strip('"')
    if not token or token.startswith("{"):
        fail("Wazuh Manager API did not return a raw authentication token")
    return token


def affected_items(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("data", {})
    items = data.get("affected_items", []) if isinstance(data, dict) else []
    return [item for item in items if isinstance(item, dict)]


def provision_manager_user(env: dict[str, str]) -> None:
    context = ssl.create_default_context(cafile=MANAGER_CA)
    bootstrap_user, bootstrap_password = dashboard_api_credentials()
    token = manager_token(bootstrap_user, bootstrap_password, context)
    auth = {"Authorization": f"Bearer {token}"}

    users_response = request_json(
        f"{MANAGER_API}/security/users?limit=500",
        context=context,
        headers=auth,
    )
    users = affected_items(users_response)
    matches = [item for item in users if item.get("username") == env["WAZUH_USER"]]
    if len(matches) > 1:
        fail("Multiple Wazuh Manager API users have the target username")
    if matches:
        user_id = matches[0].get("id")
    else:
        created = request_json(
            f"{MANAGER_API}/security/users",
            context=context,
            method="POST",
            headers=auth,
            body={"username": env["WAZUH_USER"], "password": env["WAZUH_PASS"]},
        )
        created_items = affected_items(created)
        if len(created_items) != 1:
            fail("Wazuh Manager API user creation returned an unexpected result")
        user_id = created_items[0].get("id")
    if not isinstance(user_id, int):
        fail("Wazuh Manager API user has no numeric ID")

    roles_response = request_json(
        f"{MANAGER_API}/security/roles?limit=500",
        context=context,
        headers=auth,
    )
    readonly_roles = [item for item in affected_items(roles_response) if item.get("name") == "readonly"]
    if len(readonly_roles) != 1 or not isinstance(readonly_roles[0].get("id"), int):
        fail("Built-in Wazuh Manager API readonly role was not found uniquely")
    role_id = readonly_roles[0]["id"]

    request_json(
        f"{MANAGER_API}/security/users/{user_id}/roles?{urlencode({'role_ids': role_id})}",
        context=context,
        method="POST",
        headers=auth,
    )

    readonly_token = manager_token(env["WAZUH_USER"], env["WAZUH_PASS"], context)
    verification = request_json(
        f"{MANAGER_API}/agents?limit=1",
        context=context,
        headers={"Authorization": f"Bearer {readonly_token}"},
    )
    if verification.get("error") != 0:
        fail("Wazuh Manager API read-only verification failed")
    print("manager_api_user=ok role=readonly tls=verified")


def provision_indexer_user(env: dict[str, str]) -> None:
    admin_context = ssl.create_default_context(cafile=INDEXER_CA)
    admin_context.load_cert_chain(certfile=INDEXER_ADMIN_CERT, keyfile=INDEXER_ADMIN_KEY)
    user = env["WAZUH_INDEXER_USER"]
    role = "wazuh_mcp_readonly"
    request_json(
        f"{INDEXER_API}/_plugins/_security/api/internalusers/{user}",
        context=admin_context,
        method="PUT",
        body={"password": env["WAZUH_INDEXER_PASS"], "backend_roles": [], "attributes": {}},
    )
    request_json(
        f"{INDEXER_API}/_plugins/_security/api/roles/{role}",
        context=admin_context,
        method="PUT",
        body={
            "cluster_permissions": ["cluster_composite_ops_ro", "cluster:monitor/health"],
            "index_permissions": [
                {
                    "index_patterns": ["wazuh-alerts-*", "wazuh-states-vulnerabilities-*"],
                    "allowed_actions": ["read"],
                }
            ],
            "tenant_permissions": [],
        },
    )
    request_json(
        f"{INDEXER_API}/_plugins/_security/api/rolesmapping/{role}",
        context=admin_context,
        method="PUT",
        body={"backend_roles": [], "hosts": [], "users": [user]},
    )

    readonly_context = ssl.create_default_context(cafile=INDEXER_CA)
    auth = {"Authorization": basic_header(user, env["WAZUH_INDEXER_PASS"])}
    health = request_json(f"{INDEXER_API}/_cluster/health", context=readonly_context, headers=auth)
    if health.get("status") not in {"green", "yellow"}:
        fail("Wazuh Indexer cluster health verification failed")
    for pattern in ("wazuh-alerts-*", "wazuh-states-vulnerabilities-*"):
        result = request_json(
            f"{INDEXER_API}/{pattern}/_search",
            context=readonly_context,
            method="POST",
            headers=auth,
            body={"size": 0, "track_total_hits": False},
        )
        if "hits" not in result:
            fail(f"Wazuh Indexer read verification failed for {pattern}")
    print("indexer_user=ok role=wazuh_mcp_readonly tls=verified patterns=2")


def install_files() -> None:
    if ENV_PATH.stat().st_mode & 0o077:
        fail("Staged .env permissions are broader than 0600")
    LIVE_DIR.mkdir(parents=True, exist_ok=True, mode=0o750)
    os.chmod(LIVE_DIR, 0o750)
    for source_name, destination_name, mode in (
        (".env", ".env", 0o600),
        ("Dockerfile", "Dockerfile", 0o644),
        ("docker-compose.yml", "docker-compose.yml", 0o644),
        ("static-bearer-api-key.patch", "static-bearer-api-key.patch", 0o644),
        ("verify_mcp.py", "verify_mcp.py", 0o750),
        ("wazuh-ca-bundle.pem", "wazuh-ca-bundle.pem", 0o644),
        ("wazuh-indexer-x509-compat.patch", "wazuh-indexer-x509-compat.patch", 0o644),
    ):
        source = STAGING_DIR / source_name
        if not source.is_file():
            fail(f"Missing staged file: {source_name}")
        destination = LIVE_DIR / destination_name
        temporary = LIVE_DIR / f".{destination_name}.new"
        shutil.copyfile(source, temporary)
        os.chown(temporary, 0, 0)
        os.chmod(temporary, mode)
        os.replace(temporary, destination)
    print("deployment_files=installed env_mode=600")


def run_compose() -> None:
    commands = (
        ["docker", "compose", "config", "--quiet"],
        ["docker", "compose", "build", "--pull"],
        ["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "180"],
    )
    for command in commands:
        result = subprocess.run(command, cwd=LIVE_DIR, text=True, capture_output=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()[-1500:]
            fail(f"{' '.join(command)} failed: {detail}")
    print("compose=ok container=started")


def main() -> None:
    if os.geteuid() != 0:
        fail("This bootstrap must run as root")
    env = load_env(ENV_PATH)
    provision_manager_user(env)
    provision_indexer_user(env)
    install_files()
    run_compose()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
