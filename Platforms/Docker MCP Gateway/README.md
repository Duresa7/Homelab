# Docker MCP Gateway

**Created:** 2026-08-30  
**Last updated:** 2026-09-02

I run two isolated Docker MCP Gateway endpoints on `docker-blue`. One serves UniFi Network MCP and the other serves SSH Manager MCP. Keeping them on separate endpoints lets clients such as Executor present them as separate integrations instead of one combined tool catalog.

## Current State

| Item | Value |
|---|---|
| Version | 0.43.3 |
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
| SSH Manager secret file | `/opt/docker/mcp-gateway/ssh-manager-secrets.env`, root-owned mode `0600` |
| Managed servers | UniFi Network MCP 0.29.3 with a full-access overlay; SSH Manager MCP tracking `latest` |
| Managed images | `homelab/unifi-network-mcp:0.29.3-full-access`, `homelab/mcp-ssh-manager:latest` |
| SSH Manager version | 3.8.5, 37 tools, 18 configured servers |
| UniFi controller | `192.168.1.1:443`, site `default` |
| Catalogs | `/opt/docker/mcp-gateway/config/catalogs/unifi-network.yaml`, `.../ssh-manager.yaml` |
| SSH Manager server lifetime | `--long-lived`: one managed container for the gateway's lifetime, shared across client sessions |
| Restart policy | `unless-stopped` |

Both MCP endpoints use Streamable HTTP and require different bearer tokens. The tokens are held in the approved credential store and the live `.env`; they are not in this repository. Executor reaches each internal HTTP endpoint directly through separate personal connections named `unifiMcpGateway` and `sshManagerMcpGateway`. No DNS record or TLS proxy fronts either gateway endpoint.

The UniFi server runs through the gateway's headless catalog mode and starts as a managed stdio container when a client calls it. Lazy registration exposes the server through the gateway's five discovery and execution tools instead of publishing the entire UniFi catalog at once. The local administrator credentials and Integration API key come from the approved credential store and the root-owned UniFi secret file. Create, update, and delete are enabled, and bypass mode executes mutations without the preview-confirm gate. The local 0.29.3 image overlay makes bypass authoritative when FastMCP materializes an omitted `confirm` argument as `false`; it changes no controller logic, validation, or redaction. The catalog still limits the managed container's network access to `192.168.1.1:443`.

SSH Manager has no upstream image, so I build `homelab/mcp-ssh-manager:latest` on `docker-blue` from the tracked [Dockerfile](Configuration/Dockerfile.ssh-manager). The build applies a 3.8.5-specific [homelab patch](Configuration/patches/mcp-ssh-manager-3.8.5-homelab.patch) for bounded inline remote-client transfers and actual SSH2 host-key comparison. Its private key arrives as a base64 gateway secret rather than a bind mount, because the gateway blocks mounting files it recognises as credentials. All eighteen server definitions are versioned in the catalog, `allowHosts` limits managed-container egress to those eighteen addresses on TCP 22, and all eighteen answer. The source key and the ten password-backed sudo values live in the root-owned SSH Manager secret file. The entrypoint materializes the key at mode `0600` inside each managed container, where it remains until that container is removed. The five Proxmox nodes and `docker-main` authenticate as root; `ansible-01` and `ubuntu-dev` reach root through passwordless sudo; the other ten use their configured sudo values. Every entry is unrestricted, and Executor has no approval policy for this connection.

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

Update the gateway by changing its tag and digest in the versioned Compose reference. Update UniFi MCP by changing the pinned upstream version and digest in `Dockerfile.unifi-network`, confirming the build patch still matches exactly one permission-wrapper block, then rebuilding the local image:

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

SSH Manager is marked `longLived` because its `ssh_session_*` tools keep interactive shell state between calls, and since 2026-09-02 the gateway runs with `--long-lived`, so it starts one managed container and shares it across every client session for as long as the gateway runs. Executor opens a new MCP session on every `execute` call and never closes it; without the gateway flag, each call left its own container and stdio bridge behind until the gateway hit its 256-process limit after about eighteen hours. Exactly one managed container is the expected state:

```bash
docker ps --filter label=docker-mcp-name=ssh-manager
```

A second container is a fault, not a leftover. Restart the gateway to reset the server's interactive session state; Docker removes the managed container through `--rm`, and the `ssh-manager-state` volume retains enrolled host keys and other durable server state.

## Records

- [Compose reference](Configuration/docker-compose.yml)
- [Environment template](Configuration/.env.example)
- [UniFi secret template](Configuration/unifi-secrets.env.example)
- [SSH Manager secret template](Configuration/ssh-manager-secrets.env.example)
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
- [Executor integration](../Executor/Documentation/Change%20Records/Docker%20MCP%20Gateway%20Integration%20-%202026-08-31.md)
- [Executor integration separation](../Executor/Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md)

## Upstream

- [Docker MCP Gateway documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/)
- [Docker MCP Gateway repository](https://github.com/docker/mcp-gateway)
- [Official container package](https://hub.docker.com/r/docker/mcp-gateway)
- [UniFi Network MCP repository](https://github.com/sirkirby/unifi-mcp)
- [SSH Manager MCP repository](https://github.com/bvisible/mcp-ssh-manager)
