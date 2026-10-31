# SSH Manager Retirement

**Created:** 2026-10-31  
**Last updated:** 2026-10-31  
**Change date:** 2026-10-31  
**Status:** Complete

I removed SSH Manager MCP 3.8.5 and its gateway instance from the `docker-mcp-gateway` project on `docker-blue`. [ssh-mcp](../../../SSH%20MCP/README.md) took over all 26 servers the same day, and I removed SSH Manager only after ssh-mcp had passed on every reachable host, directly and through Executor 2: [Deployment and SSH Manager Replacement](../../../SSH%20MCP/Documentation/Change%20Records/Deployment%20and%20SSH%20Manager%20Replacement%20-%202026-10-31.md).

## Compose Change

The live Compose file held the 26 server definitions as resolved environment settings, 194 `SSH_SERVER_` lines with the sudo passwords among them, so I did not copy it off the host. I removed the `ssh-manager` and `ssh-manager-gateway` services and the `ssh-manager-state` volume from the tracked [Compose reference](../../Configuration/docker-compose.yml). On the host, a script normalized the live file and the new one with `docker compose config --format json`, dropped the two services and the volume from the live result, and compared the rest key by key, printing only key paths. It reported `compose diff after removing SSH Manager: none` before it installed the new file, so nothing else in the project changed.

## What I Removed

On `docker-blue`, run as one script through ssh-mcp:

- `docker compose up -d --remove-orphans` removed `mcp-ssh-manager` and `ssh-manager-mcp-gateway`. `docker-mcp-gateway` and `mcp-unifi-network` were not recreated and still read `Up 3 weeks (healthy)`.
- `docker volume rm ssh-manager-state`, which held the enrolled `known_hosts`, command history and SSH Manager's own settings. ssh-mcp had copied the `known_hosts` first.
- `mcp-ssh-manager-restart.timer` and its service: disabled, unit files deleted, `daemon-reload`. `systemctl list-timers --all` lists no SSH Manager timer.
- `ssh-manager.env`, which held the base64 SSH key and the sudo passwords, and `ssh-manager-servers.env`, both removed with `shred -u`.
- `Dockerfile.ssh-manager`, `ssh-manager-secrets.env.example`, the homelab patch, and `config/catalogs/ssh-manager.yaml`.
- `SSH_MANAGER_MCP_GATEWAY_AUTH_TOKEN` from `.env`, which now holds only `UNIFI_MCP_GATEWAY_AUTH_TOKEN`.
- The `forgejo.alphasecunited.com/homelab-images/mcp-ssh-manager:stable` image from the host (`sha256:c4bb756d...`).

Nothing listens on `192.168.40.39:8812` any more, and `8811` still does. The UniFi gateway's `/health` answered, and a `unifi_list_networks` call through Executor's `unifi` app returned `total_count: 24` afterwards.

Dockhand's imported copy of the project, `/opt/docker/dockhand/stacks/imported/docker_blue/docker-mcp-gateway/compose.yaml` on `docker-main`, still held both services with their resolved sudo passwords. I edited it in place with a script that removed the two services and the volume and printed only names. It reported services `['gateway', 'unifi-network']` afterwards and `SSH_SERVER_ mentions left: 0`. The file stays mode 0600.

I archived the gateway's bearer token item in my password manager, since nothing accepts it now. The tracked Dockerfile, homelab patch, catalog, secret template, restart timer and cutover script moved to [the archive](../../../../Archive/Platforms/Docker%20MCP%20Gateway/) under their original paths.

## Open Items

- Done 2026-10-31: I deleted the `mcp-ssh-manager` package from my Forgejo registry, the `stable` tag and both digests, through the packages API; each returned 204 and a relist shows none. Forgejo frees the blobs in its own cleanup.

## Leftovers Removed After Cutover

On 2026-10-31, once Executor 2 and ssh-mcp had run cleanly, I removed what the old setup left behind:

- On `docker-blue`: the September compose backup and recreate log in `/root`, which still held SSH Manager's server definitions; an orphaned anonymous volume from 2026-08-31 laid out like the UniFi gateway's `/misc` volume, most likely left by SSH Manager's gateway; and 0.94 GB of unused build cache. Every remaining container kept running, and both health checks returned 200.
- On `docker-network`: the 13 access and error logs of deleted NPM proxy host 27.
- On `ubuntu-dev`: Executor 1 OAuth tokens in both Claude Code profiles and in the keyring for Codex, the SSH Manager client helper script, and the local, untracked `ssh-manager-servers.env` reference copy in this platform's `Configuration` folder.

I kept the UniFi policy `Allow docker-blue SSH Manager to Proxmox`. Only its name is stale: ssh-mcp runs from the same address and uses it to reach the Proxmox nodes.
