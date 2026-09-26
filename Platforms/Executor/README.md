# Executor

**Created:** 2026-08-30  
**Last updated:** 2026-09-25

I run the self-hosted Executor MCP integration service on `docker-blue`. It gives my MCP clients one endpoint in front of the SSH Manager, UniFi, Wazuh, Cloudflare and other integrations.

## Current State

| Item | Value |
|---|---|
| Version | 1.6.10, read live on 2026-09-24 |
| Upgrade to 1.6.10 | The running container was created at 3:00 AM EDT on 2026-09-19, the day after upstream published [v1.6.10](https://github.com/UsefulSoftwareCo/executor/releases/tag/v1.6.10); the earlier version, 1.6.8, is recorded on 2026-09-14 |
| OCI image | `ghcr.io/usefulsoftwareco/executor-selfhost:latest` (rolling); on 2026-09-21 the running digest matched the upstream `1.6.10` tag |
| Host | `docker-blue` (CT 108, `192.168.40.39`) |
| Internal URL | `https://mcp.alphasecunited.com`, through Nginx Proxy Manager |
| Upstream listener | `192.168.40.39:4788` |
| Live Compose path | `/opt/docker/executor/docker-compose.yml` |
| Persistent state | `/opt/docker/executor/data` |
| Restart policy | `unless-stopped` |
| Tool-call limit | 60 seconds of active work per MCP tool call, hard-coded in 1.6.10 |

## Integrations

| Integration | Connection | Tools | Access |
|---|---|---|---|
| UniFi MCP (`unifi-mcp-gateway`) | `unifiMcpGateway`, `http://192.168.40.39:8811/mcp` | 5 | Read, create, update and delete; mutations run without confirmation |
| SSH Manager MCP (`ssh-manager-mcp-gateway`) | `sshManagerMcpGateway`, `http://192.168.40.39:8812/mcp` | 37 | 24 servers, unrestricted mode |
| Wazuh MCP (`wazuh-mcp-server`) | `localWazuh`, `http://192.168.72.2:3000/mcp` | 41 | Read-only: the bearer credential holds only `wazuh:read` |
| Cloudflare Account MCP (`cloudflare_account`) | `cloudflareAccount`, `https://mcp.cloudflare.com/mcp` | 3 | Full-access account API token, every account and zone permission group |
| Draw.io MCP (`drawio`) | `drawio`, `https://mcp.draw.io/mcp` | 2 | No authentication |
| Brandfetch MCP (`brandfetch`) | `brandfetch`, `https://mcp.brandfetch.io/mcp` | 6 | Encrypted bearer credential |
| Excalidraw, Mermaid Chart, Microsoft Learn, Miro MCP, Supabase MCP | Connected on or before 2026-09-14 | | No change record yet |

I read the connection inventory on 2026-09-14. Each gateway connection keeps its own bearer token in Executor's encrypted credential provider, and the integration header maps are empty.

## Access and Trust

Executor is internal only: UniFi resolves `mcp.alphasecunited.com` to Nginx Proxy Manager, and one UniFi policy lets only `192.168.85.2` reach `192.168.40.39:4788`. No public DNS record or WAN forward exists.

The container runs with a read-only root filesystem, no Linux capabilities, `no-new-privileges`, a 256-process limit and bounded JSON logs. Local STDIO MCP servers and analytics are off. Local-network integrations are on, so Executor can reach the two gateways and Wazuh MCP.

The integrations configured on 2026-09-06 and Draw.io, added on 2026-09-14, carry a workspace policy of Always run, so their tools do not wait for approval. Without one, Executor pauses any tool whose annotations mark it as modifying state, which the Cloudflare `execute` tool did on 2026-09-06 before its policy existed.

That makes Executor a root path into the lab. On 2026-09-24 `ssh_list_servers` returned 24 entries. On the 17 Linux nodes and guests, the recorded privilege paths reach root: direct root login on the five Proxmox nodes and `docker-main`, password-backed sudo on nine guests, and passwordless sudo on `ansible-01` and `ubuntu-dev`. The other seven entries are HQ-DC01, HQ-DC02 and HQ-MGT01 as `Administrator`, ObiPC, win11-dev, and the physical laptops `surface_pro` and `parrot`; I have not swept their privilege level. The UniFi and Cloudflare connections can change or delete anything they reach.

My three Codex profiles and two Claude Code profiles on `ubuntu-dev` reach Executor as one user-scoped remote MCP server named `executor` at `https://mcp.alphasecunited.com/mcp?search_tools=true`, all over OAuth. Neither client adds an approval gate: Codex approves Executor tools without prompting, and Claude Code allows `mcp__executor__*`.

## Records

- [Access Paths](../../Architecture/Access-Paths.md): agent access alongside the other paths into the lab

- [Active Work Timeout in 1.6.10 - 2026-09-21](Documentation/Troubleshooting/Active%20Work%20Timeout%20in%201.6.10%20-%202026-09-21.md), the 1.6.10 version check and the 60-second limit
- [Brandfetch MCP integration](Documentation/Change%20Records/Brandfetch%20MCP%20Integration%20-%202026-09-14.md)
- [Brandfetch MCP compatibility assessment](Documentation/Brandfetch%20MCP%20Compatibility%20-%202026-09-14.md)
- [Draw.io MCP integration](Documentation/Change%20Records/Draw.io%20MCP%20Integration%20-%202026-09-14.md)
- [Draw.io MCP compatibility assessment](Documentation/Draw.io%20MCP%20Compatibility%20-%202026-09-14.md)
- [Cloudflare Account MCP integration](Documentation/Change%20Records/Cloudflare%20Account%20MCP%20Integration%20-%202026-09-06.md)
- [Update to 1.6.8](Documentation/Change%20Records/Update%20to%201.6.8%20-%202026-09-06.md)
- [Integration search tools](Documentation/Change%20Records/Integration%20Search%20Tools%20-%202026-09-06.md)
- [Compose reference](Configuration/docker-compose.yml)
- [Runbook](Documentation/Runbook.md)
- [Troubleshooting](Documentation/Troubleshooting/README.md)
- [Initial deployment](Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md)
- [Docker MCP Gateway integration](Documentation/Change%20Records/Docker%20MCP%20Gateway%20Integration%20-%202026-08-31.md)
- [MCP integration separation](Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md)
- [Connection metadata cleanup](Documentation/Change%20Records/Connection%20Metadata%20Cleanup%20-%202026-09-01.md)
- [Agent client cutover](Documentation/Change%20Records/Agent%20Client%20Cutover%20-%202026-08-31.md)
- [UniFi full agent access](../Docker%20MCP%20Gateway/Documentation/Change%20Records/UniFi%20Full%20Agent%20Access%20-%202026-09-01.md)
- [SSH Manager fleet reach completion](../Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md)
- [Wazuh MCP Server and Executor integration](../Wazuh/Documentation/Change%20Records/MCP%20Server%20and%20Executor%20Integration%20-%202026-09-03.md)

## Upstream

- [Hosted Docker documentation](https://executor.sh/docs/hosted/docker)
- [Container package](https://github.com/UsefulSoftwareCo/executor/pkgs/container/executor-selfhost)
