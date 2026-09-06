#!/usr/bin/env python3
"""Run a credential-safe MCP protocol and local Wazuh data-path smoke test."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ENDPOINT = "http://192.168.72.2:3000/mcp"
ENV_PATH = Path("/opt/docker/wazuh-mcp-server/.env")
WRITE_TOOLS = {
    "wazuh_block_ip",
    "wazuh_isolate_host",
    "wazuh_kill_process",
    "wazuh_disable_user",
    "wazuh_quarantine_file",
    "wazuh_active_response",
    "wazuh_firewall_drop",
    "wazuh_host_deny",
    "wazuh_restart",
    "wazuh_unisolate_host",
    "wazuh_enable_user",
    "wazuh_restore_file",
    "wazuh_firewall_allow",
    "wazuh_host_allow",
}


def api_key() -> str:
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("MCP_API_KEY="):
            value = line.partition("=")[2]
            if value:
                return value
    raise RuntimeError("MCP_API_KEY is missing")


def parse_response(raw: str, content_type: str) -> dict[str, Any]:
    if not raw.strip():
        return {}
    if "text/event-stream" in content_type:
        messages = []
        for line in raw.splitlines():
            if line.startswith("data:"):
                messages.append(json.loads(line.partition(":")[2].strip()))
        if not messages:
            raise RuntimeError("MCP SSE response contained no data event")
        value = messages[-1]
    else:
        value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError("MCP response had an unexpected JSON shape")
    return value


def request_mcp(payload: dict[str, Any], key: str, session_id: str | None = None) -> tuple[dict[str, Any], str | None]:
    headers = {
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = Request(ENDPOINT, data=json.dumps(payload).encode(), method="POST", headers=headers)
    try:
        with urlopen(req, timeout=60) as response:
            parsed = parse_response(response.read().decode(), response.headers.get("Content-Type", ""))
            return parsed, response.headers.get("Mcp-Session-Id") or session_id
    except HTTPError as exc:
        exc.read()
        raise RuntimeError(f"MCP request returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"MCP request failed: {exc.reason}") from exc


def assert_result(response: dict[str, Any], method: str) -> dict[str, Any]:
    if "error" in response:
        error = response["error"]
        code = error.get("code") if isinstance(error, dict) else "unknown"
        raise RuntimeError(f"{method} returned JSON-RPC error {code}")
    result = response.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(f"{method} returned no result object")
    if result.get("isError") is True:
        raise RuntimeError(f"{method} returned isError=true")
    return result


def close_session(key: str, session_id: str) -> None:
    req = Request(
        ENDPOINT,
        method="DELETE",
        headers={"Authorization": f"Bearer {key}", "Mcp-Session-Id": session_id},
    )
    try:
        with urlopen(req, timeout=30) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"MCP session close returned HTTP {response.status}")
    except HTTPError as exc:
        exc.read()
        raise RuntimeError(f"MCP session close returned HTTP {exc.code}") from exc


def main() -> None:
    key = api_key()
    initialized, session_id = request_mcp(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "homelab-verifier", "version": "1"},
            },
        },
        key,
    )
    initialize_result = assert_result(initialized, "initialize")
    if not session_id:
        raise RuntimeError("MCP server did not issue a session ID")
    request_mcp({"jsonrpc": "2.0", "method": "notifications/initialized"}, key, session_id)

    listed, _ = request_mcp({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, key, session_id)
    tools_result = assert_result(listed, "tools/list")
    tools = tools_result.get("tools")
    if not isinstance(tools, list):
        raise RuntimeError("tools/list returned no tool array")
    names = {tool.get("name") for tool in tools if isinstance(tool, dict)}
    exposed_write_tools = sorted(WRITE_TOOLS & names)
    if exposed_write_tools:
        raise RuntimeError(f"Read-only API key exposed {len(exposed_write_tools)} write tools")

    required_calls = (
        ("validate_wazuh_connection", {}),
        ("get_wazuh_agents", {"limit": 1}),
        ("get_wazuh_alert_summary", {"time_range": "24h"}),
        ("get_wazuh_vulnerability_summary", {"time_range": "7d"}),
    )
    missing = [name for name, _ in required_calls if name not in names]
    if missing:
        raise RuntimeError(f"Required read tools missing: {', '.join(missing)}")

    print(
        "protocol={} session=established tools={} write_tools_exposed=0".format(
            initialize_result.get("protocolVersion", "unknown"), len(names)
        )
    )
    for request_id, (name, arguments) in enumerate(required_calls, start=3):
        response, _ = request_mcp(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
            key,
            session_id,
        )
        result = assert_result(response, name)
        content = result.get("content", [])
        if not isinstance(content, list) or not content:
            raise RuntimeError(f"{name} returned no MCP content")
        print(f"tool_call={name} ok content_blocks={len(content)}")
    close_session(key, session_id)
    print("session=closed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
