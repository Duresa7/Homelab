# OpenClaw Change Record

**Created:** 2026-04-27  
**Last updated:** 2026-07-20

**Change time:** 2026-04-27 15:04 EDT  
**Environment:** `AI_Alpha_01`  
**Service:** OpenClaw Gateway  
**Status:** Running

## Result

I upgraded OpenClaw from `2026.4.15` to `2026.4.25`, enabled the gateway service, limited the bot to one Discord channel, added a 60-minute group-session reset, & installed the Discord member resolver. The final service state was `active` on loopback.

## Changes

### Service and Runtime

- Updated OpenClaw from `2026.4.15` to `2026.4.25`.
- Reinstalled the OpenClaw gateway user service after the update.
- Enabled `openclaw-gateway.service` for the `openclaw` user.
- Enabled user linger for the `openclaw` account so the user service can run without an active login session.
- Started the OpenClaw gateway service after completing configuration work.

### File and Directory Permissions

- Tightened `/home/openclaw/.ssh-manager` permissions from `775` to `700`.
- Confirmed `/home/openclaw/.ssh-manager/.env` remained `600`.
- Confirmed OpenClaw configuration validation passed after changes.

### Discord Access Restrictions

- Restricted Discord operation to one server and one channel:
  - Server: `Home Base`
  - Guild ID: `<YOUR_DISCORD_GUILD_ID>`
  - Channel: `#alpha-ai`
  - Channel ID: `<YOUR_DISCORD_CHANNEL_ID>`
- Configured the Discord channel policy to require a bot mention.
- Disabled Discord DMs for the bot.
- Configured non-allowed guilds and channels to be denied.

### Session Behavior

- Added a group-chat idle session reset policy:

```json
{
  "session": {
    "dmScope": "per-channel-peer",
    "resetByType": {
      "group": {
        "mode": "idle",
        "idleMinutes": 60
      }
    }
  }
}
```

- Result: after 60 minutes of inactivity, the next inbound group message starts a fresh session automatically.

### Identity and Public-Channel Behavior

- Updated `SOUL.md`, `IDENTITY.md`, and `AGENTS.md`.
- Removed the requirement to reference AlphaFly in every response.
- Set the bot identity as a professional representative of `<YOUR_ORG_NAME>` United LLC.
- Set the model identity response to:

```text
I am Alpha-Zeta-022 #22, a member of the <YOUR_ORG_NAME> AI Model Fleet developed by <YOUR_ORG_NAME> United.
```

- Added guidance that AlphaFly is the CEO and owner of `<YOUR_ORG_NAME>` United LLC.
- Added rules preventing disclosure of:
  - credentials
  - API keys
  - tokens
  - passwords
  - private keys
  - PII
  - private user metadata
  - deployment details
  - backend/internal implementation details
  - hostnames, server names, logs, paths, and tool internals

### Workspace Files

- Archived stale `BOOTSTRAP.md`.
- Archived old memory files under the OpenClaw workspace.
- Replaced forced proactive heartbeat behavior with a no-proactive-tasks policy.
- Added public Discord channel assumptions.
- Added a refusal response for internal requests.
- Preserved SSH manager MCP usage for authorized administrative work.

### Discord Mention Handling

- Added instructions for proper Discord user mentions using:

```text
<@USER_ID>
```

- Added fallback behavior to ask for a user mention or user ID if the target user cannot be resolved safely.
- Added safeguards against `@everyone`, `@here`, role mentions, mass mentions, repeated mentions, or harassment-style mentions.

### Discord Member Resolver

- Added a local workspace skill named `discord-mention-resolver`.
- Added a local MCP server named `discord_member_resolver`.
- Added the resolver tool to the OpenClaw tool allowlist:

```text
mcp__discord_member_resolver__resolve_discord_user
```

- The resolver searches the configured Discord guild for a member by nickname, display name, username, or plain `@name`.
- When a unique match is found, it returns the proper Discord mention format:

```text
<@USER_ID>
```

- The active Discord channel session was reset after installation so the next message loads the updated skill/tool context.

## Final Checks

- OpenClaw config validation passed.
- Gateway service started successfully.
- Gateway reported ready with the Discord plugin loaded.
- Gateway was listening on loopback only.
- Service status after final start: `active`.
- `discord-mention-resolver` appeared as a ready workspace skill.
- `discord_member_resolver` appeared in the configured MCP server list.

## Remaining Verification

- Mention the bot in `#alpha-ai` and confirm its response from Discord.
- Record future Discord permission, identity, or channel-scope changes in this folder.
