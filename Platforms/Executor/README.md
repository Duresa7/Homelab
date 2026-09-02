# Executor

**Created:** 2026-08-30  
**Last updated:** 2026-09-01

I run the self-hosted Executor MCP integration service on `docker-blue`. It is available only through internal DNS at `https://mcp.alphasecunited.com`; no public DNS record or WAN forwarding exists.

## Current State

| Item | Value |
|---|---|
| Version | 1.6.7 |
| OCI image | `ghcr.io/usefulsoftwareco/executor-selfhost:1.6.7` |
| Pinned image digest | `sha256:c8dd83a5dba8ac992dfe1ded4aa65ae4e7f52ec31fddbe2af5b49ffebe5bbfa7` |
| Host | `docker-blue` (`192.168.40.39`) |
| Internal URL | `https://mcp.alphasecunited.com` |
| Upstream listener | `192.168.40.39:4788` |
| Live Compose path | `/opt/docker/executor/docker-compose.yml` |
| Persistent state | `/opt/docker/executor/data` |
| Connected integrations | Cloudflare MCP, Supabase MCP, UniFi MCP, SSH Manager MCP |
| UniFi connection | Personal connection `unifiMcpGateway`, 5 tools |
| SSH Manager connection | Personal connection `sshManagerMcpGateway`, 37 tools |
| Restart policy | `unless-stopped` |

Nginx Proxy Manager terminates TLS with the existing wildcard certificate and forwards to the HTTP listener on Docker Blue. UniFi resolves the name to Nginx Proxy Manager and permits only `192.168.85.2` to cross from AlphaSec-Access to `192.168.40.39:4788` for this proxy path.

The container uses a read-only root filesystem, a bounded temporary filesystem, no Linux capabilities, `no-new-privileges`, a 256-process limit, and bounded JSON logs. Local STDIO MCP servers and analytics are disabled. Local-network integrations are enabled so Executor can reach the UniFi gateway at `http://192.168.40.39:8811/mcp` and the SSH Manager gateway at `http://192.168.40.39:8812/mcp`.

The first administrator account is claimed. Credentials and Executor's generated secret files stay outside this repository.

The gateway endpoints are registered separately. `unifi-mcp-gateway` is displayed as `UniFi MCP`, uses personal connection `unifiMcpGateway`, and discovers 5 UniFi tools. `ssh-manager-mcp-gateway` is displayed as `SSH Manager MCP`, uses personal connection `sshManagerMcpGateway`, and discovers 37 SSH tools. Each connection keeps its own bearer token in Executor's encrypted credential provider, and both integration header maps remain empty. The retired combined `docker-mcp-gateway` integration and `dockerMcpGateway` connection are absent.

No Executor policy overrides cover either connection. The gateway tools therefore carry no Executor approval requirement today. UniFi permits read, create, update, and delete operations, and its full-access bypass executes mutations without confirmation. SSH Manager reaches all eighteen configured servers in unrestricted mode and can obtain root on every one: direct root login on the five Proxmox nodes and `docker-main`, password-backed sudo on ten hosts, and passwordless sudo on `ansible-01` and `ubuntu-dev`.

Codex and Claude Code on `ubuntu-dev` each use one user-scoped remote MCP server named `executor` at `https://mcp.alphasecunited.com/mcp`. Both connections use OAuth. The direct `ssh-manager` and `unifi-network` client entries, standalone SSH Manager package, and UniFi client plugins are absent. Codex approves Executor tools without prompting, and Claude Code persistently allows `mcp__executor__*`, so the client layer does not add an approval gate to UniFi or SSH Manager.

I permanently deleted the temporary pre-cutover archive on 2026-09-01 after both Claude Code profiles reported Executor connected and Claude Alt passed a live Executor-backed UniFi request. The direct-server files remain absent, and no credential-bearing rollback copy remains.

## Records

- [Compose reference](Configuration/docker-compose.yml)
- [Runbook](Documentation/Runbook.md)
- [Initial deployment](Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md)
- [Docker MCP Gateway integration](Documentation/Change%20Records/Docker%20MCP%20Gateway%20Integration%20-%202026-08-31.md)
- [MCP integration separation](Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md)
- [Connection metadata cleanup](Documentation/Change%20Records/Connection%20Metadata%20Cleanup%20-%202026-09-01.md)
- [Agent client cutover](Documentation/Change%20Records/Agent%20Client%20Cutover%20-%202026-08-31.md)
- [UniFi full agent access](../Docker%20MCP%20Gateway/Documentation/Change%20Records/UniFi%20Full%20Agent%20Access%20-%202026-09-01.md)
- [SSH Manager fleet reach completion](../Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md)

## Upstream

- [Hosted Docker documentation](https://executor.sh/docs/hosted/docker)
- [Container package](https://github.com/UsefulSoftwareCo/executor/pkgs/container/executor-selfhost)
