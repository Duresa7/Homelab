# Executor

**Created:** 2026-08-30  
**Last updated:** 2026-08-30

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
| Restart policy | `unless-stopped` |

Nginx Proxy Manager terminates TLS with the existing wildcard certificate and forwards to the HTTP listener on Docker Blue. UniFi resolves the name to Nginx Proxy Manager and permits only `192.168.85.2` to cross from AlphaSec-Access to `192.168.40.39:4788` for this proxy path.

The container uses a read-only root filesystem, a bounded temporary filesystem, no Linux capabilities, `no-new-privileges`, a 256-process limit, and bounded JSON logs. Local-network tools and local STDIO MCP servers are disabled. Analytics are disabled.

The first administrator account still needs to be claimed through the setup form. Credentials and Executor's generated secret files stay outside this repository.

## Records

- [Compose reference](Configuration/docker-compose.yml)
- [Runbook](Documentation/Runbook.md)
- [Initial deployment](Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md)

## Upstream

- [Hosted Docker documentation](https://executor.sh/docs/hosted/docker)
- [Container package](https://github.com/UsefulSoftwareCo/executor/pkgs/container/executor-selfhost)
