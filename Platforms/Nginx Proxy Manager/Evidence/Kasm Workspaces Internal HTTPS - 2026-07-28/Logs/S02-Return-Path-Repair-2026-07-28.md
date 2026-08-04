# S02 Return-Path Repair

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Captured:** 2026-07-28 23:44 EDT  
**Target:** UniFi controller and `docker-network`  
**Mechanism:** UniFi Network MCP and SSH Manager MCP

I previewed policy `6a68e0a4052792cd2140c72f` changing only:

```text
connection_state_type: ALL -> CUSTOM
connection_states: [] -> [NEW, INVALID]
```

The confirmed update returned `success: true`. Its readback retained action `BLOCK`, source LAB-MGMT, destination `AlphaSec-Access`, protocol `all`, logging enabled, & index 10000.

Verification from `docker-network`:

```sh
curl -kfsS -o /dev/null -w 'kasm_backend_http=%{http_code}\n' --connect-timeout 8 https://192.168.78.10/
curl -kfsS --connect-timeout 8 https://192.168.78.10/api/__healthcheck
```

The first request returned HTTP `200`; the second returned `{"ok": true}`. Both commands exited `0`.
