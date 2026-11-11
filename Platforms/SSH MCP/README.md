# SSH MCP

**Created:** 2026-10-31  
**Last updated:** 2026-11-10

I run [ssh-mcp](https://github.com/tufantunc/ssh-mcp) on `docker-blue` as the agents' SSH path into the lab. It replaced SSH Manager MCP on 2026-10-31 and kept the same 26 servers under the same names. On 2026-11-04 I added `hermes_01`, and on 2026-11-05 the live configuration held 26 profiles. On 2026-11-10 I renamed `parrot_os_mac` to `macbook_pro`. Agents reach it through [Executor](../Executor/README.md) as the `ssh` app.

## Current State

| Item | Value |
|---|---|
| Version | ssh-mcp 2.22.0 from npm, installed into `node:22-slim` by the tracked [Dockerfile](Configuration/Dockerfile) |
| Image | `homelab/ssh-mcp:2.22.0`, built on `docker-blue` |
| Host | `docker-blue` (CT 108, `192.168.40.39`) |
| Endpoint | `http://192.168.40.39:8813/`, Streamable HTTP at `POST /`, bearer token required; `GET /health` is open |
| Live Compose path | `/opt/docker/ssh-mcp/docker-compose.yml` |
| Live configuration | `/opt/docker/ssh-mcp/config/config.toml`, UID 65532, mode 0600 in a 0700 directory |
| Secrets | `/opt/docker/ssh-mcp/ssh-mcp.env` (bearer token and eleven sudo passwords), root-only at mode 0600, read by Docker at start; `keys/id_ed25519`, owned by the container user (UID 65532) at mode 0400 in a 0700 directory |
| Audit log | `/opt/docker/ssh-mcp/data/ssh-mcp/audit.log`, one JSON record per command, rotated at 100 MB with ten files kept |
| Profiles | 26 on 2026-11-05; the install script reported `profiles: 26`, `pins: 26`, `sudo passwords: 11`. `hermes_01` was added on 2026-11-04: [hermes-01 Provisioning](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/hermes-01%20Provisioning%20-%202026-11-04.md) |
| Profile renames | 2026-11-10: `parrot_os_mac` became `macbook_pro`. I changed the `name` line in the tracked config, in `config.unpinned.toml` and in the live config, leaving the pin, host and key untouched, then sent `HUP`. The log printed `Profiles: added macbook_pro; removed parrot_os_mac.`, `list-connections` still showed 26 profiles, and the live config kept UID 65532 and mode 0600. The profile has no sudo password, so `ssh-mcp.env` did not change. The Mac was off, so the new name is untested against the host. Hermes's `homelab-ops` skill on `hermes-01` and its [tracked copy](../Hermes%20Agent/Configuration/skills/homelab-ops/SKILL.md) use the new name |
| Tools | 15 |
| Restart policy | `unless-stopped` |

The bearer token is in my password manager as `SSH MCP Bearer Token - docker-blue`. Executor's `ssh` app holds it as an encrypted app account, and the deploy script submitted it without it passing through an MCP call.

## Access Model

Every profile is `role = "admin"` on one custom tier, `homelab`, which holds all four command classes: `read-only`, `safe`, `destructive` and `privileged`. `approvalMode = "auto"`, so nothing waits for approval. That matches the unrestricted SSH Manager setup it replaced, where I am the confirmation step.

The profiles reach root the way SSH Manager did: direct root login on the five Proxmox nodes and `docker-main`; passwordless sudo on `ansible-01`, `ubuntu-dev` and `media-01`; password-backed sudo on `alpha-prod-01`, `andor_parrot_os_pc`, `app-01`, `docker-blue`, `docker-network`, `edge-01`, `hermes-01`, `monitor-01`, `security-01`, `splunk-siem` and `surface_pro`. The five Windows profiles log in as `Administrator` on HQ-DC01, HQ-DC02 and HQ-MGT01, `local-obipc` on ObiPC and `dkadi` on win11-dev. `macbook_pro` uses `dkadi`.

ssh-mcp refuses a fixed list whatever the policy grants, and no setting removes it: `shutdown`, `reboot`, `halt`, `poweroff` and `eval` as commands; `rm -rf /`, `mkfs`, `dd of=/dev/`, `iptables -F`, a recursive `chmod 777 /` or `chown /`, `curl | sh`, fork bombs; and any write that names `/etc/cron*`, `/etc/systemd` or an `authorized_keys` file through a redirect, `tee`, `cp`, `mv`, `install`, `dd of=` or an upload. On 2026-10-31 `reboot` and `tee /etc/systemd/system/x.service` were both refused with `POLICY_DENIED`.

Every host key is pinned. [pin-host-keys.py](Scripts/pin-host-keys.py) writes a `trustedHostKey` into each profile from `/opt/docker/ssh-mcp/known_hosts`, which came from SSH Manager's verified store, and the server runs with `--hostKeyMode=strict`, so an unpinned or changed key refuses the connection. The pins are not tracked here.

## How It Differs from SSH Manager

- Commands reach the host's own shell unchanged. SSH Manager re-encoded Windows commands and ate every `$`; ssh-mcp does not, and the Windows hosts' shell is PowerShell 5.1.
- `privileged-command` wraps the whole command in `sudo -S sh -c`, so a `;` chain runs as root throughout.
- No tunnels, rsync, backup, database or health-check helpers: SSH Manager had 37 tools and ssh-mcp has 15. `run-command` covers the commands those helpers ran.
- A command runs for up to 240 seconds and Executor's `ssh` app waits 280. The 60-second ceiling Executor 1 imposed is gone.
- `monitor_01` connects directly. ssh-mcp's ProxyJump through `ansible_01` failed its handshake with `incomplete message` in monitor-01's sshd log, and `docker-blue` reaches `192.168.73.2:22` directly.

## Records

- [Deployment and SSH Manager replacement - 2026-10-31](Documentation/Change%20Records/Deployment%20and%20SSH%20Manager%20Replacement%20-%202026-10-31.md)
- [Runbook](Documentation/Runbook.md)
- [Compose reference](Configuration/docker-compose.yml), [Dockerfile](Configuration/Dockerfile), [configuration without pins](Configuration/config.toml)
- [Install script](Scripts/install-on-docker-blue.sh), [host-key pinning](Scripts/pin-host-keys.py)
- [Fleet smoke test](Tests/fleet-smoke.mjs)
- [Executor 2 migration](../Executor/Documentation/Change%20Records/Executor%202%20Migration%20-%202026-10-31.md), which created the `ssh` app
- [Docker MCP Gateway](../Docker%20MCP%20Gateway/README.md), where SSH Manager ran until 2026-10-31

## Upstream

- [Repository](https://github.com/tufantunc/ssh-mcp) and [security model](https://github.com/tufantunc/ssh-mcp/blob/main/SECURITY.md)
- [npm package](https://www.npmjs.com/package/ssh-mcp)
