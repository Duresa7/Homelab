# Docker MCP Gateway

**Created:** 2026-08-30  
**Last updated:** 2026-10-31

I run a Docker MCP Gateway endpoint on `docker-blue` in front of UniFi Network MCP. Until 2026-10-31 a second endpoint served SSH Manager MCP; [ssh-mcp](../SSH%20MCP/README.md) replaced it and I removed SSH Manager and its gateway: [SSH Manager Retirement](Documentation/Change%20Records/SSH%20Manager%20Retirement%20-%202026-10-31.md).

## Current State

| Item | Value |
|---|---|
| Gateway version | 0.43.3, pinned by digest; one instance since 2026-10-31 |
| OCI image | `docker.io/docker/mcp-gateway:v0.43.3` |
| Pinned manifest digest | `sha256:e3ee13818cb067a506c5e9acdb2bb4fe0e601caef7d116fc329755782f1a3cfa` |
| Host | `docker-blue` (CT 108, `192.168.40.39`) |
| UniFi endpoint | `http://192.168.40.39:8811/mcp` (container `docker-mcp-gateway`), 5 gateway tools; health at `/health` |
| UniFi server | `mcp-unifi-network`, UniFi Network MCP 0.29.3 with a full-access overlay, image `forgejo.alphasecunited.com/homelab-images/unifi-network-mcp:stable`, private `http://unifi-network:8080/mcp` |
| UniFi controller | `192.168.1.1:443`, site `default` |
| Live Compose path | `/opt/docker/mcp-gateway/docker-compose.yml`; Dockhand's imported copy at `/opt/docker/dockhand/stacks/imported/docker_blue/docker-mcp-gateway/compose.yaml` on `docker-main` |
| Secret files | `/opt/docker/mcp-gateway/.env` (the bearer token) and `unifi-network.env`, both root-owned mode `0600` |
| Restart policy | `unless-stopped` |

The endpoint uses Streamable HTTP and requires a bearer token, held in my credential store and the live `.env`. Executor 2's `unifi` app reaches it directly with that token as an app account. No DNS record or TLS proxy fronts it.

## How It Works

UniFi runs as one persistent Compose service behind [mcp-proxy](https://github.com/sparfenyuk/mcp-proxy) 0.12.0, which spawns the stdio server once and serves it over HTTP on the project network. Every caller shares that one process. The gateway catalog points at the private `remote` URL, and the gateway sets `DOCKER_MCP_ALLOW_INSECURE_REMOTE_URLS=1` because it rejects a plain-HTTP remote by default. UniFi moved to this layout on 2026-09-07, following SSH Manager on 2026-09-03.

UniFi create, update, and delete stay enabled. The full-access overlay makes bypass authoritative even when FastMCP supplies `confirm=false`, so a mutation runs without a confirmation step. UniFi credentials come from `unifi-network.env`, read in Compose's raw env-file format so literal values survive.

SSH Manager's Dockerfile, homelab patch, catalog, nightly restart timer and cutover script moved to [the archive](../../Archive/Platforms/Docker%20MCP%20Gateway/) on 2026-10-31. The change records below keep its history.

## Trust Boundary

The gateway container needs the host Docker socket, which gives it control of Docker Engine on `docker-blue`. That socket is the main trust boundary. Otherwise the gateway runs with a read-only root filesystem, no Linux capabilities, `no-new-privileges`, 256 MiB, half a CPU, a 256-process limit and bounded JSON logs. The UniFi server service is limited to one CPU and 512 MiB.

Routine checks and image updates are in the [Runbook](Documentation/Runbook.md).

## Records

- [Access Paths](../../Architecture/Access-Paths.md): agent access alongside the other paths into the lab

- [Runbook](Documentation/Runbook.md)
- [Compose reference](Configuration/docker-compose.yml)
- [Environment template](Configuration/.env.example)
- [UniFi service secret template](Configuration/unifi-network.env.example)
- [UniFi catalog](Configuration/catalogs/unifi-network.yaml)
- [UniFi full-access Dockerfile](Configuration/Dockerfile.unifi-network)
- [UniFi full-access build patch](Configuration/patches/unifi-network-mcp-0.29.3-full-access.py)
- [Initial deployment](Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md)
- [UniFi Network MCP integration](Documentation/Change%20Records/UniFi%20Network%20MCP%20Integration%20-%202026-08-31.md)
- [UniFi Network MCP release tracking](Documentation/Change%20Records/UniFi%20Network%20MCP%20Release%20Tracking%20-%202026-08-31.md)
- [UniFi full agent access](Documentation/Change%20Records/UniFi%20Full%20Agent%20Access%20-%202026-09-01.md)
- [SSH Manager MCP integration](Documentation/Change%20Records/SSH%20Manager%20MCP%20Integration%20-%202026-08-31.md)
- [SSH Manager fleet reach completion](Documentation/Change%20Records/SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md)
- [SSH Manager gateway process exhaustion](Documentation/Change%20Records/SSH%20Manager%20Gateway%20Process%20Exhaustion%20-%202026-09-02.md)
- [Docker MCP Gateway v2 compatibility rollback](Documentation/Change%20Records/v2%20Compatibility%20Rollback%20-%202026-09-03.md)
- [SSH Manager shared server cutover](Documentation/Change%20Records/SSH%20Manager%20Shared%20Server%20Cutover%20-%202026-09-03.md)
- [UniFi shared server cutover](Documentation/Change%20Records/UniFi%20Shared%20Server%20Cutover%20-%202026-09-07.md)
- [Andor-ParrotOS-PC SSH Manager enrollment](Documentation/Change%20Records/Andor-ParrotOS-PC%20SSH%20Manager%20Enrollment%20-%202026-10-11.md)
- [SSH Manager retirement](Documentation/Change%20Records/SSH%20Manager%20Retirement%20-%202026-10-31.md)
- [Archived SSH Manager configuration](../../Archive/Platforms/Docker%20MCP%20Gateway/)
- [Dockhand registry and agent cutover](../Dockhand/Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md), which moved both server images to Forgejo
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Executor integration](../Executor/Documentation/Change%20Records/Docker%20MCP%20Gateway%20Integration%20-%202026-08-31.md), and since 2026-10-31 the [Executor 2 `unifi` app](../Executor/Documentation/Change%20Records/Executor%202%20Migration%20-%202026-10-31.md)
- [Executor integration separation](../Executor/Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md)

## Upstream

- [Docker MCP Gateway documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/)
- [Docker MCP Gateway repository](https://github.com/docker/mcp-gateway)
- [Official container package](https://hub.docker.com/r/docker/mcp-gateway)
- [UniFi Network MCP repository](https://github.com/sirkirby/unifi-mcp)
