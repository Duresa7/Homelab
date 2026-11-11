# Hermes Agent

**Created:** 2026-11-04  
**Last updated:** 2026-11-07

I run [Hermes Agent](https://github.com/NousResearch/hermes-agent) from Nous Research on `hermes-01` as a personal assistant I can message in Discord. The agent calls itself **Horus**; Hermes is only the software underneath. It talks to me through its own bot user, **Horus AS**, kept separate from the **Anubis AS** alert bot so a fault or token reset here cannot touch alert delivery. It reaches my lab through Executor's `SSH` connection, which gives it ssh-mcp and therefore root or sudo on every host ssh-mcp holds, with no approval prompts.

## Current State

| Item | Value |
|---|---|
| Host | `hermes-01`, VM 112 on `grey-server`, `192.168.80.22` on SERVERS-A. [Provisioning](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/hermes-01%20Provisioning%20-%202026-11-04.md) |
| Version | Hermes Agent v0.22.7 (2026.9.24), `stable` channel, git checkout, Python 3.14.9 |
| Install | The upstream installer, run as `dkadi`: install directory `/home/dkadi/.hermes/hermes-agent`, data and config in `/home/dkadi/.hermes` (mode 0700) |
| Config | `/home/dkadi/.hermes/config.yaml` (mode 0600) |
| Secrets and gates | `/home/dkadi/.hermes/.env` (mode 0600): `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS`, `DISCORD_ALLOWED_CHANNELS`, `DISCORD_HOME_CHANNEL`, and the dashboard's `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`, `_PASSWORD_HASH` and `_SECRET`. Executor's OAuth tokens are in `~/.hermes/mcp-tokens/` (mode 0600) |
| Model | Anthropic API, `claude-opus-5-5` since 2026-11-07 (was `claude-sonnet-5-5` from 2026-11-04, and `claude-sonnet-5` before that), reasoning effort `medium` from the global `agent.reasoning_effort`. The `public` profile stays on `claude-sonnet-5-5`. Backup before the switch: `config.yaml.bak-2026-11-07-opus` |
| Auxiliary models | Background chores in `config.yaml` under `auxiliary`, set 2026-11-07 for cost: `vision`, `background_review` (the memory step after each reply) and `memory_query_rewrite` on `claude-haiku-5-5`; `skills_hub`, `mcp`, `title_generation` and `curator` (the occasional skill clean-up, which reads every skill at once, so Luna's 272K long-prompt threshold beats Haiku's 100K) on `gpt-6-luna` through `OPENAI_API_KEY`; `compression` and `review` stay on `claude-sonnet-5-5`; the other tasks follow the main model. Per million tokens, input/output: Haiku 5.5 and Luna $0.10/$0.50, Sonnet 5.5 $2/$10. Mixture of Agents is configured (advisors `claude-opus-5-5`, `claude-sonnet-5-5`, `gpt-6.1-sol`; aggregator `claude-opus-5-5`) but runs only on `/moa`. Backups before each change: `config.yaml.bak-2026-11-07-aux` and `config.yaml.bak-2026-11-07-aux2`. The `public` profile has no `auxiliary` block, so its chores run on its main model |
| Terminal backend | `local`: commands run as `dkadi` on the host |
| Approvals | `approvals.mode: off`; only Hermes's hardline blocklist still refuses commands |
| MCP | `executor`: `https://executor.alphasecunited.com/mcp?connection=1c3a72d7-0b72-48ea-86f1-3a3a5f1f0788`, `auth: oauth`, `trust: full`, `timeout: 300`, `connect_timeout: 60`, `oauth.redirect_port: 8765`. The Executor connection is `SSH`: the SSH app only, all 15 of its tools, no account. Hermes sees Executor's six MCP tools |
| Services | systemd user units `hermes-gateway.service` and `hermes-dashboard.service`, both enabled with `Restart=always`; linger on for `dkadi` so they start at boot without a login |
| Messaging | Discord only, as `Horus AS#9152`, and only when @mentioned. In `#ai-bot` (`1568709425131290704`, since 2026-11-07; it was `#alert-bots`, `1495962372936826991`) in `Home Base` it answers anyone who can see the channel (the `AI-Access` and `Good Kush` roles), in an auto-created thread, as the chat-only `public` profile. Typing the server code unlocks the full `default` profile for that person in that thread for 15 minutes; a code typed in the channel itself covers all their `#ai-bot` threads (since 2026-11-07; before that only `DISCORD_ALLOWED_USERS` could talk to it there). In `#secret` (`1016933615793356820`, since 2026-11-05) it answers anyone, in the channel with no thread, as the chat-only `public` profile. The `discord-no-dms` plugin turns off the DM intents, so the bot never receives a DM |
| Profiles | `default` has the full setup below and serves `#ai-bot` only through route `ai-bot-server-code`, whose `user_id` is the placeholder `server-code-unlocked`; only the `discord-open-channel` plugin can make it match, for an unlocked sender. `public` (`~/.hermes/profiles/public`) gets `#secret` through route `secret-channel` and `#ai-bot` through route `ai-bot-channel`. It has the same SOUL plus a paragraph on what it cannot do there, the `horus` skin and the locale overlay; `platform_toolsets.discord: [vision]`, no MCP servers, memory off, and an `.env` holding only `ANTHROPIC_API_KEY`. Tracked copies: [profiles/public](Configuration/profiles/public/) |
| Identity | `~/.hermes/SOUL.md` opens with "You are Horus, AlphaSec United's AI agent, called Horus AS in Discord" and tells it never to call itself Hermes, then gives it the voice of Horus of ancient Egypt in English, watching over "the realm of AlphaFly" and calling the servers "the temples of AlphaFly", never "the homelab": a regal, slightly archaic cadence and Egyptian imagery, one or two touches per reply, with commands, hostnames, paths, errors and tool output always written exactly and plainly. Since 2026-11-07 both profiles' `SOUL.md` also tell it to take what people say about themselves at their word and never hedge it with "so he claims" or "unverified"; a claim never changes what it will do. `display.skin: horus` (`~/.hermes/skins/horus.yaml`) labels the CLI and dashboard chat `𓂀 Horus`. A locale overlay, `~/.hermes/locales/en.yaml`, overrides 120 of Hermes's 3,515 English interface strings so gateway notices say Horus and use `𓂀` in place of `☤`, and the shutdown, restart and back-online notices open with `𓂀`; text inside backticks, such as `hermes gateway restart`, is unchanged. The pre-edit SOUL.md is at [Backups/hermes-01-SOUL.md-2026-11-04](../../Backups/hermes-01-SOUL.md-2026-11-04) |
| Standing instructions | `#ai-bot` channel prompt in `config.yaml` under `discord.channel_prompts` (also applies in its threads): act on server requests from allowed users without confirming, and Discord formatting rules. Tracked copy: [channel-prompt-bots.txt](Configuration/channel-prompt-bots.txt) |
| Skill | `homelab-ops` in `~/.hermes/skills/homelab-ops/SKILL.md`: how to use Executor's SSH tools, a map of every ssh-mcp profile to its role, and ssh-mcp's limits. Tracked copy: [SKILL.md](Configuration/skills/homelab-ops/SKILL.md) |
| Memory | Empty; left for what Horus learns |
| Discord display | `display.platforms.discord`: `tool_progress: log` (tool calls go to `~/.hermes/logs/tool_calls.log`, not the chat), `interim_assistant_messages: false`, `show_reasoning: false` |
| Plugins | User plugins in `~/.hermes/plugins/`, both in `plugins.enabled`: `discord-no-dms`, and `discord-open-channel` (since 2026-11-05), which admits every sender in `#secret` and `#ai-bot`, handles the `#ai-bot` server code (`HORUS_SERVER_CODE_HASH` in `.env`, a salted HMAC; the code itself is stored nowhere on the host), keeps slash and typed commands in both channels to `DISCORD_ALLOWED_USERS`, and keeps the shutdown, restart and back-online notices out of `#secret`. Tracked with its test script: [discord-open-channel](Configuration/plugins/discord-open-channel/) |
| Discord toolsets | `discord` (fetch messages, search members, create threads) on; `discord_admin` and `computer_use` off |
| Web search | `web` toolset on in Discord: search and page reading through the `web-perplexity` plugin. There is no `PERPLEXITY_API_KEY`; it uses the Nous Research login in `~/.hermes/auth.json` (provider `nous`, added 2026-11-07), which routes through Nous's managed tool gateway, billed to that Nous account. A test search on 2026-11-07 returned results. Only the main model calls it, not the auxiliary models |
| Dashboard | `http://192.168.80.22:9119`, `hermes dashboard --host 0.0.0.0 --port 9119 --no-open --skip-build`, username/password provider with my standard application account `dkadi`, stored as a scrypt hash. Plain HTTP on the LAN; Internal and VPN zones reach it through `Allow Internal to AlphSec-Servers`. Theme `clear` since 2026-11-07 (was `default-large` with the Inter font override; `dashboard.font` is now `theme`): Atkinson Hyperlegible Next and Mono, sentence case, and it follows the viewing device's light or dark setting; `clear-light` and `clear-dark` pin one mode. The three YAML files live in `~/.hermes/dashboard-themes/` and are generated by [build_themes.py](Configuration/dashboard-themes/build_themes.py), which also checks WCAG AA contrast. Hermes's theme loader drops terminal colors from user themes, so the Chat terminal stays black in light mode |
| API server | Not enabled |

## Decisions

- **Local install as `dkadi`, not the Docker image.** I chose the upstream installer and the local terminal backend. Hermes's shell has `dkadi`'s access on this host. It does not have sudo without root's password, and the host has no standing network path into the Internal zone.
- **A bot of its own.** Anubis AS's token would have worked, but sharing it would let a leak here post as the alert bot, tie a rotation here to `monitor-01`, and share one rate limit with alerting.
- **Private bot.** Public Bot is off, so only my AlphaSec United developer team can add Horus AS to a server. Discord refuses a private bot while the Installation tab has a default install link, so the Install Link is `None`.
- **Full lab access without prompts.** I gave Hermes the Executor `SSH` connection with `trust: full` and turned Hermes's approvals off, so a message in `#ai-bot` from anyone who has typed the server code can run any command on any ssh-mcp host, including root on the five Proxmox nodes, without a confirmation step. ssh-mcp's own deny list (`reboot`, `shutdown`, writes to cron, systemd and `authorized_keys`) still applies. The Executor connection uses OAuth because a personal access token would ignore the connection's scope.
- **Dashboard on the LAN, not behind NPM.** It listens on all interfaces with a password gate. Hermes's docs limit the username/password provider to a trusted network or VPN; it carries no TLS, MFA or per-user accounts.
- **`#secret` is open, but only to a chat-only Horus.** Hermes has one user allowlist for the whole bot, and opening it would give anyone in `Home Base` root on every ssh-mcp host through `#ai-bot`. So the `discord-open-channel` plugin adds a per-channel exception at both of Hermes's sender checks, and `profile_routes` hands `#secret` to the `public` profile, which has no terminal, files, MCP or Discord fetch tool. Every patch fails closed: if Hermes changes underneath it, `#secret` goes quiet for outsiders and `#ai-bot` is untouched. [Change record](Documentation/Change%20Records/Open%20Secret%20Channel%20-%202026-11-05.md)
- **`#ai-bot` is open, and server work takes a code that Horus never sees.** Anyone who can see `#ai-bot` talks to the chat-only Horus. The plugin checks every message against a salted hash of the server code in the Discord adapter, before Hermes batches, routes or records it; a match is deleted, answered with "Password accepted. Unlocked for 15 minutes.", and unlocks the full profile for that person and thread. Asking the model to check a password was rejected, because a model that knows the code can be talked into revealing it or skipping the check. A `pre_gateway_dispatch` hook cannot do the check: the multiplexing gateway routes a message first and runs that hook with the routed profile's plugins, and `public` has none. The plugin admits an outsider only when the routes send them to a profile other than `default` or through the unlock route, so a missing route shuts the channel instead of opening it. [Change record](Documentation/Change%20Records/Server%20Code%20for%20ai-bot%20-%202026-11-07.md)
- **Message Content is the only privileged intent.** Presence and Server Members stay off.
- **No DMs, one channel.** Hermes's Discord adapter always admits a DM from an allowlisted user and does not read `dm_policy`, so the `discord-no-dms` plugin clears the `dm_messages`, `dm_reactions` and `dm_typing` intents on the bot before it connects, and Discord never delivers a DM to it. As a backstop, its `pre_gateway_dispatch` hook drops every Discord event whose chat type is not a server channel or thread (`group`, `thread` or `channel`) before authorization. `DISCORD_ALLOWED_CHANNELS` limits server traffic to `#ai-bot` and `#secret`, and `DISCORD_HOME_CHANNEL` sends cron and notice output there rather than to a DM. Hermes has no agent-callable send-message tool, and with `discord_admin` off its Discord tool can only fetch messages, search members and create threads. The terminal can still read the bot token from `.env`, so a command run through the agent could call the Discord API directly; the gates cover the agent's own channels, not a determined shell.

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
- **No automatic session end.** A Discord thread stays one session until someone sends `/new` or `/reset`; Hermes core no longer reads `session_reset`. Each @mention in `#ai-bot` opens a new thread and so a new session, which limits the effect. The catalog plugin `hermes-session-reset-policy` (community tier, v0.3.0, commit `0f2ea5a`) would add idle or daily resets through a `pre_gateway_dispatch` hook; I would read its source before enabling it. Under the multiplexing gateway that hook runs only for messages routed to a profile that has the plugin, so it would not reset `public` sessions unless installed there too.
- **Open channels after updates and at cost.** The `discord-open-channel` plugin patches Hermes internals, so after each `hermes update` I run its test script and check `agent.log` for `opened Discord channel(s)` and `server code unlocks route`. Anyone who can see `#secret` or `#ai-bot` can spend Anthropic credit there, with no rate limit, and nothing limits guesses at the server code.
- **Slash commands in a DM.** Interactions do not depend on gateway intents, so a slash command sent in a DM may still reach Hermes. The plugin's hook drops it, but Discord would show the command as failed.

## Records

- [Configuration](Configuration/): tracked copies of `SOUL.md`, the `#ai-bot` prompt, the `homelab-ops` skill, the `horus` skin, the locale overlay and the `discord-no-dms` plugin, as deployed on 2026-11-04; the `discord-open-channel` plugin and the `public` profile's `config.yaml` and `SOUL.md`, as deployed on 2026-11-05; the `clear` dashboard themes and their generator, as deployed on 2026-11-07

- [UniFi policy `Allow hermes-01 to NPM HTTPS`](../../Infrastructure/Network/UniFi/Configuration/firewall.md)

- [Install and Discord gateway - 2026-11-04](Documentation/Change%20Records/Install%20and%20Discord%20Gateway%20-%202026-11-04.md)
- [Open the #secret channel - 2026-11-05](Documentation/Change%20Records/Open%20Secret%20Channel%20-%202026-11-05.md)
- [Move to #ai-bot - 2026-11-07](Documentation/Change%20Records/Move%20to%20ai-bot%20Channel%20-%202026-11-07.md)
- [Server code for #ai-bot - 2026-11-07](Documentation/Change%20Records/Server%20Code%20for%20ai-bot%20-%202026-11-07.md)
- [Identity claims at face value - 2026-11-07](Documentation/Change%20Records/Identity%20Claims%20at%20Face%20Value%20-%202026-11-07.md)
- [hermes-01 provisioning - 2026-11-04](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/hermes-01%20Provisioning%20-%202026-11-04.md)

## Upstream

- [Repository](https://github.com/NousResearch/hermes-agent)
- [Documentation](https://hermes-agent.nousresearch.com/docs)
