# Docker MCP Gateway

**Created:** 2026-08-30  
**Last updated:** 2026-08-30

I run Docker MCP Gateway on `docker-blue` as the container runtime and aggregation point for future MCP servers. The gateway is deployed, authenticated, and healthy, but no MCP server or catalog is configured yet.

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
| Live secret file | `/opt/docker/mcp-gateway/.env`, root-owned mode `0600` |
| Restart policy | `unless-stopped` |

The MCP endpoint uses Streamable HTTP and requires a bearer token. The token is held in the approved credential store and the live `.env`; it is not in this repository. No DNS record, TLS proxy, Executor connection, or UniFi policy was added in this deployment.

The gateway has an empty default profile. It exposes its built-in MCP management tools but has not started a managed MCP server container. Its configuration directory is persistent across container recreation.

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

Update by changing the tag and digest in the versioned Compose reference, installing the same file on `docker-blue`, and running `docker compose pull && docker compose up -d`. Verify the health endpoint, bearer-token enforcement, and an authenticated MCP initialization after recreation.

## Records

- [Compose reference](Configuration/docker-compose.yml)
- [Environment template](Configuration/.env.example)
- [Initial deployment](Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md)

## Upstream

- [Docker MCP Gateway documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/)
- [Docker MCP Gateway repository](https://github.com/docker/mcp-gateway)
- [Official container package](https://hub.docker.com/r/docker/mcp-gateway)
