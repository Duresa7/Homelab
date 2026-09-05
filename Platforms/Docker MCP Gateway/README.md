# Docker MCP Gateway

**Created:** 2026-08-30  
**Last updated:** 2026-09-03

I run two isolated Docker MCP Gateway endpoints on `docker-blue`. One serves UniFi Network MCP and the other serves SSH Manager MCP. Keeping them on separate endpoints lets clients such as Executor present them as separate integrations instead of one combined tool catalog.

## Current State

| Item | Value |
|---|---|
| Gateway version | 0.43.3, pinned by digest |
| OCI image | `docker.io/docker/mcp-gateway:v0.43.3` |
| Pinned manifest digest | `sha256:e3ee13818cb067a506c5e9acdb2bb4fe0e601caef7d116fc329755782f1a3cfa` |
| Host | `docker-blue` (`192.168.40.39`) |
| UniFi container | `docker-mcp-gateway` |
| UniFi MCP endpoint | `http://192.168.40.39:8811/mcp`, 5 gateway tools |
| UniFi health endpoint | `http://192.168.40.39:8811/health` |
| SSH Manager container | `ssh-manager-mcp-gateway` |
| SSH Manager MCP endpoint | `http://192.168.40.39:8812/mcp`, 37 tools |
| SSH Manager health endpoint | `http://192.168.40.39:8812/health` |
| Live Compose path | `/opt/docker/mcp-gateway/docker-compose.yml` |
| Live configuration | `/opt/docker/mcp-gateway/config` |
| Gateway token file | `/opt/docker/mcp-gateway/.env`, two distinct bearer tokens, root-owned mode `0600` |
| UniFi secret file | `/opt/docker/mcp-gateway/unifi-secrets.env`, root-owned mode `0600` |
| SSH Manager secret file | `/opt/docker/mcp-gateway/ssh-manager.env`, root-owned mode `0600` |
| Servers | UniFi Network MCP 0.29.3 with a full-access overlay, started by the gateway as a managed container; SSH Manager MCP as a persistent service the gateway reaches over HTTP |
| Local server images | `homelab/unifi-network-mcp:0.29.3-full-access` started by the gateway, `homelab/mcp-ssh-manager:latest` run as the `mcp-ssh-manager` service |
| SSH Manager version | 3.8.5, 37 tools, 18 configured servers |
| UniFi controller | `192.168.1.1:443`, site `default` |
| Catalogs | `/opt/docker/mcp-gateway/config/catalogs/unifi-network.yaml`, `.../ssh-manager.yaml` |
| SSH Manager server definitions | `/opt/docker/mcp-gateway/ssh-manager-servers.env`, the eighteen entries |
| SSH Manager server lifetime | One persistent `mcp-ssh-manager` Compose service shared by every client session |
| Restart policy | `unless-stopped` |

Both MCP endpoints use Streamable HTTP and require different bearer tokens. The tokens are held in the approved credential store and the live `.env`; they are not in this repository. Executor reaches each internal HTTP endpoint directly through separate personal connections named `unifiMcpGateway` and `sshManagerMcpGateway`. No DNS record or TLS proxy fronts either gateway endpoint.

The UniFi server runs through the gateway's headless catalog mode and starts as a managed stdio container when a client calls it. Lazy registration exposes the server through the gateway's five discovery and execution tools instead of publishing the entire UniFi catalog at once. The local administrator credentials and Integration API key come from the approved credential store and the root-owned UniFi secret file. Create, update, and delete are enabled, and bypass mode executes mutations without the preview-confirm gate. The local 0.29.3 image overlay makes bypass authoritative when FastMCP materializes an omitted `confirm` argument as `false`; it changes no controller logic, validation, or redaction. The catalog declares `192.168.1.1:443` as the managed container's only allowed host, but the gateway enforces `allowHosts` only under `--block-network`, which this service does not pass, so the limit is declared and not applied. I decided on 2026-09-03 to leave it that way rather than restrict either server.

SSH Manager has no upstream image, so I build `homelab/mcp-ssh-manager:latest` on `docker-blue` from the tracked [Dockerfile](Configuration/Dockerfile.ssh-manager). The build applies a 3.8.5-specific [homelab patch](Configuration/patches/mcp-ssh-manager-3.8.5-homelab.patch) for bounded inline remote-client transfers and actual SSH2 host-key comparison.

Since 2026-09-03 that image runs as its own Compose service rather than as a container the gateway starts. `mcp-ssh-manager` speaks stdio only, so [mcp-proxy](https://github.com/sparfenyuk/mcp-proxy) 0.12.0 is installed in the image and fronts it: it spawns the server once and serves it over Streamable HTTP on port 8080, multiplexing every HTTP caller onto that one process. The catalog entry is a `remote` server at `http://ssh-manager:8080/mcp`, reached over the project network and published on no host port. Because the gateway rejects a non-HTTPS remote by default, its service sets `DOCKER_MCP_ALLOW_INSECURE_REMOTE_URLS=1`. The reasoning and the alternatives are in the [shared server change record](Documentation/Change%20Records/SSH%20Manager%20Shared%20Server%20Cutover%20-%202026-09-03.md).

The eighteen server definitions live in `Configuration/ssh-manager-servers.env`, which is not versioned, and the private key and ten sudo passwords in the root-owned `ssh-manager.env`, both read by that service. The key is materialized at mode `0600` on a `/keys` tmpfs at start and is never in an image layer. All eighteen answer. The five Proxmox nodes and `docker-main` authenticate as root; `ansible-01` and `ubuntu-dev` reach root through passwordless sudo; the other ten use their configured sudo values. Every entry is unrestricted, and Executor has no approval policy for this connection. Egress is deliberately unrestricted, decided 2026-09-03: the server may reach any machine I add to it. The catalog's `allowHosts` never applied here, and it was never enforced for the managed container either because that needs `--block-network`.

The official container deployment requires the host Docker socket. This gives the gateway control of Docker Engine on `docker-blue`, which is necessary for starting managed MCP server containers and is the deployment's main trust boundary. The gateway container otherwise has a read-only root filesystem, no Linux capabilities, `no-new-privileges`, a 256 MiB memory limit, a half-CPU limit, a 256-process limit, and bounded JSON logs. Future managed MCP server containers default to one CPU and 512 MiB through the gateway arguments.

## Routine Operations

Run on `docker-blue` with elevation:

```bash
cd /opt/docker/mcp-gateway
docker compose config --quiet
docker compose ps
docker compose logs --tail 100 gateway
docker compose logs --tail 100 ssh-manager-gateway
docker stats docker-mcp-gateway ssh-manager-mcp-gateway --no-stream
curl -fsS http://192.168.40.39:8811/health
curl -fsS http://192.168.40.39:8812/health
```

The gateway stays on the 0.43.3 digest for now. The 2026-09-03 test of `:latest` was rolled back because it started one SSH Manager container per client session, but 0.43.3 does the same: the pool keys kept containers by session in both, so that test did not distinguish them and the pin is not a compatibility requirement. A future update needs `docker compose pull` followed by `docker compose up -d --wait`, both endpoint checks, real UniFi and SSH tool calls, and a count of `Client initialized` against `Running` lines in the log after several parallel calls. Update UniFi MCP by changing the pinned upstream version and digest in `Dockerfile.unifi-network`, confirming the build patch still matches exactly one permission-wrapper block, then rebuilding the local image:

```bash
cd /opt/docker/mcp-gateway
docker build --no-cache -f Dockerfile.unifi-network -t homelab/unifi-network-mcp:0.29.3-full-access .
docker run --rm --network none --entrypoint python homelab/unifi-network-mcp:0.29.3-full-access -c 'import importlib.metadata as m; print(m.version("unifi-network-mcp"))'
docker compose up -d --force-recreate gateway
```

Use a new local tag when the upstream version changes. If upstream makes bypass mode authoritative after FastMCP supplies default arguments, remove the overlay rather than carrying a redundant patch. Verify health, bearer-token enforcement, an authenticated system-information read, an Integration API read, and a no-confirm mutation probe after the recreation.

Update SSH Manager by rebuilding its image, since it tracks `latest` and has no upstream registry:

```bash
cd /opt/docker/mcp-gateway
docker build --no-cache -f Dockerfile.ssh-manager -t homelab/mcp-ssh-manager:latest .
docker run --rm --entrypoint sh homelab/mcp-ssh-manager:latest -c 'npm ls -g --depth=0 | grep mcp-ssh-manager'
docker compose up -d --force-recreate ssh-manager-gateway
```

Record the resolved version, then verify with an `ssh_list_servers` call and one `ssh_execute` against a reachable host.

One `mcp-ssh-manager` process serves every caller, which is what keeps its pooled SSH connections, `ssh_session_*` interactive shells, tunnels and history shared across calls the way a local install does. The gateway holds one client session to it per Executor session, but those are HTTP sessions against one process, not containers, so nothing accumulates:

```bash
docker ps --filter label=docker-mcp-name=ssh-manager   # expected: none
docker compose ps ssh-manager                          # expected: one, healthy
curl -fsS http://127.0.0.1:8080/status                  # from inside the container
```

Before this cutover the gateway kept one managed container per client session and released it only when the client closed that session, which Executor never does. The count reached 22 and 192 of the gateway's 256 processes on 2026-09-03, and 27 containers exhausted it on 2026-09-02. Restarting the gateway was the only remedy. The [troubleshooting record](Documentation/Troubleshooting/Managed%20SSH%20Manager%20Containers%20Accumulated%20Under%20long-lived%20-%202026-09-03.md) holds that diagnosis.

A local install got a fresh process every time Claude Code was reopened. Executor never signals the end of a session, so nothing can trigger that here; instead the systemd timer [mcp-ssh-manager-restart.timer](Configuration/systemd/mcp-ssh-manager-restart.timer) restarts the service every day at 4 AM Eastern, decided 2026-09-03. The restart takes about a second, the gateway is not touched and its forwarded sessions survive it, and any interactive session or tunnel left open by an agent is cleared. The same restart by hand:

```bash
cd /opt/docker/mcp-gateway
docker compose restart ssh-manager          # or: systemctl start mcp-ssh-manager-restart.service
systemctl list-timers mcp-ssh-manager-restart.timer
```

## Records

- [Compose reference](Configuration/docker-compose.yml)
- [Environment template](Configuration/.env.example)
- [UniFi secret template](Configuration/unifi-secrets.env.example)
- [SSH Manager secret template](Configuration/ssh-manager.env.example)
- SSH Manager server definitions, `Configuration/ssh-manager-servers.env`, local only
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
- [Docker MCP Gateway v2 compatibility rollback](Documentation/Change%20Records/Docker%20MCP%20Gateway%20v2%20Compatibility%20Rollback%20-%202026-09-03.md)
- [SSH Manager shared server cutover](Documentation/Change%20Records/SSH%20Manager%20Shared%20Server%20Cutover%20-%202026-09-03.md)
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
