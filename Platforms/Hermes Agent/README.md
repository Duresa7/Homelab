# Hermes Agent

**Created:** 2026-11-04  
**Last updated:** 2026-11-05

I run [Hermes Agent](https://github.com/NousResearch/hermes-agent) from Nous Research on `hermes-01` as a personal assistant I can message in Discord. The agent calls itself **Horus**; Hermes is only the software underneath. It talks to me through its own bot user, **Horus AS**, kept separate from the **Anubis AS** alert bot so a fault or token reset here cannot touch alert delivery. It reaches my lab through Executor's `SSH` connection, which gives it ssh-mcp and therefore root or sudo on every host ssh-mcp holds, with no approval prompts.

## Current State

| Item | Value |
|---|---|
| Host | `hermes-01`, VM 112 on `grey-server`, `192.168.80.22` on SERVERS-A. [Provisioning](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/hermes-01%20Provisioning%20-%202026-11-04.md) |
| Version | Hermes Agent v0.22.7 (2026.9.24), `stable` channel, git checkout, Python 3.14.9 |
| Install | The upstream installer, run as `dkadi`: install directory `/home/dkadi/.hermes/hermes-agent`, data and config in `/home/dkadi/.hermes` (mode 0700) |
| Config | `/home/dkadi/.hermes/config.yaml` (mode 0600) |
| Secrets and gates | `/home/dkadi/.hermes/.env` (mode 0600): `ANTHROPIC_API_KEY`, `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS`, `DISCORD_ALLOWED_CHANNELS`, `DISCORD_HOME_CHANNEL`, and the dashboard's `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`, `_PASSWORD_HASH` and `_SECRET`. Executor's OAuth tokens are in `~/.hermes/mcp-tokens/` (mode 0600) |
| Model | Anthropic API, `claude-sonnet-5-5` since 2026-11-04 (was `claude-sonnet-5`), reasoning effort `medium` |
| Terminal backend | `local`: commands run as `dkadi` on the host |
| Approvals | `approvals.mode: off`; only Hermes's hardline blocklist still refuses commands |
| MCP | `executor`: `https://executor.alphasecunited.com/mcp?connection=1c3a72d7-0b72-48ea-86f1-3a3a5f1f0788`, `auth: oauth`, `trust: full`, `timeout: 300`, `connect_timeout: 60`, `oauth.redirect_port: 8765`. The Executor connection is `SSH`: the SSH app only, all 15 of its tools, no account. Hermes sees Executor's six MCP tools |
| Services | systemd user units `hermes-gateway.service` and `hermes-dashboard.service`, both enabled with `Restart=always`; linger on for `dkadi` so they start at boot without a login |
| Messaging | Discord only, as `Horus AS#9152`. It answers only in `#bots` (`1495962372936826991`) in `Home Base`, only to users in `DISCORD_ALLOWED_USERS` (my account and `MB-user`, since 2026-11-04), and only when @mentioned, in an auto-created thread. Every DM is dropped by the `discord-no-dms` plugin |
| Identity | `~/.hermes/SOUL.md` opens with "You are Horus, AlphaSec United's AI agent, called Horus AS in Discord" and tells it never to call itself Hermes, then gives it the voice of Horus of ancient Egypt in English, watching over "the realm of AlphaFly" and calling the servers "the temples of AlphaFly", never "the homelab": a regal, slightly archaic cadence and Egyptian imagery, one or two touches per reply, with commands, hostnames, paths, errors and tool output always written exactly and plainly. `display.skin: horus` (`~/.hermes/skins/horus.yaml`) labels the CLI and dashboard chat `𓂀 Horus`. A locale overlay, `~/.hermes/locales/en.yaml`, overrides 120 of Hermes's 3,515 English interface strings so gateway notices say Horus and use `𓂀` in place of `☤`, and the shutdown, restart and back-online notices open with `𓂀`; text inside backticks, such as `hermes gateway restart`, is unchanged. The pre-edit SOUL.md is at [Backups/hermes-01-SOUL.md-2026-11-04](../../Backups/hermes-01-SOUL.md-2026-11-04) |
| Standing instructions | `#bots` channel prompt in `config.yaml` under `discord.channel_prompts` (also applies in its threads): act on server requests from allowed users without confirming, and Discord formatting rules. Tracked copy: [channel-prompt-bots.txt](Configuration/channel-prompt-bots.txt) |
| Skill | `homelab-ops` in `~/.hermes/skills/homelab-ops/SKILL.md`: how to use Executor's SSH tools, a map of every ssh-mcp profile to its role, and ssh-mcp's limits. Tracked copy: [SKILL.md](Configuration/skills/homelab-ops/SKILL.md) |
| Memory | Empty; left for what Horus learns |
| Discord display | `display.platforms.discord`: `tool_progress: log` (tool calls go to `~/.hermes/logs/tool_calls.log`, not the chat), `interim_assistant_messages: false`, `show_reasoning: false` |
| Plugins | `discord-no-dms` (user plugin, `~/.hermes/plugins/discord-no-dms/`, in `plugins.enabled`) |
| Discord toolsets | `discord` (fetch messages, search members, create threads) on; `discord_admin` and `computer_use` off |
| Dashboard | `http://192.168.80.22:9119`, `hermes dashboard --host 0.0.0.0 --port 9119 --no-open --skip-build`, username/password provider with my standard application account `dkadi`, stored as a scrypt hash. Plain HTTP on the LAN; Internal and VPN zones reach it through `Allow Internal to AlphSec-Servers` |
| API server | Not enabled |

## Decisions

- **Local install as `dkadi`, not the Docker image.** I chose the upstream installer and the local terminal backend. Hermes's shell has `dkadi`'s access on this host. It does not have sudo without root's password, and the host has no standing network path into the Internal zone.
- **A bot of its own.** Anubis AS's token would have worked, but sharing it would let a leak here post as the alert bot, tie a rotation here to `monitor-01`, and share one rate limit with alerting.
- **Private bot.** Public Bot is off, so only my AlphaSec United developer team can add Horus AS to a server. Discord refuses a private bot while the Installation tab has a default install link, so the Install Link is `None`.
- **Full lab access without prompts.** I gave Hermes the Executor `SSH` connection with `trust: full` and turned Hermes's approvals off, so a message from me or `MB-user` in `#bots` can run any command on any ssh-mcp host, including root on the five Proxmox nodes, without a confirmation step. ssh-mcp's own deny list (`reboot`, `shutdown`, writes to cron, systemd and `authorized_keys`) still applies. The Executor connection uses OAuth because a personal access token would ignore the connection's scope.
- **Dashboard on the LAN, not behind NPM.** It listens on all interfaces with a password gate. Hermes's docs limit the username/password provider to a trusted network or VPN; it carries no TLS, MFA or per-user accounts.
- **Message Content is the only privileged intent.** Presence and Server Members stay off.
- **No DMs, one channel.** Hermes's Discord adapter always admits a DM from an allowlisted user and does not read `dm_policy`, so a `pre_gateway_dispatch` hook drops every Discord event whose chat type is not a server channel or thread (`group`, `thread` or `channel`) before authorization. `DISCORD_ALLOWED_CHANNELS` limits server traffic to `#bots`, and `DISCORD_HOME_CHANNEL` sends cron and notice output there rather than to a DM. Hermes has no agent-callable send-message tool, and with `discord_admin` off its Discord tool can only fetch messages, search members and create threads. The terminal can still read the bot token from `.env`, so a command run through the agent could call the Discord API directly; the gates cover the agent's own channels, not a determined shell.

## Discord Bot

| Setting | Value |
|---|---|
| Application | `Horus AS`, owned by the `AlphaSec United` developer team |
| Public Bot | off |
| Privileged intents | Message Content on; Presence and Server Members off |
| Install Link | None; User Install and Guild Install contexts both still ticked |
| Server | `Home Base`, invited with View Channels, Send Messages, Send Messages in Threads, Create Public Threads, Embed Links, Attach Files, Read Message History and Add Reactions |
| Token | My password manager item `Discord Bot - Horus AS`, field `credential` |

## Operations

- Status and logs: `systemctl --user status hermes-gateway` and `journalctl --user -u hermes-gateway -f` as `dkadi`, or `~/.hermes/logs/gateway.log`.
- Rotate the bot token: reset it in the Developer Portal, update the password manager item, replace `DISCORD_BOT_TOKEN` in `.env` without putting the value in a command, then `systemctl --user restart hermes-gateway`.
- Update: `hermes update`, which tracks the stable channel, then `hermes gateway restart`.

## Open Items

- **Dashboard over HTTPS.** An NPM proxy host and a UniFi DNS name would put TLS in front of the login.
- **Tools that cannot work here.** Computer Use failed setup on a missing `libXi.so.6` and has no desktop to drive. Browser Automation downloaded Chromium, which still needs its system libraries.
- **Not monitored.** No node_exporter target, no blackbox probe of the gateway, and no Wazuh agent.
- **No automatic session end.** A Discord thread stays one session until someone sends `/new` or `/reset`; Hermes core no longer reads `session_reset`. Each @mention in `#bots` opens a new thread and so a new session, which limits the effect. The catalog plugin `hermes-session-reset-policy` (community tier, v0.3.0, commit `0f2ea5a`) would add idle or daily resets through a `pre_gateway_dispatch` hook; I would read its source before enabling it.
- **DM drop not yet seen.** The `discord-no-dms` plugin has not logged a dropped DM, because none has been sent.

## Records

- [Configuration](Configuration/): tracked copies of `SOUL.md`, the `#bots` prompt, the `homelab-ops` skill, the `horus` skin, the locale overlay and the `discord-no-dms` plugin, as deployed on 2026-11-04

- [UniFi policy `Allow hermes-01 to NPM HTTPS`](../../Infrastructure/Network/UniFi/Configuration/firewall.md)

- [Install and Discord gateway - 2026-11-04](Documentation/Change%20Records/Install%20and%20Discord%20Gateway%20-%202026-11-04.md)
- [hermes-01 provisioning - 2026-11-04](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/hermes-01%20Provisioning%20-%202026-11-04.md)

## Upstream

- [Repository](https://github.com/NousResearch/hermes-agent)
- [Documentation](https://hermes-agent.nousresearch.com/docs)
