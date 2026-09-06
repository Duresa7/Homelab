# Executor Runbook

**Created:** 2026-08-30  
**Last updated:** 2026-09-06

## Deployment Layout

| Path | Purpose |
|---|---|
| `/opt/docker/executor/docker-compose.yml` | Live Compose definition on `docker-blue` |
| `/opt/docker/executor/data` | SQLite database and generated authentication/encryption keys |
| `Platforms/Executor/Configuration/docker-compose.yml` | Versioned Compose reference |

The live data directory is owned by root with mode `0700`. Generated key files are mode `0600`. I do not put the data directory, keys, administrator credentials, or tokens in Git.

`EXECUTOR_ALLOW_LOCAL_NETWORK` is enabled because the UniFi and SSH Manager gateways are intentional local integrations at `192.168.40.39:8811` and `192.168.40.39:8812`, and Wazuh MCP is at `192.168.72.2:3000`. Local STDIO MCP servers remain disabled.

## Initial Deployment Process

1. Confirm that the official GitHub container package still publishes `latest` and note the version and manifest it currently resolves to.
2. Keep the versioned Compose reference on `ghcr.io/usefulsoftwareco/executor-selfhost:latest`.
3. Install the same file as `/opt/docker/executor/docker-compose.yml` on `docker-blue` and create `/opt/docker/executor/data`.
4. Validate and start the project:

   ```bash
   cd /opt/docker/executor
   docker compose config --quiet
   docker compose pull
   docker compose up -d
   ```

5. Configure Nginx Proxy Manager for `mcp.alphasecunited.com` with the wildcard certificate, Force SSL, HTTP/2, WebSocket support, Block Common Exploits, and these streaming settings:

   ```nginx
   proxy_buffering off;
   proxy_cache off;
   proxy_read_timeout 3600s;
   proxy_send_timeout 3600s;
   send_timeout 3600s;
   ```

6. Create the internal UniFi A record pointing the name to `192.168.85.2` and the narrow TCP policy from Nginx Proxy Manager to `192.168.40.39:4788`.
7. Verify internal DNS, the HTTP-to-HTTPS redirect, the wildcard certificate, `/api/health`, the unauthenticated `401` response at `/mcp`, and a restart with persistent keys unchanged.
8. Open `https://mcp.alphasecunited.com` and create the first administrator account.

## Routine Checks

Run on `docker-blue`:

```bash
cd /opt/docker/executor
docker compose ps
docker compose logs --tail 100 executor
docker stats executor --no-stream
curl -fsS http://192.168.40.39:4788/api/health
```

Run from an internal client:

```bash
curl -fsS https://mcp.alphasecunited.com/api/health
```

A healthy response is `{"status":"ok"}`. A request to `/mcp` without authentication should return `401`; that is application enforcement, not a proxy failure.

For the Docker MCP Gateway integrations, confirm all of the following in Executor after an upgrade or credential change:

- Integration `unifi-mcp-gateway` points to `http://192.168.40.39:8811/mcp`, and personal connection `unifiMcpGateway` reports healthy.
- A refresh of `unifiMcpGateway` discovers 5 names under `unifi_`.
- Executor can execute `unifi-mcp-gateway.user.unifiMcpGateway.unifi_tool_index`.
- The UniFi connection identity label is `UniFi MCP`, and its description is `Full UniFi Network read, create, update, and delete access.`
- Executor has no tool policy targeting the UniFi connection. A no-confirm mutation probe reaches the handler without returning `requires_confirmation`.
- Integration `ssh-manager-mcp-gateway` points to `http://192.168.40.39:8812/mcp`, and personal connection `sshManagerMcpGateway` reports healthy.
- A refresh of `sshManagerMcpGateway` discovers 37 names under `ssh_` while SSH Manager remains at 3.8.5.
- `docker ps -a --filter label=docker-mcp-name=ssh-manager` on `docker-blue` returns nothing, and the `mcp-ssh-manager` service is healthy. Since 2026-09-03 the SSH Manager server is a persistent service rather than a container the gateway starts per session, so any managed container here is a sign the old catalog entry came back.
- Executor can execute `ssh-manager-mcp-gateway.user.sshManagerMcpGateway.ssh_list_servers`.
- The SSH Manager connection identity label is `SSH Manager MCP`, and its description is `SSH Manager access.`
- `ssh_list_servers` returns all 18 catalog entries. A privilege sweep proves the five Proxmox nodes and `docker_main` return UID `0` through root login and the other twelve return UID `0` through `ssh_execute_sudo`.
- Both integrations have empty static request-header maps. Each bearer token belongs in its connection's encrypted credential.
- The retired `docker-mcp-gateway` integration and `dockerMcpGateway` connection remain absent.

For Wazuh MCP, confirm all of the following:

- Integration `wazuh-mcp-server` points to `http://192.168.72.2:3000/mcp`, and user connection `localWazuh` reports healthy.
- A refresh discovers 41 tools for Wazuh MCP Server 4.3.0 and none of the 14 `wazuh:write` tools.
- Executor can execute `wazuh-mcp-server.user.localWazuh.validate_wazuh_connection`.
- `get_wazuh_agents`, `get_wazuh_alert_summary`, and `get_wazuh_vulnerability_summary` each return an MCP success result.
- The connection identity label is `Local Wazuh`, and its bearer credential is in Executor's encrypted provider rather than the integration's static header map.
- On `security-01`, `/ready` reports `wazuh_manager`, `wazuh_indexer`, and `mcp` healthy.

Tool counts change when a managed server changes its surface. Record each new count rather than treating 5, 37, and 41 as permanent release invariants.

## Updating

1. Check the official GitHub container package for the current `latest` manifest and note the running version before the update.
2. Confirm the repository Compose reference still uses `ghcr.io/usefulsoftwareco/executor-selfhost:latest`.
3. Install the same Compose file on `docker-blue`.
4. Apply and verify:

   ```bash
   cd /opt/docker/executor
   docker compose config --quiet
   docker compose pull
   docker compose up -d
   docker compose ps
   curl -fsS http://192.168.40.39:4788/api/health
   ```

5. Recheck the HTTPS health endpoint and authenticated MCP connection before removing any older image. Then run one live call through each integration, since a recreate drops every client session. The [1.6.8 update](Change%20Records/Update%20to%201.6.8%20-%202026-09-06.md) is the worked example.

## Restarting and Stopping

```bash
cd /opt/docker/executor
docker compose restart executor
docker compose stop
docker compose up -d
```

Stopping or recreating the container does not remove `/opt/docker/executor/data`.

## Recovery

Executor's durable state is the complete `/opt/docker/executor/data` directory. A usable backup must preserve `data.db`, its SQLite companion files when present, both generated key files, ownership, and modes. Restore the directory while the container is stopped, then start the project and verify both the direct and HTTPS health endpoints.

No separate backup was created during the initial deployment.
