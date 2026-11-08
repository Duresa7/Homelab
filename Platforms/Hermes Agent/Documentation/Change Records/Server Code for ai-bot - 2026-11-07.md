# Server Code for #ai-bot

**Created:** 2026-11-07  
**Last updated:** 2026-11-07

**Implementation date:** 2026-11-07, about 5:50 PM to 7:30 PM Eastern  
**Status:** Deployed. Two live tests failed. The second fix went live at 7:21 PM, and the retest is still to do.  
**Affected systems:** `hermes-01` (`~/.hermes/plugins/discord-open-channel/`, `~/.hermes/config.yaml`, `~/.hermes/.env`, `~/.hermes/profiles/public/SOUL.md`)

Anyone who can see `#ai-bot` can now talk to Horus there. They get the chat-only `public` profile, which has no terminal, files, MCP or Discord fetch tool. Server work needs the server code. Typing it unlocks the full `default` profile for that person, in that thread, for 15 minutes. A code typed in the channel itself, with an @mention, unlocks all of that person's `#ai-bot` threads for 15 minutes. My account and `MB-user` need the code too.

## Why the model never sees the code

A password the model checks is a password the model knows, and a model can be talked into revealing it or skipping the check. So the check runs in the `discord-open-channel` plugin, inside the Discord adapter, before Hermes batches, routes or records a message:

- Every server message is compared with `HORUS_SERVER_CODE_HASH` (`v1$<salt>$<HMAC-SHA256>` in `~/.hermes/.env`). The comparison covers the whole message and every run of up to 8 words, with surrounding punctuation and backticks trimmed, so a code inside a sentence is caught too. It is case-sensitive.
- A match is deleted through the Discord API (Horus AS has Manage Messages in `#ai-bot`), answered with "Password accepted. Unlocked for 15 minutes.", and dropped. If the message held other text, the answer adds "Send your request again."
- The code in `#secret` is deleted and answered with "That code only works in #ai-bot." It unlocks nothing there.
- The Discord adapter names an auto-thread from the message before the check runs. The plugin stops a message holding the code from creating a thread, and never lets a thread be named after it.
- Hermes merges text messages sent within 0.6 seconds of each other into one, under the first message's id. Typed text is checked before it joins a batch, so the message deleted is the one holding the code.

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

## Second live test failed

At 7:11 PM I typed the code alone in a new thread, twice. Same result: both messages went to the chat-only Horus, and the plugin logged nothing.

Both earlier fixes assumed the plugin's `pre_gateway_dispatch` hook runs for every `#ai-bot` message. It does not. The multiplexing gateway routes a message to its profile first (`_make_default_profile_message_handler` in `gateway/run_adapters.py`) and runs `_handle_message`, hook included, inside that profile's scope. Hermes keeps one plugin manager per profile home, and `public` has no user plugins. A probe on `hermes-01` that enters each profile's runtime scope the way the gateway does showed it:

```
default scope: home /home/dkadi/.hermes | has pre_gateway_dispatch: True
public scope:  home /home/dkadi/.hermes/profiles/public | has pre_gateway_dispatch: False
```

A locked sender is always routed to `public`, so the hook never ran for the code. The plugin's other patches sit on classes shared by the whole process, which is why admission and routing worked. The 2026-11-05 rule that drops typed commands from outsiders in `#secret` never ran either, for the same reason. A message sent while Horus is still answering skips `_handle_message` altogether (`_handle_active_session_busy_message` in `gateway/run_busy.py`), so even a working hook would have missed that case.

Fix, plugin version 2.1, deployed with a restart at 7:21 PM: the check moved into the Discord adapter class, which the plugin already patches. `DiscordAdapter._handle_message` hands typed text to `_enqueue_text_event` and everything else to `handle_message`. Both run before profile routing and before the busy-path split, and the plugin wraps both. The plugin no longer registers `pre_gateway_dispatch`. The previous plugin is kept as `~/.hermes/plugin-backups/discord-open-channel-2026-11-07-pre-adaptergate.tar`.

The test script now has 44 checks. The new ones drive the patched adapter: a typed code never joins a batch, the unlock holds before the batch is sent on, the batched code message is the one deleted, a code sent while Horus is answering is dropped, and an internal event passes. With the live home, the script also reads the real `DiscordAdapter._handle_message` and `BasePlatformAdapter.handle_message` source and checks that every message still passes the two wrapped methods. All 44 pass. After the restart, `agent.log` shows both plugin lines, no warning, and `Connected as Horus AS#9152`.

### Clean-up

The same steps as the first time:

- Deleted the two messages holding the code from thread `1568779830843940995` (HTTP 204 each). The script found them by checking each message against the stored hash, so the script itself never held the code. A re-read of the thread and of `#ai-bot` found none left.
- Deleted the `public` session `20261107_191109_a6a1b831`.
- Replaced the code with `[redacted]` in `profiles/public/logs/gateway.log` (2 lines) and `agent.log` (4 lines), and ran `VACUUM` on `profiles/public/state.db`. Afterwards: 0 free pages, `integrity_check` ok.
- A search of `~/.hermes`, outside the Hermes source, tools and caches, found no file containing the code.

## Open

- Retest in Discord: a message without the code gets the chat-only Horus; the code alone in a thread is deleted and answered; a server request then works; a second person in the same thread stays chat-only; after 15 minutes the thread is chat-only again.
- Nothing limits guesses at the code, and anyone in `#ai-bot` can spend Anthropic credit.
- After each `hermes update`, run the test script with the live home and check `agent.log` for the two plugin lines above. Its live checks fail if Hermes stops sending every Discord message through the two wrapped methods.
- Delete `plugin-backups/discord-open-channel-2026-11-07-pre-adaptergate.tar` and the older plugin backups once the retest passes.
- Delete the `.bak-2026-11-07-servercode` files once this has run for a while.
