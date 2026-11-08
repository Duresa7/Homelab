# Open the #secret Channel

**Created:** 2026-11-05  
**Last updated:** 2026-11-05

**Implementation date:** 2026-11-05, about 5:15 PM to 5:45 PM Eastern  
**Status:** Deployed. The live test from an account outside the allowlist is still open.  
**Affected systems:** `hermes-01` (`~/.hermes/config.yaml`, `~/.hermes/.env`, new profile `public`, new plugin `discord-open-channel`)

Horus now answers anyone in Home Base who @mentions it in `#secret` (`1016933615793356820`). It replies in the channel without opening a thread, and it does that as a separate, chat-only profile. In `#secret` it has the Horus voice and nothing else: no Executor, no terminal, no files, no Discord fetch tool. `#bots` is unchanged.

## Why not just open the allowlist

`DISCORD_ALLOWED_USERS` covers the whole bot. Hermes v0.22.7 has no setting that admits every sender in one channel and keeps another channel to named people. Discord's `group_allowed_chats_env` does not exist, and `DISCORD_ALLOWED_ROLES` set to the `@everyone` role would admit everyone in `#bots` as well. Since the default profile gives root on every ssh-mcp host with no approval step, opening the user list would have handed that to anyone in the server.

A sender passes two checks: `DiscordAdapter._is_allowed_user` at intake, then `GatewayAuthorizationMixin._principal_authorized` in the gateway. For a routed message, both checks run under the receiving bot's profile, which is `default`.

## What I changed

1. **Profile `public`.** I created it with `hermes profile create public --no-skills --no-alias`, then installed [config.yaml](../../Configuration/profiles/public/config.yaml) (`claude-sonnet-5-5` on Anthropic, `platform_toolsets.discord: [vision]`, memory and user profile off, skin `horus`) and [SOUL.md](../../Configuration/profiles/public/SOUL.md). The SOUL is the default one with one more paragraph saying it holds no keys to the temples in `#secret`, should send server work to `#bots`, and must not share hostnames, addresses, credentials or how AlphaFly is built. The skin and the locale overlay are copies of the default profile's. Its `.env` holds only `ANTHROPIC_API_KEY`, copied from the default `.env` with `grep` so the value never printed.
2. **Route.** In `~/.hermes/config.yaml`, `gateway.profile_routes` went from `[]` to one route, `secret-channel`: platform `discord`, `guild_id` `984884989407690883`, `chat_id` `1016933615793356820`, profile `public`. `multiplex_profiles: true` was already set.
3. **Channel gates** in `~/.hermes/.env`: `DISCORD_ALLOWED_CHANNELS` is now `1495962372936826991,1016933615793356820`. I added `DISCORD_NO_THREAD_CHANNELS=1016933615793356820`, which stops the auto-thread there.
4. **Plugin [`discord-open-channel`](../../Configuration/plugins/discord-open-channel/__init__.py)** in `~/.hermes/plugins/`, added to `plugins.enabled` after `discord-no-dms`:
   - `_is_allowed_user` returns true for a server message whose channel, or a thread's parent, is `#secret`. Slash-command interactions skip that exception, because the plugin wraps `_evaluate_slash_authorization` and turns it off for the duration of the call.
   - `_principal_authorized` returns true for a Discord `group`, `thread` or `channel` source in `#secret` that has a user ID.
   - A `pre_gateway_dispatch` hook drops typed `/commands` in `#secret` from anyone outside `DISCORD_ALLOWED_USERS`, so `/restart`, `/model` and the rest stay with my allowlist.
   - `DiscordAdapter.send` refuses lifecycle notices bound for `#secret`: any send marked `non_conversational`, and any text that starts like one of these catalog strings, after the locale overlay: `gateway.shutdown.notice_restart`, `notice_shutdown`, `cron_interrupted`, `gateway.startup.restarted`, `online`, `gateway.draining`, `gateway.restart.in_progress`, `restarting`, and the three `gateway.busy.drain_*` strings. `#bots` still gets them.

   Each patch fails closed. If one does not apply, `#secret` stays shut to anyone outside the allowlist, and `#bots` is untouched.

I did not copy `config.yaml` or `.env` before editing. Every change was an addition, and the exact lines are listed above.

## Verification

- `DISCORD_ALLOWED_CHANNELS=1495962372936826991,1016933615793356820` and `DISCORD_NO_THREAD_CHANNELS=1016933615793356820` read back from `.env`. `profile_routes` and `plugins.enabled` read back as written.
- The bot token's `/channels/1016933615793356820` returned `secret`, type 0, guild `984884989407690883`. `Home Base` is the bot's only server.
- `hermes -p public tools list --platform discord`: `vision` enabled, every other built-in toolset disabled, `terminal`, `file`, `code_execution`, `discord`, `memory`, `delegation` and `connections` included. `hermes -p public mcp list` showed no servers.
- The plugin compiled with the bundled Python 3.14.9.
- I restarted the gateway at 5:38 PM. `systemctl --user is-active hermes-gateway` returned `active`. `agent.log` showed `plugins.discord-open-channel: opened Discord channel(s) 1016933615793356820 to every sender` twice, at 5:38:46 PM, once for each loaded copy of the adapter class (`plugins.platforms.discord.adapter` and `hermes_plugins.platforms__discord.adapter`). Then `cleared Discord DM intents` and `Connected as Horus AS#9152` at 5:38:50 PM. `gateway.log` showed `[MULTIPLEX] Now serving profile 'public'` and the cron scheduler ticking `['default', 'public']`.
- In `agent.log` the plugin loader also logged `capability_check plugin=discord-open-channel capability=tools.override decision=deny`. The plugin overrides no tools, and the patches applied anyway.

## First use and clean-up

Between 5:43 and 5:45 PM, Horus posted four replies in `#secret`, in the channel itself with no thread. They were in the Horus voice and said it cannot act on any server, which is the `public` profile's wording. I did not check who the senders were before I deleted those four messages through the bot token at about 5:50 PM. A re-read of the last 100 messages afterwards found no Horus messages left. A minute later the same token got `403 Forbidden` on `/channels/1016933615793356820/messages`, so the bot can no longer read `#secret`. Until that access comes back, Horus cannot answer there.

## Open

- I still need to @mention Horus in `#secret` from an account outside the allowlist. I expect a reply in the channel with no thread. A `/restart` typed in `#secret` from that account should get no reply, and `agent.log` should show `dropped a command in open channel`. I also still need to check that the next restart posts nothing in `#secret`.
- The plugin patches Hermes internals: `_is_allowed_user`, `_evaluate_slash_authorization`, `send` and `_principal_authorized`. After each `hermes update` I need to check that the `opened Discord channel(s)` line still appears.
- Every message in `#secret` from anyone in Home Base is a paid Anthropic request. Nothing limits the rate.
