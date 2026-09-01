# Executor Runbook

**Created:** 2026-08-30  
**Last updated:** 2026-08-31

## Deployment Layout

| Path | Purpose |
|---|---|
| `/opt/docker/executor/docker-compose.yml` | Live Compose definition on `docker-blue` |
| `/opt/docker/executor/data` | SQLite database and generated authentication/encryption keys |
| `Platforms/Executor/Configuration/docker-compose.yml` | Versioned Compose reference |

The live data directory is owned by root with mode `0700`. Generated key files are mode `0600`. I do not put the data directory, keys, administrator credentials, or tokens in Git.

`EXECUTOR_ALLOW_LOCAL_NETWORK` is enabled because the UniFi and SSH Manager gateways are intentional local integrations at `192.168.40.39:8811` and `192.168.40.39:8812`. Local STDIO MCP servers remain disabled.

## Initial Deployment Process

1. Confirm the newest stable version and multi-architecture image digest in the official GitHub container package.
2. Update the versioned Compose reference so both the release tag and digest are pinned.
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
- Integration `ssh-manager-mcp-gateway` points to `http://192.168.40.39:8812/mcp`, and personal connection `sshManagerMcpGateway` reports healthy.
- A refresh of `sshManagerMcpGateway` discovers 37 names under `ssh_` while SSH Manager remains at 3.8.5.
- Executor can execute `ssh-manager-mcp-gateway.user.sshManagerMcpGateway.ssh_list_servers`.
- `ssh_list_servers` returns all 18 catalog entries. A privilege sweep proves the five Proxmox nodes and `docker_main` return UID `0` through root login and the other twelve return UID `0` through `ssh_execute_sudo`.
- Both integrations have empty static request-header maps. Each bearer token belongs in its connection's encrypted credential.
- The retired `docker-mcp-gateway` integration and `dockerMcpGateway` connection remain absent.

Tool counts change when either managed server changes its surface. Record each new count rather than treating 5 and 37 as permanent release invariants.

## Updating

1. Check the official GitHub container package for the newest stable tag and current multi-architecture digest.
2. Change both values in the repository Compose reference.
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

5. Recheck the HTTPS health endpoint and authenticated MCP connection before removing any older image.

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
