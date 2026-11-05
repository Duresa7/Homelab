# Install and Discord Gateway

**Created:** 2026-11-04  
**Last updated:** 2026-11-05

**Implementation date:** 2026-11-04, about 9:00 PM to 11:15 PM Eastern  
**Status:** Complete.  
**Affected systems:** `hermes-01`, the Discord Developer Portal (new application `Horus AS`), the `Home Base` Discord server, my password manager

I installed Hermes Agent on `hermes-01` and connected it to Discord through a new bot user, Horus AS.

## 1. Install

I ran the upstream installer and `hermes setup` as `dkadi`. The setup chose the Anthropic API with my API key, model `claude-sonnet-5`, reasoning effort `medium`, and kept the `local` terminal backend. I left the Discord token blank during setup. The optional `anthropic` feature installed. Afterwards, read on the host:

- `hermes --version`: `Hermes Agent v0.22.7 (2026.9.24) · stable`, install method `git`, Python 3.14.9, `Up to date`.
- `~/.hermes` mode 0700, `.env` and `config.yaml` mode 0600, 3.0 GiB on disk.
- `hermes-gateway.service` was a running, enabled systemd user unit. `loginctl` reported `Linger=no`, so it would not have started at boot.

Two tools failed during setup. Computer Use's `cua-driver --version` exited 127 on a missing `libXi.so.6`. Chromium downloaded to `~/.hermes/tools/chromium-1208`, but Playwright reported it needs system libraries that are not installed.

## 2. Discord application

In the Developer Portal, under my `AlphaSec United` team:

1. I created the application `Horus AS`.
2. On the Bot page I turned on the Message Content intent. Turning off Public Bot in the same save failed with `Private application cannot have a default authorization link`, so I saved the intent first.
3. On the Installation page I changed Install Link from `Discord Provided Link` to `None` and saved.
4. Back on the Bot page I turned off Public Bot and saved, with no validation error.
5. I reset the token, which asked for multi-factor authentication, and stored it in my password manager as `Discord Bot - Horus AS`.

From my workstation, with the token read out of the password manager into memory, the Discord API returned:

- `/users/@me`: `Horus AS`, a bot user.
- `/oauth2/applications/@me`: `bot_public` false, flags `524288` (the limited Message Content intent), team `AlphaSec United` with one member, my account, as admin.

I invited the bot with a link that fixed the server to `Home Base` and requested permissions `309237763136`: View Channels, Send Messages, Send Messages in Threads, Create Public Threads, Embed Links, Attach Files, Read Message History and Add Reactions. Chrome asked to let `discord.com` access other apps on the device, and I blocked it. After I authorized, `/users/@me/guilds` for the bot listed `Home Base`.

## 3. Gateway configuration

I wrote `DISCORD_BOT_TOKEN` and `DISCORD_ALLOWED_USERS`, set to my own Discord user ID, into `~/.hermes/.env`. The values went from the password manager into a mode-0600 staging file, were copied to the host and merged by a script that rewrote `.env` at mode 0600. Both staging copies were shredded. Neither value appeared in a command. Before copying, I pinned `hermes-01`'s ED25519 host key on my workstation after matching it against the host's own key file through the guest agent.

Then:

- `loginctl enable-linger dkadi` returned `Linger=yes`.
- `systemctl --user restart hermes-gateway.service`, and the unit read `active`.

The gateway log after the restart:

```text
2026-11-04 22:08:55,520 INFO gateway.run: Connecting to discord...
2026-11-04 22:08:55,543 WARNING plugins.platforms.discord.adapter_opus: Opus codec not found — voice channel playback disabled
2026-11-04 22:08:55,880 INFO hermes_plugins.platforms__discord.adapter: [Discord] Registered /skill command with 39 skill(s) via autocomplete
2026-11-04 22:08:58,514 INFO hermes_plugins.platforms__discord.adapter: [Discord] Connected as Horus AS#9152
2026-11-04 22:08:58,523 INFO gateway.run: ✓ discord connected
2026-11-04 22:08:58,574 INFO gateway.run: Gateway running with 1 platform(s)
```

I opened a direct-message channel from the bot to my account and posted one message, which Discord accepted with a message ID.

## 4. Channel and DM restrictions

At about 10:12 PM I limited Horus AS to `#bots` in `Home Base` and turned off DMs in both directions:

- `.env`: `DISCORD_ALLOWED_CHANNELS` and `DISCORD_HOME_CHANNEL` set to `#bots`, `1495962372936826991`, read from the guild's channel list through the API.
- Plugin `discord-no-dms` in `~/.hermes/plugins/`, a `pre_gateway_dispatch` hook returning `skip` for any Discord event with chat type `dm`. I needed it because the adapter's `_is_allowed_user` admits an allowlisted user's DM before any channel gate, and the channel gate itself is skipped for `DMChannel`. `hermes plugins enable discord-no-dms` added it to `plugins.enabled`.
- `hermes tools disable --platform discord discord_admin` and `computer_use`: `✓ Disabled` for both.

After `systemctl --user restart hermes-gateway.service` the unit was `active`, the log showed `[Discord] Connected as Horus AS#9152` at 22:12:23, `hermes plugins list` showed `discord-no-dms` `enabled`, and `hermes tools list --platform discord` showed `discord` on and `discord_admin` and `computer_use` off.

## 5. Second approved user

At 10:24 PM I added `MB-user`, a `Home Base` member found through the guild member search, to `DISCORD_ALLOWED_USERS`, beside my own ID. After the restart the unit was `active` and the log showed `[Discord] Connected as Horus AS#9152` at 22:24:43. The DM plugin and the `#bots` channel gate apply to this user exactly as to me.

## 6. Executor MCP

I connected Hermes to Executor's connection `1c3a72d7-0b72-48ea-86f1-3a3a5f1f0788`. Executor's dashboard names it `SSH`, turns on one app, SSH, with `All tools` and `No account needed`, and leaves Book Digest, Cloudflare, Docker Hub, Executor, OpenUI Cloud, Sure, UniFi, VirusTotal and Wazuh off. The SSH app exposes 15 tools, from `run-command` and `privileged-command` to the SFTP tools.

1. HTTPS from `hermes-01` to `executor.alphasecunited.com` (NPM, `192.168.85.2`) timed out. I created the UniFi policy `Allow hermes-01 to NPM HTTPS`, after which `/mcp?connection=…` returned `HTTP/2 401` with `tls_verify=0` and a `www-authenticate` header pointing at the connection's protected-resource metadata.
2. `hermes config set` wrote `mcp_servers.executor` with the connection URL, `auth: oauth`, `trust: full`, `timeout: 300`, `connect_timeout: 60` and `oauth.redirect_port: 8765`, and `approvals.mode: off`.
3. For the OAuth sign-in I forwarded port 8765 from my workstation to `127.0.0.1:8765` on `hermes-01`, ran `hermes mcp login executor --flow browser` there, opened its authorize URL in my workstation's browser, and approved Executor's consent page ("Hermes Agent wants to connect", one connection, access sent to `http://127.0.0.1:8765`). Hermes printed `✓ Authenticated — 6 tool(s) available` and wrote three mode-0600 files to `~/.hermes/mcp-tokens/`. I closed the tunnel.
4. `hermes mcp test executor`: `✓ Connected (519ms)`, `✓ Tools discovered: 6` (`skills`, `search`, `describe`, `call`, `execute`, `resume`).
5. After a gateway restart at 10:40 PM the log showed `MCP server 'executor' (HTTP): registered 6 tool(s)`.

## 7. Web dashboard

I added a systemd user unit, `~/.config/systemd/user/hermes-dashboard.service`, running `hermes dashboard --host 0.0.0.0 --port 9119 --no-open --skip-build` with `Restart=always` and `RestartPreventExitStatus=78`. The login is my standard application account. I computed the scrypt hash on my workstation, in the format `plugins.dashboard_auth.basic.hash_password` produces, and wrote only `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`, `_PASSWORD_HASH` and a random `_SECRET` into `.env`, so the password never reached the host.

My first attempt imported Hermes's hash function from the bundled Python and failed on `ModuleNotFoundError: No module named 'httpx'`. With no provider configured the dashboard exited 1 and told me a public bind needs one; I stopped the unit until the hash was in place.

From my workstation on another VLAN:

| Request | Result |
|---|---|
| `GET /api/config`, `/api/env`, `/api/sessions`, `/api/keys`, `/api/logs`, `/api/auth/me` without a session | `401` each |
| `GET /api/status` without a session | `200`, version and gateway state only |
| `POST /auth/password-login`, wrong password | `401` |
| `POST /auth/password-login`, right password | `200`, `{"ok":true,"next":"/"}` |
| `GET /api/status` with the session cookie | `200` |

Both units were `active` and `enabled` after the gateway restart.

## 8. Horus AS has no access to `#bots`

The same restart logged `403 Forbidden (error code: 50001): Missing Access` on a send. Through the API, `GET /channels/1495962372936826991` with the bot token returned `403 Missing Access`. `#bots` carries a permission overwrite denying View Channel (`1024`) to `@everyone` and four role overwrites allowing it; the bot's only role, `Horus AS`, has none. The bot holds no Manage Channels or Manage Roles permission, so it cannot add itself.

## 9. Model

At 10:45 PM I changed `model.default` from `claude-sonnet-5` to `claude-sonnet-5-5` and restarted the gateway. A one-line `hermes chat -q` test logged `API call #1: model=claude-sonnet-5-5 provider=anthropic` and `Turn ended: reason=text_response(finish_reason=stop)`, with no tool calls.

## 10. Agent memory

At 10:55 PM I wrote one 1,402-character entry to `~/.hermes/memories/MEMORY.md` (limit 2,200): what the `executor` MCP server reaches, to look up profile names with `list-connections` and pass `profile` on every call, that a server mentioned by an allowed user in `#bots` is a request to check that host and then make the change without asking, and ssh-mcp's refusals and 240-second limit. Before writing I ran it through Hermes's own `scan_for_threats` at strict scope. The first draft was flagged `ssh_backdoor` for naming the SSH key file by its filename, so I reworded that line, and the second returned no findings. After a gateway restart neither log held a `BLOCKED` line, and a `hermes chat -q` question with no tools answered that it uses the executor SSH app with profile names such as `grey_server` and does not need to ask.

## 11. Name

At 11:00 PM I renamed the agent to Horus. In `~/.hermes/SOUL.md` I replaced the opening "You are Hermes Agent, built by Nous Research." with a line naming it Horus, AlphaSec United's agent, called Horus AS in Discord, and telling it to name Hermes Agent only as the software it runs on. I added a user skin, `~/.hermes/skins/horus.yaml`, with `agent_name: Horus` and the response label ` 𓂀 Horus `, and set `display.skin: horus`. After restarting both units, a `hermes chat -q` question "who are you?" came back under the label `𓂀 Horus` with "I'm Horus, AlphaSec United's AI agent (called Horus AS in Discord)". I copied the original SOUL.md, which holds no withheld values, to `Backups/hermes-01-SOUL.md-2026-11-04` and deleted it from the host.

## 12. Voice

At 11:10 PM I added two paragraphs to `SOUL.md` after the identity line, keeping the original directness paragraph after them. The first gives Horus the voice of the Egyptian sky god in English: measured and slightly archaic, with imagery of Ra, the Nile, temples, scribes and the Two Lands, the homelab as the kingdom it guards, one or two touches per reply, and no invented hieroglyphs or fake quotations. The second puts precision first: commands, hostnames, profile names, paths, errors, numbers and tool output stay exact and plain, and a failure or uncertainty is stated plainly before any flourish. Hermes's `scan_for_threats` at strict scope returned no findings for the 2,047-character file. After restarting both units, a greeting got back "Ra's barque is riding high, the temples of the homelab stand quiet, and I have no fires to report", and a question about root filesystem usage got back `df -h /` with one plain sentence of explanation.

## 13. Notices and the realm of AlphaFly

The gateway's own notices, such as "⚠️ Hermes is shutting down", are fixed interface strings in the bundled `locales/en.yaml`, not model output, so `SOUL.md` does not reach them. Hermes reads a partial overlay of flat dotted keys from `$HERMES_HOME/locales/<lang>.yaml`. I generated `~/.hermes/locales/en.yaml` from the bundled file: every leaf string where "Hermes Agent" or "Hermes" appears outside a backtick span, with that word replaced by "Horus" and `☤` by `𓂀`, and every `{placeholder}` checked unchanged. That is 120 of 3,515 strings. Through Hermes's own `agent.i18n.t` with its bootstrap loaded, `gateway.shutdown.notice_shutdown` returned "⚠️ Horus is shutting down…", `gateway.shutdown.notice_restart` "⚠️ Horus is restarting…" and `gateway.startup.online` "♻️ Gateway online — Horus is back and ready." A first check with bare Python failed on `No module named 'ruamel'`, which concerned the check, not the overlay; after the restart the gateway log held no `Failed to load i18n overlay` line.

In `SOUL.md` I replaced "The homelab is the kingdom you watch over" with a line naming the realm of AlphaFly, the servers as the temples of AlphaFly, and an instruction never to call it "the homelab" or "the lab" when speaking. The scan returned no findings. Asked what it watches over, Horus answered "I watch over AlphaFly, the temples (servers and virtual machines), the roads between them, and the services that dwell within".

## 14. Channel access, quieter Discord output and where instructions live

I added the `Horus AS` role to `#bots`. Afterwards `GET /channels/1495962372936826991` with the bot token returned `200`. The channel's history showed the first exchange in a thread named "God Horus". Before the answer, Horus had posted a tool-progress message listing `tool_search` and four `mcp__executor__execute` calls. It answered that four players were on the Minecraft server, from `mc-monitor status` in the `minecraft` container on `alpha_prod_01`. A request from `MB-user` at 02:09 UTC had no @mention and got no reply, which is the `require_mention` default.

At about 11:12 PM:

- `display.platforms.discord`: `tool_progress: log`, `interim_assistant_messages: false`, `show_reasoning: false`, so Discord gets only the final answer and each tool call goes to `~/.hermes/logs/tool_calls.log`.
- In the locale overlay, the shutdown, restart and back-online notices now open with `𓂀` in place of `⚠️` and `♻️`.
- I moved the standing instructions out of memory, because Hermes's docs reserve memory for facts the agent learns and the agent can rewrite or drop those entries itself. The `#bots` behaviour and Discord formatting rules are a channel prompt under `discord.channel_prompts."1495962372936826991"`, which Hermes applies to the channel's threads as well. The how-to and a role map of all 31 ssh-mcp profiles are the user skill `homelab-ops`. Both passed `scan_for_threats` at strict scope. `hermes config set` refused the multi-line prompt as a value, so I appended it to `config.yaml` as a YAML block, and `hermes config get discord.channel_prompts` read it back. I deleted `MEMORY.md`. After the restart the gateway registered 40 skills, one more than before, and connected as `Horus AS#9152`.

Two exchanges in `#bots` threads after the restart, at 11:14 PM and 11:31 PM, each logged one `Sending response` line, 364 and 1,003 characters. The second, a request from `MB-user` to change a Minecraft server setting, took 87.9 seconds and 12 API calls, and its `mcp__executor__execute` calls appear in `tool_calls.log` at 23:30 rather than in the thread.

On 2026-11-05 at 11:07 AM I changed `discord-no-dms` to fail closed. It had skipped only an event whose `chat_type` was exactly `dm`, so any other value would have fallen through to authorization, which admits allowlisted DMs. The adapter sets `chat_type` as a plain string, `group` or `thread` for server messages and `dm` for DMs, so the old check matched every DM it was given; the change guards against a value it did not expect. The hook now lowercases the platform and chat type, unwrapping an enum's `.value`, and passes a Discord event only when its chat type is `group`, `thread` or `channel`. A local test with stub events skipped `dm`, `DM`, a missing chat type and an unknown one, and passed `group`, `thread`, `channel` and a Telegram `dm`. The file on the host matched the tracked copy by SHA-256, `hermes plugins list` showed the plugin `enabled`, and after the restart the gateway connected as `Horus AS#9152`.

At 12:15 PM on 2026-11-05 a DM from my account was dropped: the log showed `dropped Discord DM from user … (chat type 'dm')` and `pre_gateway_dispatch skip: reason=discord-dms-disabled`, with no inbound-message, agent or `response ready` line, so no model call was made. The DM still got a `👀` reaction, because the adapter's `on_processing_start` reacts before the dispatch hook runs. The adapter hard-codes `intents.dm_messages = True` when it builds its `commands.Bot` (discord.py 2.7.1), and only `DISCORD_REACTIONS=false` would stop the reaction, which would also stop it in `#bots`. So version 1.1 of the plugin wraps `commands.Bot.__init__` at registration and clears `dm_messages`, `dm_reactions` and `dm_typing` on the `intents` it is given. The dispatch hook stays as a backstop. After the 12:16 PM restart the log showed `cleared Discord DM intents (dm_messages, dm_reactions, dm_typing)` at 12:16:42, then `Connected as Horus AS#9152`, and the host file matched the tracked copy by SHA-256. A wrapper on a class Hermes does not own can stop working after `hermes update`; that log line is how to tell.

Tracked copies of every file I deployed on the host are under [Configuration](../../Configuration/).

## Left open

- Not yet observed: a DM sent after the intent change, which should get no reaction and leave no log line at all.
- Sessions do not end on their own. Hermes core ignores the legacy `session_reset` block, so a thread stays one session until `/new` or `/reset`. The community catalog plugin `hermes-session-reset-policy` (v0.3.0, pinned in the catalog to commit `0f2ea5a`) restores idle and daily resets; I have not installed it.
- The two failed tools and monitoring are listed in the [README](../../README.md#open-items).
