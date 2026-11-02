# Executor

**Created:** 2026-08-30  
**Last updated:** 2026-11-02

I run the self-hosted Executor on `docker-blue`. It gives my MCP clients one endpoint in front of SSH, UniFi, Wazuh, Cloudflare and the other integrations. On 2026-10-31 I moved from Executor 1.6.10 to the Executor 2 beta, which is a different server with its own database, and retired Executor 1: [Executor 2 migration](Documentation/Change%20Records/Executor%202%20Migration%20-%202026-10-31.md).

## Current State

| Item | Value |
|---|---|
| Version | 2.0.0-beta.34, apps framework `0.0.1-beta.117` |
| OCI image | `ghcr.io/usefulsoftwareco/executor-selfhost:2.0.0-beta.34`, pinned by digest `sha256:1af389b0a9ffca783c175a514df1667d3e911bd01df63262c9908d90872900e3`; the `beta` tag moves daily |
| Host | `docker-blue` (CT 108, `192.168.40.39`) |
| URL | `https://executor.alphasecunited.com`, through Nginx Proxy Manager proxy host 37; MCP at `/mcp` |
| Upstream listener | `192.168.40.39:4400` |
| Live Compose path | `/opt/docker/executor-v2/docker-compose.yml` |
| Persistent state | `/opt/docker/executor-v2/data` (PGlite database, app source and builds, `auth-secret.key`, `encryption.key`) and `/opt/docker/executor-v2/motel-data` (traces), both UID 1000, mode 0700 |
| Organization | `AlphaSec United`, slug `executor`, one owner signed in with my standard application account |
| App pages | `https://<app-slug>.executor.apps.alphasecunited.com`, base `EXECUTOR_APP_UI_BASE_URL=https://apps.alphasecunited.com` since 2026-11-02, through NPM proxy host 38 and one UniFi A record per page: [app page domain](Documentation/Change%20Records/App%20Page%20Domain%20-%202026-11-02.md) |
| Memory | 757 MiB at idle after the first start; the container limit is 1.5 GiB |
| Restart policy | `unless-stopped` |

## Apps

Each integration is an app, and agents call its tools as `tools.<slug>.<tool>`. The four bearer-token apps are generated from one template by [deploy-bearer-apps.mjs](Scripts/deploy-bearer-apps.mjs) and [bearer-apps.config.mjs](Scripts/bearer-apps.config.mjs). Each declares one app account, linked once for every caller, and lists its server as the provider's only host, so app code holds an opaque handle and Executor substitutes the token only on requests to that host. Sure was added by URL. I removed Brandfetch, Draw.io, Excalidraw, Microsoft Learn, Mermaid Chart, Miro and Supabase on 2026-10-31.

| App | Server | Account | Tools on 2026-10-31 |
|---|---|---|---|
| `ssh` | [ssh-mcp](../SSH%20MCP/README.md), `http://192.168.40.39:8813/` | Bearer token, app account | 15 |
| `unifi` | [UniFi gateway](../Docker%20MCP%20Gateway/README.md), `http://192.168.40.39:8811/mcp` | Bearer token, app account | 5 |
| `wazuh` | [Wazuh MCP Server](../Wazuh/README.md), `http://192.168.72.2:3000/mcp` | `wazuh_` API key as a bearer token, app account; read-only scope | 41 |
| `cloudflare` | `https://mcp.cloudflare.com/mcp` | Account API token as a bearer token, app account | 4 |
| `sure` | [Sure](../Sure/README.md), `https://sure.alphasecunited.com/mcp` | OAuth, my own account | Not connected yet |

No app declares an approval, and an omitted approval runs without asking, so no tool waits for one. That keeps the posture Executor 1 had.

The bearer tokens stay in my password manager under the items named in the config file. The deploy script opens each account's connection with `appAccounts.appConnect` over MCP and posts the token straight to `/api/organizations/<org>/connections/<id>/submit` over HTTPS, so no token passes through an MCP call.

## Access and Trust

Executor is internal only. UniFi resolves `executor.alphasecunited.com` and each app-page name under `executor.apps.alphasecunited.com` to Nginx Proxy Manager, and policy `Allow NPM to docker-blue Executor` lets only `192.168.85.2` reach `192.168.40.39:4400`. No public DNS record or WAN forward exists.

The container runs as UID 1000, the image's `executor` user, with no Linux capabilities, `no-new-privileges`, a 512-process limit and bounded JSON logs. Starting as that user skips the entrypoint's root branch, which would chown the data directories and drop privileges. Unlike Executor 1, the root filesystem is not read-only: I have not tested Executor 2 with one. `/tmp` is a 256 MiB tmpfs.

`EXECUTOR_APPS_ALLOW_PRIVATE_FETCH=true` lets app code reach private addresses. Every app shares that network position, so any app I add can reach the lab. `EXECUTOR_URL_ALLOW_HTTP_ORIGINS` lists `https://sure.alphasecunited.com` as the one private origin Executor's own requests may use, for the add-by-URL check and Sure's OAuth. `EXECUTOR_CATALOG_URL` points **Add app** at Executor's official feed, `https://catalog.executor.sh/index.json`; self-host has no default, and without it the catalog lists only the built-in Executor app: [official app catalog](Documentation/Change%20Records/Official%20App%20Catalog%20-%202026-10-31.md). Analytics are off.

That makes Executor a root path into the lab. Through the `ssh` app it reaches root on every Linux node and guest ssh-mcp holds, and the UniFi and Cloudflare apps can change or delete anything they reach.

## Clients

On `ubuntu-dev`, seven client configs reach Executor as one user-scoped remote MCP server named `executor` at `https://executor.alphasecunited.com/mcp`: Claude Code in `~/.claude.json` and `~/.claude_alt`, Codex in `~/.codex`, `~/.codex_alt` and `~/.codex_personal`, GitHub Copilot CLI in `~/.copilot`, and Antigravity in `~/.gemini/config/mcp_config.json`. I wrote them on 2026-10-31 with `npx add-mcp https://executor.alphasecunited.com/mcp --name executor -g -t http -a <agent> -y` (add-mcp 2.6.0), with `CODEX_HOME` set per Codex profile and `HOME` set to `~/.claude_alt` for the second Claude profile, because add-mcp always writes Claude Code's `~/.claude.json`. The three Codex profiles share one file: `~/.codex_alt/config.toml` and `~/.codex_personal/config.toml` are symlinks to `~/.codex/config.toml`, which T3 Code creates for its shadow homes. add-mcp replaces the file it writes instead of writing through the link, so the per-profile runs turned both links into regular copies, and T3 then refused to start Codex Alt and Codex Personal ("already exists and is not a symlink"). I restored the symlinks the same day, with all three copies byte-identical. Edit Codex settings in `~/.codex/config.toml` only. Each signs in with OAuth in the browser: `/mcp` in Claude Code, `codex mcp login executor` with the profile's `CODEX_HOME` in Codex. Copilot CLI is the exception: it sends its own API key as a fixed `Authorization` header in `~/.copilot/mcp-config.json` (mode 0600), stored in my password manager as `Executor API Token - Copilot CLI ubuntu-dev`. T3 Code starts Copilot in the background in ACP mode, and each of those processes opened the OAuth sign-in page in the browser even though a saved login was in the keyring. With the header there is no sign-in step; an ACP session on 2026-10-31 connected with HTTP 200 and opened no page. Discovery, PKCE and dynamic client registration for a localhost redirect answered correctly on 2026-10-31. The Codex entries carry `default_tools_approval_mode = "approve"`, and Claude Code allows `mcp__executor__*`, so neither adds an approval gate. I do not use Executor from VS Code or Gemini CLI on this host.

Scripts use a personal access token instead, as the bearer token on `https://executor.alphasecunited.com/mcp`. The token is scoped to the one organization, has no expiry, and is in my password manager as `Executor API Token - ubuntu-dev agents`.

## Records

- [Executor 2 migration - 2026-10-31](Documentation/Change%20Records/Executor%202%20Migration%20-%202026-10-31.md)
- [Official app catalog - 2026-10-31](Documentation/Change%20Records/Official%20App%20Catalog%20-%202026-10-31.md)
- [App page domain - 2026-11-02](Documentation/Change%20Records/App%20Page%20Domain%20-%202026-11-02.md)
- [Safari 17 URL.parse polyfill - 2026-11-02](Documentation/Change%20Records/Safari%2017%20URL.parse%20Polyfill%20-%202026-11-02.md)
- [Runbook](Documentation/Runbook.md)
- [Compose reference](Configuration/docker-compose.yml)
- [Bearer app deploy script](Scripts/deploy-bearer-apps.mjs) and [its app table](Scripts/bearer-apps.config.mjs)
- [Troubleshooting](Documentation/Troubleshooting/README.md), which covers Executor 1
- [Access Paths](../../Architecture/Access-Paths.md): agent access alongside the other paths into the lab

Executor 1, 2026-08-30 to 2026-10-31:

- [Initial deployment](Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md)
- [Docker MCP Gateway integration](Documentation/Change%20Records/Docker%20MCP%20Gateway%20Integration%20-%202026-08-31.md)
- [MCP integration separation](Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md)
- [Agent client cutover](Documentation/Change%20Records/Agent%20Client%20Cutover%20-%202026-08-31.md)
- [Connection metadata cleanup](Documentation/Change%20Records/Connection%20Metadata%20Cleanup%20-%202026-09-01.md)
- [Cloudflare Account MCP integration](Documentation/Change%20Records/Cloudflare%20Account%20MCP%20Integration%20-%202026-09-06.md)
- [Integration search tools](Documentation/Change%20Records/Integration%20Search%20Tools%20-%202026-09-06.md)
- [Update to 1.6.8](Documentation/Change%20Records/Update%20to%201.6.8%20-%202026-09-06.md)
- [Brandfetch MCP integration](Documentation/Change%20Records/Brandfetch%20MCP%20Integration%20-%202026-09-14.md) and [compatibility assessment](Documentation/Brandfetch%20MCP%20Compatibility%20-%202026-09-14.md)
- [Draw.io MCP integration](Documentation/Change%20Records/Draw.io%20MCP%20Integration%20-%202026-09-14.md) and [compatibility assessment](Documentation/Draw.io%20MCP%20Compatibility%20-%202026-09-14.md)
- [Rolling image recreation](Documentation/Change%20Records/Rolling%20Image%20Recreation%20-%202026-10-05.md)
- [Wazuh MCP Server and Executor integration](../Wazuh/Documentation/Change%20Records/MCP%20Server%20and%20Executor%20Integration%20-%202026-09-03.md)

## Upstream

- [Self-host with Docker](https://executor.sh/docs/run/self-host)
- [The MCP endpoint](https://executor.sh/docs/mcp)
- [Releases](https://github.com/UsefulSoftwareCo/executor/releases)
