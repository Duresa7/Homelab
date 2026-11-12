# E2B

**Created:** 2026-11-11  
**Last updated:** 2026-11-11

I run [E2B Embed](https://github.com/e2b-dev/runtime/tree/main/embed), the single-machine package of E2B's open-source runtime, on `e2b-01` as a trial. Agents on my machines use it to run code in throwaway Firecracker microVMs on Grey instead of on the machine they run on. A sandbox is restored from a snapshot in well under a second, can reach the internet but not my LAN, and is gone when killed. The trial ends with a keep-or-remove review on 2026-11-25.

## Current State

| Item | Value |
|---|---|
| Host | `e2b-01`, VM 113 on `grey-server`, Ubuntu 26.04.1, kernel `7.0.0-43-generic`, 8 vCPU, 16 GiB fixed, 300 GiB on `local-lvm` (120 GiB until 2026-11-11), `192.168.80.30` on SERVERS-A, `onboot=0`. [Provisioning](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/e2b-01%20Provisioning%20-%202026-11-11.md) |
| Version | Embed 0.30.0 from `e2b-dev/runtime` commit `df41cd32cb7f3838d71625f04ce1e015e12ed046`: API, client-proxy and orchestrator `v0.30.0`, dashboard `v0.5.1`, envd `v0.10.0`, guest kernel `vmlinux-6.1.177`, Firecracker `v1.14`; new template builds use the Firecracker 1.17 line |
| Runtime | Docker Engine 29.9.3, Compose 5.7.1; project in `/opt/e2b`, `.env` mode `0600` |
| Addresses | Dashboard `https://e2b.alphasecunited.com`, API `https://api.e2b.alphasecunited.com`, sandbox traffic `https://sandbox.e2b.alphasecunited.com`, Desktop viewer `https://desktop.e2b.alphasecunited.com`, through Nginx Proxy Manager hosts 39, 40, 41 and 42 with certificate 3 (`*.e2b.alphasecunited.com`, expires 2027-02-09). LAN and VPN only. |
| Access control | UniFi `Allow NPM to e2b-01 E2B` admits only NPM to TCP 3000 to 3002. The VM's [e2b-guard.nft](Configuration/e2b-guard.nft) drops those three from anyone else and the other nine Embed ports, including the unauthenticated control API on 5008, from everywhere off the VM. |
| Authentication | One team API key, held in my password manager with the API's admin token and hash seed, pinned in `/opt/e2b/.env`. The dashboard has no user accounts: you paste the team key, and it keeps it in an httpOnly cookie marked `Secure` since 2026-11-11. |
| Templates | `base` (Debian 12, Python 3.11, 2 vCPU, 512 MiB); `dev` (Python 3.12 with `uv`, Node 22, `git`, `gh`, `build-essential`; 2 vCPU, 1 GiB, 9.4 GB free disk); `code-interpreter-v1` (E2B's Code Interpreter: Jupyter kernels for Python, JavaScript, R, Java and Bash; 2 vCPU, 2 GiB); `desktop` (E2B's Desktop: Xfce and Firefox for computer use; 4 vCPU, 2 GiB) |
| Capacity | `HUGEPAGES=3072` (6 GiB) since 2026-11-11, up from 2048: about twelve 512 MiB sandboxes at full memory, or one `desktop` and one `code-interpreter-v1` at full memory beside small ones; at most 3 starting at once; 64 NBD devices |
| Sandbox network | Internet allowed; 10/8, 172.16/12, 192.168/16, 100.64/10 and link-local denied inside every sandbox (E2B's default) |
| Team limits | Embed's `default_limits` row: `disk_mb` 10240 (raised from 512 on 2026-11-11), sandboxes at most 24 hours per run (`max_length_hours` 24, raised from 1 on 2026-11-11), 20 concurrent, 8 vCPU and 8 GiB per sandbox |
| Telemetry | Embed's built-in OpenTelemetry collector into its own ClickHouse; Wazuh agent `022` on `security-01`; no Prometheus or Discord alerts during the trial |
| Clients | `ubuntu-dev`: `@e2b/cli` 2.23.0, [`~/.config/e2b/env`](Configuration/client-env.reference), and the [e2b-sandbox skill](https://github.com/Duresa7/tools-and-scripts/tree/main/ai-configs/skills/e2b-sandbox) for Claude Code and Codex, which lives in my `tools-and-scripts` repository and is linked in from its clone at `~/Documents/code-projects/tools-and-scripts` |

## Features on this deployment

Probed on 2026-11-11 with SDK 2.63.0 against Embed 0.30.0:

| Feature | State |
|---|---|
| Egress allow and deny lists (`network={"deny_out": [...], "allow_out": [...]}`) | Works. A sandbox limited to `pypi.org` got `200` there and could not connect to `github.com`. |
| Pause on timeout and auto-resume (`--lifecycle.ontimeout pause --lifecycle.autoresume`) | Works. The sandbox read `paused` after its 10-second timeout and kept its files when reconnected. |
| Persistent volumes | Off: `501: volumes content token signing is not supported by this deployment`. Embed sets `VOLUME_TOKEN_ENABLED=false`; turning it on needs a token issuer and signing key and another compose patch, which Embed does not document. |
| Secret injection | Not available: `403: Secrets are not available for this team`. The API needs E2B's separate secrets backend and a feature flag that comes from LaunchDarkly. |
| MCP gateway in a sandbox | Not available: `404: template 'mcp-gateway' not found`. E2B does not publish that template for self-hosting. |
| Workload identity tokens | Not configured; the API runs with an empty identity-provider list. Not tested. |
| Dashboard "Create a Sandbox" button | A link to `/docs/quickstart`, which only exists on `e2b.dev`; here it returns 404. The dashboard cannot create sandboxes in any version; the CLI and SDK do. |

## How a sandbox is reached

The CLI or SDK calls the API at `api.e2b.alphasecunited.com` to create a sandbox. The API places it, and the orchestrator restores the template's snapshot into a new Firecracker microVM with memory loaded on demand and a copy-on-write disk. Commands, files and ports then go to `sandbox.e2b.alphasecunited.com`, where client-proxy routes on the `E2b-Sandbox-Id` and `E2b-Sandbox-Port` headers to `envd` inside the sandbox.

Clients need `E2B_SANDBOX_URL` as well as `E2B_DOMAIN`. With only the domain, the SDK and CLI address each sandbox as `<port>-<sandbox id>.e2b.alphasecunited.com`, and UniFi local DNS has no wildcard records to answer that. For the same reason the SDK's `get_host()` URLs do not resolve here; reach a port with the two headers instead.

## Watching a Desktop sandbox

After `stream.start()` in the Desktop SDK, open `https://desktop.e2b.alphasecunited.com/<sandbox id>/vnc.html?autoconnect=1&resize=scale&path=<sandbox id>/websockify`. NPM host 42 takes the ID from the path and sets the routing headers ([npm-desktop-viewer.conf](Configuration/npm-desktop-viewer.conf)); the SDK's own `stream.get_url()` address does not resolve here. noVNC has no password, so the sandbox ID is the only thing between a LAN or VPN client and the desktop.

## Using it from a machine

The whole setup, for macOS, Linux and Windows, is the skill's [SETUP.md](https://github.com/Duresa7/tools-and-scripts/blob/main/ai-configs/skills/e2b-sandbox/SETUP.md): install the CLI (Node 22.19 or newer), set `E2B_API_KEY`, `E2B_DOMAIN`, `E2B_SANDBOX_URL` and `E2B_DESKTOP_VIEWER_URL` (the values are in [client-env.reference](Configuration/client-env.reference), the key in my password manager), link the skill into `~/.claude/skills` and `~/.agents/skills`, and check with `e2b sandbox create base --detach` and `e2b sandbox kill <id>`.

The machine needs HTTPS to NPM at `192.168.85.2`, which every Internal network and the VPN already have.

## Operations

Commands run as root in `/opt/e2b` on `e2b-01`, through ssh-mcp profile `e2b_01`.

| Task | How |
|---|---|
| Status | `docker compose ps`; `ready` running means the stack is usable |
| Logs | `docker compose logs --tail 100 api orchestrator client-proxy` |
| After a reboot of `e2b-01` or Grey | Start VM 113, then `docker compose up -d --wait`. It recreates the TCP MSS clamp and `/var/run/netns`, which do not survive a reboot. |
| Upgrade | Rerun [setup-embed.sh](Scripts/setup-embed.sh) with the new runtime commit and no secrets file: it downloads both files again, reapplies the dashboard patch, carries the secrets over and runs `up`, which pulls the newly pinned image tags. Then `docker compose up -d --wait --remove-orphans` drops services the new file no longer defines. Running sandboxes end when the orchestrator restarts. |
| Raise capacity | `HUGEPAGES=<n>` in `.env` and `docker compose up -d --wait`; each 512 MiB sandbox takes 256 pages at full memory. On a running host the page cache holds most free memory, so run `sync; echo 3 > /proc/sys/vm/drop_caches; echo 1 > /proc/sys/vm/compact_memory` first. If `host-setup` still cannot reserve them all it exits 1 and Compose leaves the recreated dashboard stopped; lower the number and run `up` again. A larger pool than the free memory allows takes a reboot of `e2b-01`, or more VM memory. |
| Build a template | [build-dev-template.py](Scripts/build-dev-template.py) is the pattern, and [build-upstream-template.py](Scripts/build-upstream-template.py) builds E2B's published ones from a clone. A `copy()` step uploads through port 5008, which needs `ssh -N -L 5008:127.0.0.1:5008 dkadi@192.168.80.30`. Each step gets the team's `disk_mb` (10240) of working space; `min_free_disk_mb` only sets the space left afterwards. Each step restores the previous step's snapshot while the old VM still holds its memory, so a template's memory has to fit in the pool twice. Every step is stored as a layer under `/var/lib/e2b/storage/templates` and again in `/orchestrator/build`, and nothing removes layers of failed or superseded builds: check `df -h /` before building. |
| Remove everything | `docker compose down -v`, `docker compose --profile purge run --rm host-teardown`, destroy VM 113, then remove NPM hosts 39 to 42 and certificate 3, the four UniFi records and the firewall policy |

SSH to `e2b-01` from one host several times within a few minutes trips UniFi's `EMERGING_SCAN` intrusion-prevention signature, and that host's SSH to `e2b-01` is then dropped for several minutes. ssh-mcp holds its connection open and has not tripped it.

## Open Items

- Layer storage: about 140 GB after four templates and their failed attempts. Work out a cleanup that keeps the layers live templates depend on before building more.
- Grey's `local-lvm` thin pool: `e2b-01` may grow to 300 GiB; the pool had 267 GB free on 2026-11-11.
- Sign in to the dashboard in a browser and open a sandbox terminal, the path the HTTPS sandbox URL patch is for.
- Trial review on 2026-11-25. Keeping it brings an Executor MCP app, `onboot=1` with a boot-time `up`, monitoring, and the CLI on the Mac, Windows and Linux machines.

## Records

| Date | Record |
|---|---|
| 2026-11-11 | [Extra Templates and Disk Growth](Documentation/Change%20Records/Extra%20Templates%20and%20Disk%20Growth%20-%202026-11-11.md) |
| 2026-11-11 | [Embed Trial Deployment](Documentation/Change%20Records/Embed%20Trial%20Deployment%20-%202026-11-11.md) |
| 2026-11-11 | [e2b-01 Provisioning](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/e2b-01%20Provisioning%20-%202026-11-11.md) |

## Upstream

- Runtime and Embed: [github.com/e2b-dev/runtime](https://github.com/e2b-dev/runtime), [Embed with Docker Compose](https://github.com/e2b-dev/runtime/blob/main/embed/compose/README.md)
- SDKs and CLI: [github.com/e2b-dev/E2B](https://github.com/e2b-dev/E2B)
