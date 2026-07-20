# OpenClaw Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

## What This Guide Covers

I configured OpenClaw as a Discord assistant for one server and one channel. This guide covers the gateway service, channel allowlist, mention requirement, idle-session reset, public-channel rules, & member resolver.

## Current Status and Verified Versions

The recorded OpenClaw version is 2026.4.25. `openclaw-gateway.service` runs as a user service under `openclaw`, user linger is enabled, & the gateway binds only to `127.0.0.1:18789`. Discord access is limited to one guild and `#alpha-ai`; DMs are disabled and a mention is required.

## What You Need

- A Linux account dedicated to OpenClaw.
- An OpenClaw installation and its user-level systemd service.
- A Discord application added to your server.
- The guild ID and channel ID you intend to allow.
- A test account that can send messages in and outside the allowed channel.

## How the Pieces Fit Together

> Diagram placeholder

## Walkthrough

### Step 1: Install OpenClaw Under Its Service Account

I installed OpenClaw for the `openclaw` account, kept its workspace under `/home/openclaw/.openclaw/workspace`, & confirmed the running version before changing Discord behavior.

### Step 2: Create the User Service

I installed `openclaw-gateway.service` in the user's systemd directory, enabled linger, enabled the service, & started it.

```sh
systemctl --user enable --now openclaw-gateway.service
systemctl --user status openclaw-gateway.service
```

I checked that the process listened on `127.0.0.1:18789`, not a LAN address.

### Step 3: Restrict Discord Scope

I added `<YOUR_DISCORD_GUILD_ID>` and `<YOUR_DISCORD_CHANNEL_ID>` to the allowlist, disabled direct messages, & required a mention before the bot responds. I used real Discord IDs rather than names because names can change.

### Step 4: Set the Public-Channel Rules

I kept the assistant's identity, organization, & allowed public behavior in the workspace instructions. I also told it not to repeat internal system output or deployment details into the channel.

### Step 5: Set the Idle Reset

I set group sessions to reset after 60 minutes of inactivity. The reset happens when the next message arrives. I kept `/new` available for an immediate clean session.

### Step 6: Add the Discord Member Resolver

I connected the `discord_member_resolver` tool so the assistant can turn a name into a Discord `<@USER_ID>` mention. It asks for clarification on multiple matches and doesn't guess when no match exists.

### Step 7: Test Allowed and Denied Paths

I mentioned the bot in `#alpha-ai`, sent a message without a mention, tried another server channel, & tried a DM. Only the allowed channel with a direct mention should receive a response.

## What I Checked After Each Step

- OpenClaw reported version 2026.4.25.
- The user service was enabled and running.
- The gateway listened only on loopback port 18789.
- A mention in the allowed channel received a response.
- Messages without a mention, outside the allowlist, & in DMs received no response.
- The member resolver returned one ID, requested clarification, or returned no match as appropriate.

## Troubleshooting and Recovery

If Discord receives no response, check the user service, recent journal entries, application membership, guild ID, channel ID, & mention setting. If it responds in the wrong place, stop the service first, restore the last configuration backup, & retest every denied path before restarting normal use.

## Known Limits

The source record describes the configured behavior but doesn't include a clean installation transcript from an empty host. It also doesn't record a later OpenClaw version check.

## Source Records

- [Setup overview](../Platforms/Openclaw/Documentation/OpenClaw-Setup-Overview.md)
- [2026-04-27 change record](../Platforms/Openclaw/Documentation/OpenClaw-Change-Record-2026-04-27.md)
