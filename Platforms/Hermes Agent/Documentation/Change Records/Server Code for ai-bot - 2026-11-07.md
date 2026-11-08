# Server Code for #ai-bot

**Created:** 2026-11-07  
**Last updated:** 2026-11-07

**Implementation date:** 2026-11-07, about 5:50 PM to 6:30 PM Eastern  
**Status:** Deployed. The first live test failed and was fixed at 6:27 PM; the retest is still to do.  
**Affected systems:** `hermes-01` (`~/.hermes/plugins/discord-open-channel/`, `~/.hermes/config.yaml`, `~/.hermes/.env`, `~/.hermes/profiles/public/SOUL.md`)

Anyone who can see `#ai-bot` can now talk to Horus there. They get the chat-only `public` profile, which has no terminal, files, MCP or Discord fetch tool. Server work needs the server code. Typing it unlocks the full `default` profile for that person, in that thread, for 15 minutes. A code typed in the channel itself, with an @mention, unlocks all of that person's `#ai-bot` threads for 15 minutes. My account and `MB-user` need the code too.

## Why the model never sees the code

A password the model checks is a password the model knows, and a model can be talked into revealing it or skipping the check. So the check runs in the `discord-open-channel` plugin's `pre_gateway_dispatch` hook, before Hermes records or routes a message:

- Every server message is compared with `HORUS_SERVER_CODE_HASH` (`v1$<salt>$<HMAC-SHA256>` in `~/.hermes/.env`). The comparison covers the whole message and every run of up to 8 words, with surrounding punctuation and backticks trimmed, so a code inside a sentence is caught too. It is case-sensitive.
- A match is deleted through the Discord API (Horus AS has Manage Messages in `#ai-bot`), answered with "Password accepted. Unlocked for 15 minutes.", and dropped. If the message held other text, the answer adds "Send your request again."
- The code in `#secret` is deleted and answered with "That code only works in #ai-bot." It unlocks nothing there.
- The Discord adapter names an auto-thread from the message before the hook runs. The plugin stops a message holding the code from creating a thread, and never lets a thread be named after it.

The code itself is stored nowhere on `hermes-01`. It was entered through a T3 secret prompt on Ubuntu-dev, hashed there, and only the hash was copied over.

## Routing

Two routes were added to `gateway.profile_routes` after `secret-channel`:

| Route | Match | Profile | Specificity |
|---|---|---|---|
| `ai-bot-server-code` | guild, `#ai-bot`, `user_id: server-code-unlocked` | `default` | 22 |
| `ai-bot-channel` | guild, `#ai-bot` | `public` | 6 |

No Discord account has the ID `server-code-unlocked`, so `ai-bot-server-code` matches only through the plugin's wrapper around `ProfileRoute.matches`, and only for a sender with a live unlock. The unlock table lives in the gateway's memory, so a restart locks everyone again.

## Fail-closed checks

- The plugin admits a sender outside `DISCORD_ALLOWED_USERS` in an open channel only when the routes send them to a profile other than `default`, or through `ai-bot-server-code`. Without the `ai-bot-channel` route, outsiders are refused rather than handed the full profile.
- If the routing patch does not apply, the unlock route never matches and everyone stays chat-only.
- If `HORUS_SERVER_CODE_HASH` is missing or malformed, nobody can unlock, and the plugin logs a warning at start.

## What I changed

Backups first: `config.yaml.bak-2026-11-07-servercode`, `.env.bak-2026-11-07-servercode` and `profiles/public/SOUL.md.bak-2026-11-07-servercode` in `~/.hermes`, and the previous plugin as `~/.hermes/plugin-backups/discord-open-channel-2026-11-07-servercode.tar`.

1. [`discord-open-channel`](../../Configuration/plugins/discord-open-channel/__init__.py) version 2.0. The channel set became a `CHANNELS` table of per-channel policies (`#secret` quiet and never unlockable, `#ai-bot` unlockable). It adds the server code, the unlock table, the route wrapper, the admission rule and the auto-thread guard.
2. The two routes above.
3. `HORUS_SERVER_CODE_HASH` in `.env`, mode 600.
4. The [public SOUL](../../Configuration/profiles/public/SOUL.md) now covers `#ai-bot`: it says server work needs the code, typed by itself in the thread, and that it does not know the code, so it never asks for it, guesses it or discusses it.
5. `systemctl --user restart hermes-gateway` at 6:07 PM.

## Verification

- [`test_open_channel.py`](../../Configuration/plugins/discord-open-channel/test_open_channel.py) ran on `hermes-01` with Hermes's own Python and its real `parse_profile_routes` and `match_profile_route`, using a throwaway code and no Discord calls. All 32 checks passed. They cover a code alone, with an @mention, inside a sentence and in backticks; a near miss and a lowercase version unlocking nothing; the unlock holding at 14:59 and ending at 15:00; another sender in the same thread and the same sender in another thread staying chat-only; `#secret` never unlocking; outsiders' typed `/commands` dropped; the missing-route refusal; a malformed hash; and the auto-thread guard.
- The real code was checked the same way on Ubuntu-dev before hashing, alone, with an @mention, inside a sentence, in backticks and with its case flipped.
- After the restart, `agent.log` showed `server code unlocks route ai-bot-server-code for 15 minutes`, `opened Discord channel(s) 1016933615793356820, 1568709425131290704 to every sender` once for each loaded copy of the adapter class, no hash warning, and `Connected as Horus AS#9152`. `MCP: registered 6 tool(s) from 1 server(s)` shows the full profile has Executor.
- Hermes's config loader read the new routes back as written.
- The bot token's permissions in `#ai-bot` include Manage Messages.

## First live test failed

At 6:18 and 6:19 PM I typed the code alone in a thread, twice. Both messages went to the chat-only Horus as ordinary text, were not deleted, and unlocked nothing.

The plugin read `HORUS_SERVER_CODE_HASH`, `DISCORD_BOT_TOKEN` and `DISCORD_ALLOWED_USERS` from `os.environ`. A multiplexing gateway keeps every profile's `.env` out of `os.environ` (`agent/secret_scope.py`), so at message time the plugin saw no code and treated every message as text. The same flaw meant the bot token for deleting was missing, and the `DISCORD_ALLOWED_USERS` check for typed commands, inherited from the 2026-11-05 version, never matched anyone. The test script had put those values into `os.environ` itself, so it shared the wrong premise and passed.

Fix, deployed with a restart at 6:27 PM: the plugin reads its own profile's secrets through `agent.secret_scope.build_profile_secret_scope(~/.hermes)`. The test script now takes the live home as a second argument and, with multiplexing on and the `public` profile's scope bound, checks that the three keys are readable and the hash parses. All 36 checks pass. The previous plugin is kept as `~/.hermes/plugin-backups/discord-open-channel-2026-11-07-pre-secretfix.tar`.

### Clean-up

The code was visible in the thread and had reached the chat-only profile. I kept the same code. The clean-up:

- Deleted the two messages whose whole text was the code from the thread (HTTP 204 each); a re-read found none left.
- Deleted the `public` session `20261107_181736_823d94db` ("Check Minecraft server player count", 11 messages, 2 holding the code).
- Replaced the code with `[redacted]` in `profiles/public/logs/gateway.log` (2 lines) and `agent.log` (4 lines). Hermes logs inbound text in `_handle_message_with_agent` (`gateway/run_turn.py`), which runs after the hook, so a dropped code message is no longer logged.
- Ran `VACUUM` on `profiles/public/state.db`, which still held the deleted rows in 15 free pages. Afterwards: 0 free pages, `integrity_check` ok.
- A search of `~/.hermes`, outside the Hermes source, tools and caches, found no file containing the code.

## Open

- Retest in Discord: a message without the code gets the chat-only Horus; the code alone in a thread is deleted and answered; a server request then works; a second person in the same thread stays chat-only; after 15 minutes the thread is chat-only again.
- Nothing limits guesses at the code, and anyone in `#ai-bot` can spend Anthropic credit.
- After each `hermes update`, run the test script and check `agent.log` for the two plugin lines above.
- Delete the `.bak-2026-11-07-servercode` files once this has run for a while.
