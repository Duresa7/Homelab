# Docker MCP Gateway

**Created:** 2026-08-30  
**Last updated:** 2026-08-31

I run Docker MCP Gateway on `docker-blue` as the container runtime and aggregation point for MCP servers. It currently serves the UniFi Network MCP through a dedicated catalog entry.

## Current State

| Item | Value |
|---|---|
| Version | 0.43.3 |
| OCI image | `docker.io/docker/mcp-gateway:v0.43.3` |
| Pinned manifest digest | `sha256:e3ee13818cb067a506c5e9acdb2bb4fe0e601caef7d116fc329755782f1a3cfa` |
| Host | `docker-blue` (`192.168.40.39`) |
| MCP endpoint | `http://192.168.40.39:8811/mcp` |
| Health endpoint | `http://192.168.40.39:8811/health` |
| Live Compose path | `/opt/docker/mcp-gateway/docker-compose.yml` |
| Live configuration | `/opt/docker/mcp-gateway/config` |
| Gateway secret file | `/opt/docker/mcp-gateway/.env`, root-owned mode `0600` |
| MCP secret file | `/opt/docker/mcp-gateway/mcp-secrets.env`, root-owned mode `0600` |
| Managed server | UniFi Network MCP, tracking `latest` |
| Managed image | `ghcr.io/sirkirby/unifi-network-mcp:latest` |
| UniFi controller | `192.168.1.1:443`, site `default` |
| Catalog | `/opt/docker/mcp-gateway/config/catalogs/unifi-network.yaml` |
| Restart policy | `unless-stopped` |

The MCP endpoint uses Streamable HTTP and requires a bearer token. The token is held in the approved credential store and the live `.env`; it is not in this repository. No DNS record, TLS proxy, or Executor connection is present.

The UniFi server runs through the gateway's headless catalog mode and starts as a managed stdio container when a client calls it. Lazy registration exposes the server through the gateway's discovery and execution tools instead of publishing all 187 UniFi tools at once. The local administrator credentials and Integration API key come from the approved credential store and the root-owned MCP secret file. Create, update, and delete policy switches are disabled. The catalog also limits the managed container's network access to `192.168.1.1:443`.

The official container deployment requires the host Docker socket. This gives the gateway control of Docker Engine on `docker-blue`, which is necessary for starting managed MCP server containers and is the deployment's main trust boundary. The gateway container otherwise has a read-only root filesystem, no Linux capabilities, `no-new-privileges`, a 256 MiB memory limit, a half-CPU limit, a 256-process limit, and bounded JSON logs. Future managed MCP server containers default to one CPU and 512 MiB through the gateway arguments.

## Routine Operations

Run on `docker-blue` with elevation:

```bash
cd /opt/docker/mcp-gateway
docker compose config --quiet
docker compose ps
docker compose logs --tail 100 gateway
docker stats docker-mcp-gateway --no-stream
curl -fsS http://192.168.40.39:8811/health
```

Update the gateway by changing its tag and digest in the versioned Compose reference. Update UniFi MCP manually on `docker-blue` with:

```bash
cd /opt/docker/mcp-gateway
docker pull ghcr.io/sirkirby/unifi-network-mcp:latest
docker compose up -d --force-recreate gateway
```

Verify health, bearer-token enforcement, an authenticated system-information read, and an Integration API read after the recreation.

## Records

- [Compose reference](Configuration/docker-compose.yml)
- [Environment template](Configuration/.env.example)
- [MCP secret template](Configuration/mcp-secrets.env.example)
- [UniFi catalog](Configuration/catalogs/unifi-network.yaml)
- [Initial deployment](Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md)
- [UniFi Network MCP integration](Documentation/Change%20Records/UniFi%20Network%20MCP%20Integration%20-%202026-08-31.md)
- [UniFi Network MCP release tracking](Documentation/Change%20Records/UniFi%20Network%20MCP%20Release%20Tracking%20-%202026-08-31.md)

## Upstream

- [Docker MCP Gateway documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/)
- [Docker MCP Gateway repository](https://github.com/docker/mcp-gateway)
- [Official container package](https://hub.docker.com/r/docker/mcp-gateway)
- [UniFi Network MCP repository](https://github.com/sirkirby/unifi-mcp)
