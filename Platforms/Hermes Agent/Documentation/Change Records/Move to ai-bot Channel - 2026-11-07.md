# Move Horus to #ai-bot

**Created:** 2026-11-07  
**Last updated:** 2026-11-07

**Implementation date:** 2026-11-07, about 2:40 PM to 2:45 PM Eastern  
**Status:** Deployed. A first @mention in `#ai-bot` from an allowed user is still to do.  
**Affected systems:** `hermes-01` (`~/.hermes/.env`, `~/.hermes/config.yaml`, `~/.hermes/profiles/public/SOUL.md`, `~/.hermes/plugins/discord-open-channel/__init__.py`)

Horus's private, full-access channel moved from `#alert-bots` (`1495962372936826991`) to `#ai-bot` (`1568709425131290704`) in Home Base, so it no longer shares a channel with the Anubis AS alerts. The earlier records call the old channel `#bots`; its name in Discord is `alert-bots`. `#secret` is unchanged.

## Before the change

With the bot token, `/channels/1568709425131290704` returned `ai-bot`, type 0, guild `984884989407690883`, in the same category as `#alert-bots`. `#ai-bot` denies View Channel to `@everyone`, grants it to `Good Kush` and `AI-Access`, and grants it to Horus AS by a member overwrite. From the guild roles and those overwrites, Horus AS has the same permissions in `#ai-bot` as in `#alert-bots`: View, Send, Send in Threads, Create Public Threads, Embed Links, Attach Files, Read Message History and Add Reactions. `Good Kush` and `AI-Access` can view and post there. `adm`, which could view `#alert-bots`, cannot view `#ai-bot`.

## What I changed

Each file was copied first to `<file>.bak-2026-11-07` with `cp -p`.

1. `.env`: in `DISCORD_ALLOWED_CHANNELS` and `DISCORD_HOME_CHANNEL`, `1495962372936826991` became `1568709425131290704`. `DISCORD_ALLOWED_CHANNELS` is now `1568709425131290704,1016933615793356820`. `DISCORD_NO_THREAD_CHANNELS` is unchanged, so `#ai-bot` still gets a thread per @mention.
2. `config.yaml`: the `discord.channel_prompts` key moved to `"1568709425131290704"`. The prompt's opening now says `#ai-bot`, as does the comment above it. Tracked copy: [channel-prompt-bots.txt](../../Configuration/channel-prompt-bots.txt).
3. `profiles/public/SOUL.md`: server work in `#secret` is now sent to `#ai-bot`. Tracked copy: [SOUL.md](../../Configuration/profiles/public/SOUL.md).
4. `plugins/discord-open-channel/__init__.py`: the module docstring says `#ai-bot`. The code holds only `#secret`'s ID, so its behaviour is unchanged.
5. `systemctl --user restart hermes-gateway` at 2:42:49 PM.

I made the change through `qm guest exec` on `grey-server`, running each script as `dkadi` with `runuser -l`. SSH from Ubuntu-dev to `hermes-01` began timing out partway through, after about eight logins in two minutes. At that point `hermes-01` was up, `sshd` was listening, the host had no nftables rules, and its journal showed no attempt after the last accepted login. SSH to `alpha-prod-01` on the same VLAN still connected, so something on the network path dropped that one source and destination pair. I did not check UniFi to find out what.

## Verification

- No `1495962372936826991` left in `.env` or `config.yaml`. Modes stayed `600`.
- The gateway came back `active` at 2:42:49 PM. `agent.log` showed the `discord-open-channel` and `discord-no-dms` lines, then `Connected as Horus AS#9152` at 2:42:55 PM. `gateway.log` showed `Gateway running with 2 platform(s)` and no errors.
- The bot token read `#ai-bot`'s messages with no `403`; the channel was empty. The shutdown notice from the outgoing process went to `#alert-bots` at 2:42:48 PM, before the new config loaded.

## Open

- @mention Horus in `#ai-bot` and check that it opens a thread and answers.
- Find out what blocked SSH from `192.168.40.179` to `192.168.80.22`. The block had lifted about ten minutes later, and UniFi's intrusion prevention is the likely cause.
- Delete the `.bak-2026-11-07` copies on `hermes-01` once `#ai-bot` has been working for a while.
