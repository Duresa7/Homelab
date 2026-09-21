# Executor

**Created:** 2026-08-30  
**Last updated:** 2026-09-21

I run the self-hosted Executor MCP integration service on `docker-blue`. It is available only through internal DNS at `https://mcp.alphasecunited.com`; no public DNS record or WAN forwarding exists.

## Current State

| Item | Value |
|---|---|
| Version | 1.6.10, verified live on 2026-09-21 |
| OCI image | `ghcr.io/usefulsoftwareco/executor-selfhost:latest` |
| Image policy | Rolling `latest`; the running image matches the upstream 1.6.10 digest, verified on 2026-09-21 |
| Host | `docker-blue` (`192.168.40.39`) |
| Internal URL | `https://mcp.alphasecunited.com` |
| Upstream listener | `192.168.40.39:4788` |
| Live Compose path | `/opt/docker/executor/docker-compose.yml` |
| Persistent state | `/opt/docker/executor/data` |
| Connected integrations | Brandfetch MCP, Cloudflare Account MCP, Draw.io MCP, Excalidraw (`excalidraw_app_demo`), Mermaid Chart (`mermaid_chart`), Microsoft Learn, Miro MCP, SSH Manager MCP, Supabase MCP, UniFi MCP, Wazuh MCP; connection inventory verified on 2026-09-14 |
| Cloudflare Account MCP connection | Personal connection `cloudflareAccount` on integration `cloudflare_account` at `https://mcp.cloudflare.com/mcp`, full-access account API token as a Bearer header, every account and zone permission group by decision, 3 tools (`docs`, `execute`, `search`), `execute` runs without approval under the workspace Always run policy; OAuth on this server fails because Executor's client metadata document is not publicly reachable |
| UniFi connection | Personal connection `unifiMcpGateway`, 5 tools |
| SSH Manager connection | Personal connection `sshManagerMcpGateway`, 37 tools |
| Wazuh connection | Personal connection `localWazuh`, 41 read-only tools |
| Draw.io connection | Personal connection `drawio` on integration `drawio`, remote endpoint `https://mcp.draw.io/mcp`, no authentication, 2 tools verified through Executor on 2026-09-14 |
| Brandfetch connection | Personal connection `brandfetch` on integration `brandfetch`, endpoint `https://mcp.brandfetch.io/mcp`, encrypted bearer credential, 6 tools discovered and brand search verified through Executor on 2026-09-14 |
| Restart policy | `unless-stopped` |

I checked for updates on 2026-09-21 through SSH Manager on `docker_blue`. The running container and image labels both report 1.6.10, the container reports `healthy`, and the direct `/api/health` endpoint returns `{"status":"ok"}`. Its repository digest, `sha256:b9e001775d3eb7d662d347c8f7054333c78c1a4fd97cb5a86dc1d1d1406093b9`, matches the official [container package](https://github.com/UsefulSoftwareCo/executor/pkgs/container/executor-selfhost) tagged `latest`, `1.6.10`, and `v1.6.10`. GitHub lists [v1.6.10](https://github.com/UsefulSoftwareCo/executor/releases/tag/v1.6.10), published on 2026-09-18, as the latest release. No update was needed, and I did not pull an image or restart the service. I did not retain a separate terminal capture for this check; the date and procedure of the earlier upgrade to 1.6.10 remain unverified.

Nginx Proxy Manager terminates TLS with the existing wildcard certificate and forwards to the HTTP listener on Docker Blue. UniFi resolves the name to Nginx Proxy Manager and permits only `192.168.85.2` to cross from AlphaSec-Access to `192.168.40.39:4788` for this proxy path.

The container uses a read-only root filesystem, a bounded temporary filesystem, no Linux capabilities, `no-new-privileges`, a 256-process limit, and bounded JSON logs. Local STDIO MCP servers and analytics are disabled. Local-network integrations are enabled so Executor can reach the UniFi gateway at `http://192.168.40.39:8811/mcp`, the SSH Manager gateway at `http://192.168.40.39:8812/mcp`, and Wazuh MCP at `http://192.168.72.2:3000/mcp`.

**Every integration tool call is capped at 60 seconds.** Executor 1.6.8 calls tools through the MCP SDK client with no timeout option, so the SDK default applies and no gateway or SSH Manager setting can extend it. Keep a single call under about 55 seconds and detach longer remote work. [Troubleshooting record](Documentation/Troubleshooting/Integration%20Tool%20Calls%20Time%20Out%20at%2060%20Seconds%20-%202026-09-07.md).

The first administrator account is claimed. Credentials and Executor's generated secret files stay outside this repository.

The gateway endpoints are registered separately. `unifi-mcp-gateway` is displayed as `UniFi MCP`, uses personal connection `unifiMcpGateway`, and discovers 5 UniFi tools. `ssh-manager-mcp-gateway` is displayed as `SSH Manager MCP`, uses personal connection `sshManagerMcpGateway`, and discovers 37 SSH tools. `wazuh-mcp-server` uses personal connection `localWazuh` and discovers 41 tools from the local Manager and Indexer. Each connection keeps its own bearer token in Executor's encrypted credential provider, and all three integration header maps remain empty. The retired combined `docker-mcp-gateway` integration and `dockerMcpGateway` connection are absent.

Each integration configured on 2026-09-06 carried a workspace policy set to Always run; draw.io was added on 2026-09-14 and now has the same explicit Always run policy (`drawio.*`), verified with concurrent tool calls; without such a policy Executor would pause tools whose annotations mark them as modifying state, as the Cloudflare `execute` tool did before its policy existed on 2026-09-06. UniFi permits read, create, update, and delete operations, and its full-access bypass executes mutations without confirmation. The Cloudflare Account MCP token can read and change anything in the Cloudflare account. SSH Manager reaches all eighteen configured servers in unrestricted mode and can obtain root on every one: direct root login on the five Proxmox nodes and `docker-main`, password-backed sudo on ten hosts, and passwordless sudo on `ansible-01` and `ubuntu-dev`. Wazuh is enforced read-only at the MCP server: its bearer credential has only `wazuh:read`, so the 14 active-response and rollback tools never enter Executor's catalog.

My three Codex profiles (`.codex`, `.codex_alt`, and `.codex_personal`) and two Claude Code profiles (default and `.claude_alt`) on `ubuntu-dev` use one user-scoped remote MCP server named `executor` at `https://mcp.alphasecunited.com/mcp?search_tools=true`. I enabled per-integration search tools in all five saved connections on 2026-09-06. I renewed OAuth for both Claude profiles and verified that both report connected at the new URL; fresh authenticated Codex discovery remains unverified. All five connections use OAuth. The direct `ssh-manager` and `unifi-network` client entries, standalone SSH Manager package, and UniFi client plugins are absent. Codex approves Executor tools without prompting, and Claude Code persistently allows `mcp__executor__*`, so the client layer does not add an approval gate to UniFi or SSH Manager.

I permanently deleted the temporary pre-cutover archive on 2026-09-01 after both Claude Code profiles reported Executor connected and Claude Alt passed a live Executor-backed UniFi request. The direct-server files remain absent, and no credential-bearing rollback copy remains.

## Records

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
- [Wazuh MCP Server and Executor integration](../Wazuh/Documentation/Change%20Records/Wazuh%20MCP%20Server%20and%20Executor%20Integration%20-%202026-09-03.md)

## Upstream

- [Hosted Docker documentation](https://executor.sh/docs/hosted/docker)
- [Container package](https://github.com/UsefulSoftwareCo/executor/pkgs/container/executor-selfhost)
