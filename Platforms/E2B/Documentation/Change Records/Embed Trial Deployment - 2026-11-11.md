# Embed Trial Deployment

**Created:** 2026-11-11  
**Last updated:** 2026-11-11

**Implementation date:** 2026-11-11, 7:50 PM to 8:55 PM Eastern  
**Status:** Complete, on trial until the 2026-11-25 review.  
**Affected systems:** `e2b-01` (VM 113 on `grey-server`), Nginx Proxy Manager on `docker-network`, UniFi local DNS and firewall policies, `ubuntu-dev`

I deployed E2B Embed 0.30.0 on `e2b-01` so agents on my machines can run code in throwaway Firecracker sandboxes on Grey instead of on the machine they run on. The host build is in [e2b-01 Provisioning](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/e2b-01%20Provisioning%20-%202026-11-11.md).

## Decisions

- **Embed, the single-machine package.** `e2b-dev/E2B` holds only the SDKs and CLI. The server is `e2b-dev/runtime` (renamed from `e2b-dev/infra`), and its `embed/compose` package runs the whole stack on one Linux host with KVM: API, dashboard, client-proxy, a Firecracker orchestrator, Postgres, Redis and ClickHouse. No account and no license key.
- **Newest releases.** Embed 0.30.0 (released 2026-11-06), installed from `e2b-dev/runtime` commit `df41cd32cb7f3838d71625f04ce1e015e12ed046`, the `main` head on 2026-11-11, whose `embed/compose` files match the last commit to touch them (`a958dfe4be`, 2026-11-10). Docker Engine 29.9.3 and Compose 5.7.1 from Docker's `resolute` repository. Clients use `@e2b/cli` 2.23.0 and the `e2b` SDK 2.63.0. Embed's README still says it was tested with SDK 2.46, but its own Node smoke test moved to `e2b` 2.62.0 on 2026-11-10.
- **HTTPS through NPM, LAN and VPN only.** Embed answers plain HTTP and binds twelve ports on every interface, and port 5008 is an unauthenticated control API that creates and kills sandboxes. NPM terminates TLS for the three client ports. Nothing is published to the WAN or to Cloudflare.
- **CLI first.** Agents on `ubuntu-dev` drive sandboxes with the `e2b` CLI and a skill. An Executor MCP app comes only if the trial is kept; E2B archived its own standalone MCP server in April 2026.
- **Templates.** `base`, which Embed builds on first start, and `dev` for everyday work.

## 1. Network edge

| Change | Result |
|---|---|
| NPM certificate 3 | Let's Encrypt DNS-01 for `*.e2b.alphasecunited.com` and `e2b.alphasecunited.com`, Cloudflare provider, ECDSA, 60-second propagation, the same zone-scoped token certificate 1 uses. Issued, expires 2027-02-09 11:51 PM UTC. The first request was refused with `data/meta must NOT have additional properties` until I dropped `letsencrypt_agree` from the meta. |
| NPM proxy hosts | 39 `e2b.alphasecunited.com` to `192.168.80.30:3001`, 40 `api.e2b.alphasecunited.com` to `:3000`, 41 `sandbox.e2b.alphasecunited.com` to `:3002`. Certificate 3, Force SSL, HTTP/2, Block Common Exploits, WebSocket support, HSTS off. Advanced configuration: `proxy_buffering off`, `proxy_cache off`, `proxy_request_buffering off`, 3,600-second proxy read, proxy send and send timeouts, `client_max_body_size 1024m`. |
| UniFi local DNS | `e2b.alphasecunited.com` (`fa4e90f0-8ec5-4ab1-89af-7428e900102a`), `api.e2b.alphasecunited.com` (`0f41c33c-c3da-4416-80f0-974d524a74c1`) and `sandbox.e2b.alphasecunited.com` (`7e423abc-2a58-4e08-bff5-18674fe56a32`), A records to `192.168.85.2`. |
| UniFi policy | `Allow NPM to e2b-01 E2B` (`c194c04e-12f3-41b5-98fe-723ab776d682`): TCP IPv4 from `192.168.85.2` in `AlphaSec-Access` to `192.168.80.30` ports `3000-3002` in `AlphaSec-Servers`, logging on, index 10001. |

## 2. Port guard on the VM

Every Internal network already reaches SERVERS-A on every port, so the VM filters its own ports. [e2b-guard.nft](../../Configuration/e2b-guard.nft) is one table, `inet e2b_guard`, loaded by [e2b-nft-guard.service](../../Configuration/e2b-nft-guard.service). On `ens18` it accepts 3000 to 3002 from `192.168.85.2` only and drops 3000 to 3002 from anywhere else and 3003, 5007 to 5010, 5016 to 5018, 5109, 6060 and 6061 from everywhere. It matches the LAN interface only, because sandboxes reach the orchestrator's egress proxies over their own veth interfaces. The table never flushes the ruleset, and Ubuntu's `nftables.service` stays disabled because its configuration and stop action flush everything, including Docker's rules. Ansible wrote the unit, since ssh-mcp refuses writes under `/etc/systemd`. `systemctl` reads `active` and `enabled`, and `nft list tables` shows `e2b_guard` beside Docker's four tables.

## 3. Docker and Embed

[install-docker.sh](../../Scripts/install-docker.sh) installed Docker Engine 29.9.3 and Compose 5.7.1 and added `ai-agent` to the `docker` group.

I generated the team API key (`e2b_` and 40 hex characters), `ADMIN_TOKEN` and `SANDBOX_ACCESS_TOKEN_HASH_SEED` (64 hex characters each) on `ubuntu-dev`, stored all three in one new password-manager item, and streamed them to `e2b-01` as a `0600` file. The SHA-256 of each value read back from the password manager matched the generated value, and the staged file's digest on the host matched the local one.

[setup-embed.sh](../../Scripts/setup-embed.sh) laid out `/opt/e2b` (`0750`), downloaded `compose.yaml` and `.env` at the pinned commit, applied the dashboard patch (now [compose-dashboard.patch](../../Configuration/compose-dashboard.patch), which since the [later change](Extra%20Templates%20and%20Disk%20Growth%20-%202026-11-11.md) also sets the cookie line), appended [the secrets and the OpenTelemetry collector](../../Configuration/env.additions), shredded the staged file and started `docker compose up -d --wait` detached. It printed `compose config ok` and `patched: 1`.

The patch changes one line. The dashboard's terminal and file browser send sandbox traffic from the browser to `PUBLIC_SANDBOX_URL`, which Embed sets to `http://<host>:3002`; an HTTPS dashboard page would block that as mixed content. The running container reads `PUBLIC_SANDBOX_URL=https://sandbox.e2b.alphasecunited.com`.

Four minutes later every one-shot (`preflight`, `api-secrets`, `host-setup`, `fetch-artifacts`, `db-migrator`, `clickhouse-migrator`, `seed`, `base-template`) had exited 0. `api`, `client-proxy`, `dashboard`, `orchestrator`, `postgres`, `redis`, `clickhouse` and `vector` were healthy, and `ready` and `otel-collector` were up. Images: `api`, `client-proxy`, `db-migrator`, `clickhouse-migrator`, `tools`, `node-e2b` and `seed` at `v0.30.0`, `dashboard:v0.5.1`, `postgres:18.6-alpine`, `redis:7.4.6`, `clickhouse-server:25.8.30.16`, `vector:0.51.1-alpine`, `opentelemetry-collector-contrib:0.163.2`. The orchestrator container is privileged on the host network.

Host state read back afterwards:

| Check | Result |
|---|---|
| Listeners on every interface | 3000, 3001, 3002, 3003, 5007, 5008, 5009, 5010, 5016, 5017, 5018, 5109, plus SSH |
| Loopback only | 5432, 6379, 8123, 9000, 4317, 13133, 30006, 6060, 6061 |
| Hugepages | 2048 total, 2048 free |
| NBD devices | 64 |
| TCP MSS clamp | one `TCPMSS` rule in mangle `FORWARD` |
| Memory, disk | 9.7 GiB available of 15; root 15 GiB used, 94 GiB free |
| From `ubuntu-dev` directly | TCP 3000, 3002 and 5008 to `192.168.80.30` time out |

## 4. Verification through NPM

From `ubuntu-dev`, `https://api.e2b.alphasecunited.com/health` answered `200`, `https://e2b.alphasecunited.com/` `200` and its `http://` form `301`. The presented certificate is `CN=*.e2b.alphasecunited.com`, valid to 2027-02-09.

A Python script on SDK 2.63.0 with `E2B_DOMAIN=e2b.alphasecunited.com` created a sandbox, but its first command failed: the SDK addressed `https://49983-<sandbox id>.e2b.alphasecunited.com/process.Process/Start` and DNS had no record for it. With only `E2B_DOMAIN` set, the SDK routes sandbox traffic by hostname, one name per port and sandbox, and UniFi local DNS has no wildcard records. Setting `E2B_SANDBOX_URL=https://sandbox.e2b.alphasecunited.com` as well, which is how Embed's own `sdk.env` works, switches to header routing through the one `sandbox.e2b` host. The SDK marks that variable deprecated. I killed the sandbox the failed run left behind and reran:

| Step | Result |
|---|---|
| Create from `base` | 0.12 seconds |
| `echo`, `uname -r`, `nproc`, `free -m` | exit 0; guest kernel `6.1.177`, 2 CPUs, 473 MiB |
| Write a file, run it with Python | exit 0, `499999500000` |
| `http.server` on 8080 inside, fetched through `sandbox.e2b` with `E2b-Sandbox-Id` and `E2b-Sandbox-Port` headers | `200 port-ok` |
| `curl https://pypi.org/simple/` inside | `200` |
| `curl http://192.168.40.35:11434/` inside | timed out, exit 28 |
| A 70-second command printing every 10 seconds | exit 0, 7 of 7 lines, past nginx's default 60-second read timeout |
| Kill | done, `e2b sandbox list` empty |

## 5. `dev` template

[build-dev-template.py](../../Scripts/build-dev-template.py) built `dev` from `python:3.12` with `build-essential`, `git`, `curl`, `jq`, `unzip`, Node 22 from NodeSource, `gh` from GitHub's apt repository and `uv`, at 2 vCPU and 1 GiB. The build took 1 minute 2 seconds and produced template `jvylpmrv69ldm22c3kbp`. Its last step printed Python 3.12.16, Node v22.23.5, npm 10.9.9, git 2.47.3, gh 2.103.3, uv 0.13.7 and gcc 14.2.0.

## 6. Client on ubuntu-dev

- `npm i -g @e2b/cli@2.23.0` under nvm's Node 24.19.0; `e2b --version` prints `2.23.0`.
- [`~/.config/e2b/env`](../../Configuration/client-env.reference), `0600`, sets `E2B_DOMAIN`, `E2B_SANDBOX_URL` and `E2B_API_KEY`. Line 2 of `~/.bashrc` sources it, above the early return for non-interactive shells, so agent shells see it.
- The [e2b-sandbox skill](../../Configuration/skills/e2b-sandbox/SKILL.md) lives at `~/.agents/skills/e2b-sandbox`, which Codex reads, with a `~/.claude/skills/e2b-sandbox` symlink for Claude Code.

CLI checks: `e2b sandbox create dev --detach` returned the ID in 0.35 seconds. A directory went in through `tar czf - | e2b sandbox exec <id> 'tar xzf - -C /home/user'`, and `uv run --with pytest pytest -q` inside reported `1 passed`. Piped stdin reached `python3`, `exit 3` came back as the CLI's exit code 3, `sudo -n true` succeeded inside, and the default lifetime is 300 seconds. On `base` (Debian 12, Python 3.11.6), a file written before `e2b sandbox pause` was still there after `resume`; the pause took under a second and the resume about one.

## Left open

- **Dashboard in a browser.** I have not signed in to `https://e2b.alphasecunited.com` with the team key and opened a sandbox terminal, which is the path the patch exists for. The container reads the HTTPS sandbox URL. `DASHBOARD_COOKIE_SECURE` is still `false` as Embed ships it, although the dashboard is now served over HTTPS.
- **Trial review on 2026-11-25.** Keep it if agents used sandboxes for real work most weeks. Keeping it means an Executor MCP app, `onboot=1` with a boot-time `docker compose up -d --wait` (the MSS clamp and `/var/run/netns` do not survive a reboot), monitoring and alerting. Otherwise: `docker compose down -v`, `docker compose --profile purge run --rm host-teardown`, destroy VM 113, remove the NPM hosts, certificate, DNS records and firewall policy, and archive this platform.
- **Other machines.** The CLI and env file are on `ubuntu-dev` only. The Mac, Windows and Linux machines get them, or the Executor app, if the trial is kept.
- **Gateway IPS and SSH.** Repeated SSH connections to `e2b-01` within a few minutes trip UniFi's `EMERGING_SCAN` signature for the source host. See section 4 of the provisioning record.
