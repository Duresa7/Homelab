# Docker MCP Gateway

**Created:** 2026-08-30  
**Last updated:** 2026-09-25

I run two isolated Docker MCP Gateway endpoints on `docker-blue`. One serves UniFi Network MCP and the other serves SSH Manager MCP. Keeping them on separate endpoints lets clients such as Executor present them as separate integrations instead of one combined tool catalog.

## Current State

| Item | Value |
|---|---|
| Gateway version | 0.43.3, pinned by digest; two instances running on 2026-09-24 |
| OCI image | `docker.io/docker/mcp-gateway:v0.43.3` |
| Pinned manifest digest | `sha256:e3ee13818cb067a506c5e9acdb2bb4fe0e601caef7d116fc329755782f1a3cfa` |
| Host | `docker-blue` (CT 108, `192.168.40.39`) |
| UniFi endpoint | `http://192.168.40.39:8811/mcp` (container `docker-mcp-gateway`), 5 gateway tools; health at `/health` |
| UniFi server | `mcp-unifi-network`, UniFi Network MCP 0.29.3 with a full-access overlay, image `forgejo.alphasecunited.com/homelab-images/unifi-network-mcp:stable`, private `http://unifi-network:8080/mcp` |
| UniFi controller | `192.168.1.1:443`, site `default` |
| SSH Manager endpoint | `http://192.168.40.39:8812/mcp` (container `ssh-manager-mcp-gateway`), 37 tools; health at `/health` |
| SSH Manager server | `mcp-ssh-manager`, SSH Manager MCP 3.8.5 with my homelab patch, image `forgejo.alphasecunited.com/homelab-images/mcp-ssh-manager:stable`, private `http://ssh-manager:8080/mcp` |
| SSH Manager servers | 24, read with `ssh_list_servers` on 2026-09-24 |
| Live Compose path | `/opt/docker/mcp-gateway/docker-compose.yml`; Dockhand's imported copy at `/opt/docker/dockhand/stacks/imported/docker_blue/docker-mcp-gateway/compose.yaml` on `docker-main` |
| Secret files | `/opt/docker/mcp-gateway/.env` (two bearer tokens), `unifi-network.env`, `ssh-manager.env`, all root-owned mode `0600` |
| Restart policy | `unless-stopped`; SSH Manager also restarts nightly at 4 AM Eastern |

Both endpoints use Streamable HTTP and require different bearer tokens, held in my credential store and the live `.env`. Executor reaches each endpoint directly through its own connection, `unifiMcpGateway` and `sshManagerMcpGateway`. No DNS record or TLS proxy fronts either one.

## How It Works

UniFi and SSH Manager each run as one persistent Compose service behind [mcp-proxy](https://github.com/sparfenyuk/mcp-proxy) 0.12.0, which spawns the stdio server once and serves it over HTTP on the project network. Every caller shares that one process. The gateway catalogs point at the private `remote` URLs, and each gateway sets `DOCKER_MCP_ALLOW_INSECURE_REMOTE_URLS=1` because the gateway rejects a plain-HTTP remote by default. SSH Manager moved to this layout on 2026-09-03 and UniFi on 2026-09-07.

UniFi create, update, and delete stay enabled. The full-access overlay makes bypass authoritative even when FastMCP supplies `confirm=false`, so a mutation runs without a confirmation step. UniFi credentials come from `unifi-network.env`, read in Compose's raw env-file format so literal values survive.

SSH Manager has no upstream image. I build it from the tracked [Dockerfile](Configuration/Dockerfile.ssh-manager) with a 3.8.5-specific [patch](Configuration/patches/mcp-ssh-manager-3.8.5-homelab.patch) for bounded inline transfers and real SSH2 host-key comparison. Its private key is written to a `/keys` tmpfs at mode `0600` at start and is never in an image layer.

The live SSH Manager service reads its server definitions from resolved environment settings in the root-owned live Compose file, which I verified while adding `win11_dev` on 2026-09-21. The tracked [Compose reference](Configuration/docker-compose.yml) still lists `ssh-manager-servers.env` and `ssh-manager.env` under `env_file`; those files stay on the host as references and the resolved definition does not load them.

## Trust Boundary

SSH Manager reaches root on the 17 Linux nodes and guests: direct root login on the five Proxmox nodes and `docker-main`, passwordless sudo on `ansible-01` and `ubuntu-dev`, and password-backed sudo on the other nine. The remaining seven entries are the Windows hosts and two physical laptops. Every entry is unrestricted, Executor holds no approval policy for this connection, and egress is unrestricted by my decision on 2026-09-03.

The gateway container needs the host Docker socket, which gives it control of Docker Engine on `docker-blue`. That socket is the main trust boundary. Otherwise the gateway runs with a read-only root filesystem, no Linux capabilities, `no-new-privileges`, 256 MiB, half a CPU, a 256-process limit and bounded JSON logs. Both server services are limited to one CPU and 512 MiB.

Routine checks, image updates and server additions are in the [Runbook](Documentation/Runbook.md).

## Records

- [Access Paths](../../Architecture/Access-Paths.md): agent access alongside the other paths into the lab

- [Runbook](Documentation/Runbook.md)
- [Compose reference](Configuration/docker-compose.yml)
- [Environment template](Configuration/.env.example)
- [UniFi service secret template](Configuration/unifi-network.env.example)
- [SSH Manager secret template](Configuration/ssh-manager.env.example)
- Legacy SSH Manager server reference, `Configuration/ssh-manager-servers.env`, local only
- [UniFi catalog](Configuration/catalogs/unifi-network.yaml)
- [UniFi full-access Dockerfile](Configuration/Dockerfile.unifi-network)
- [UniFi full-access build patch](Configuration/patches/unifi-network-mcp-0.29.3-full-access.py)
- [SSH Manager catalog](Configuration/catalogs/ssh-manager.yaml)
- [SSH Manager Dockerfile](Configuration/Dockerfile.ssh-manager)
- [SSH Manager homelab patch](Configuration/patches/mcp-ssh-manager-3.8.5-homelab.patch)
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
- [Dockhand registry and agent cutover](../Dockhand/Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md), which moved both server images to Forgejo
- [Cutover script](Scripts/ssh-manager-shared-server-cutover.sh)
- [Nightly restart timer and service](Configuration/systemd/)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Executor integration](../Executor/Documentation/Change%20Records/Docker%20MCP%20Gateway%20Integration%20-%202026-08-31.md)
- [Executor integration separation](../Executor/Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md)

## Upstream

- [Docker MCP Gateway documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/)
- [Docker MCP Gateway repository](https://github.com/docker/mcp-gateway)
- [Official container package](https://hub.docker.com/r/docker/mcp-gateway)
- [UniFi Network MCP repository](https://github.com/sirkirby/unifi-mcp)
- [SSH Manager MCP repository](https://github.com/bvisible/mcp-ssh-manager)
