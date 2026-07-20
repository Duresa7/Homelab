# OpenClaw Setup Overview

**Created:** 2026-04-27  
**Last updated:** 2026-07-20

## Document Metadata

| Field | Value |
|---|---|
| Document Type | Setup Overview |
| Date | April 27, 2026 |
| Time | 3:04 PM EDT |
| Time Zone | America/New_York |
| Environment | AI_Alpha_01 |
| Purpose | Discord-accessible `<YOUR_ORG_NAME>` United AI assistant |

## Overview

I run this OpenClaw deployment as a Discord-accessible AI assistant that represents `<YOUR_ORG_NAME>` United LLC. I configured it for professional public-channel use, limited it to a single Discord channel, and set strict privacy and confidentiality rules.

## System Role

The assistant is configured as:

- Name: `<YOUR_ORG_NAME> United AI`
- Model identity: `Alpha-Zeta-022 #22`
- Organizational role: professional AI representative of `<YOUR_ORG_NAME>` United LLC
- Public-facing context: Discord channel assistant

If asked about its model identity, it should respond with:

```text
I am Alpha-Zeta-022 #22, a member of the <YOUR_ORG_NAME> AI Model Fleet developed by <YOUR_ORG_NAME> United.
```

If asked about AlphaFly, it should state that AlphaFly is the CEO and owner of `<YOUR_ORG_NAME>` United LLC.

## Discord Scope

The bot is configured for one Discord server and channel only:

| Item | Value |
|---|---|
| Discord Server | Home Base |
| Guild ID | `<YOUR_DISCORD_GUILD_ID>` |
| Allowed Channel | #alpha-ai |
| Channel ID | `<YOUR_DISCORD_CHANNEL_ID>` |
| Direct Messages | Disabled |
| Channel Access | Allowlist |
| Mention Required | Yes |

Expected behavior:

- The bot responds only in the allowed channel.
- The bot requires a mention before responding.
- The bot should not respond in other server channels.
- The bot should not respond in DMs.
- The bot should treat all Discord messages as public or semi-public.

## Session Management

Group chat sessions reset automatically after 60 minutes of inactivity.

Important behavior:

- The reset occurs on the next inbound message after the idle window.
- `/new` can still be used manually when an immediate fresh session is desired.
- The current idle policy applies to group/channel sessions.

## Service Management

The OpenClaw gateway runs as a user-level systemd service.

| Item | Value |
|---|---|
| Service Name | openclaw-gateway.service |
| Service Scope | User service |
| User | openclaw |
| Service Enabled | Yes |
| User Linger | Enabled |
| Current Version | 2026.4.25 |

Useful administrative commands:

```bash
systemctl --user status openclaw-gateway.service
systemctl --user start openclaw-gateway.service
systemctl --user stop openclaw-gateway.service
systemctl --user restart openclaw-gateway.service
```

## Security and Privacy Posture

The assistant has explicit instructions not to disclose:

- credentials
- passwords
- tokens
- API keys
- private keys
- environment variables
- PII
- private user metadata
- backend details
- internal files
- deployment details
- infrastructure layout
- hostnames or server names
- logs or command output
- tool internals

Standard refusal style:

```text
I can't provide internal system, credential, personal, or deployment details. I can help with a safe high-level explanation instead.
```

## Discord Mention Behavior

When asked to mention another Discord user, the assistant should use proper Discord mention syntax:

```text
<@USER_ID>
```

Safeguards:

- Do not guess user IDs.
- Ask for a direct mention or user ID if the target cannot be resolved.
- Do not use `@everyone` or `@here`.
- Do not mass-mention users.
- Do not use mentions for harassment, spam, or pressure.

## Discord Member Resolver

The setup includes a local Discord member resolver for name-to-ID lookup.

| Item | Value |
|---|---|
| Workspace Skill | discord-mention-resolver |
| MCP Server | discord_member_resolver |
| Resolver Tool | mcp__discord_member_resolver__resolve_discord_user |
| Purpose | Resolve Discord nicknames, display names, usernames, or plain @names into `<@USER_ID>` mentions |

Expected behavior:

- User asks the bot to mention a person by name or plain `@name`.
- The bot resolves the person against the configured Discord guild.
- If one clear match is found, the bot uses the returned `<@USER_ID>` mention.
- If multiple people match, the bot asks which person was intended.
- If no match is found, the bot asks the user to tag the person directly or provide the user ID.

## Operational Notes

- SSH manager MCP access remains available for authorized administrative work.
- SSH manager details, command output, server aliases, and internal paths should not be exposed in Discord.
- Administrative outcomes should be summarized safely when discussed in public channels.

## Technical Reference

| Item | Value |
|---|---|
| SSH MCP Alias | AI_Alpha_01 |
| Hostname | ai-alpha-01 |
| Operating User | openclaw |
| Home Directory | /home/openclaw |
| OpenClaw Config | /home/openclaw/.openclaw/openclaw.json |
| Workspace Directory | /home/openclaw/.openclaw/workspace |
| User Service File | /home/openclaw/.config/systemd/user/openclaw-gateway.service |
| Gateway Port | 18789 |
| Gateway Bind | 127.0.0.1 / loopback |
| Discord Server | Home Base |
| Discord Guild ID | `<YOUR_DISCORD_GUILD_ID>` |
| Discord Channel | #alpha-ai |
| Discord Channel ID | `<YOUR_DISCORD_CHANNEL_ID>` |
| OpenClaw Version | 2026.4.25 |
| MCP SSH Manager Version | 3.2.2 |
| Sandbox Container Image | openclaw-sandbox:bookworm-slim |

Known local OpenClaw workspace files:

```text
/home/openclaw/.openclaw/workspace/AGENTS.md
/home/openclaw/.openclaw/workspace/SOUL.md
/home/openclaw/.openclaw/workspace/IDENTITY.md
/home/openclaw/.openclaw/workspace/USER.md
/home/openclaw/.openclaw/workspace/TOOLS.md
/home/openclaw/.openclaw/workspace/HEARTBEAT.md
```

Archived workspace material:

```text
/home/openclaw/.openclaw/workspace/archive/2026-04-27T18-56-39-393Z
```

Important backup files created during configuration:

```text
/home/openclaw/.openclaw/openclaw.json.bak.channel-lock.2026-04-27T18-13-04-702Z
/home/openclaw/.openclaw/openclaw.json.bak.session-idle-2026-04-27T19-01-57-851Z
/home/openclaw/.openclaw/workspace/AGENTS.md.bak.discord-public-2026-04-27T18-56-39-393Z
/home/openclaw/.openclaw/workspace/AGENTS.md.bak.discord-mentions-2026-04-27T18-59-37-311Z
/home/openclaw/.openclaw/workspace/HEARTBEAT.md.bak.discord-public-2026-04-27T18-56-39-393Z
```

## Recommended Future Maintenance

- Review OpenClaw updates periodically.
- Review Discord allowlist settings after server or channel changes.
- Keep persona files concise and aligned with public-channel use.
- Avoid storing personal profiles of Discord users unless explicitly approved.
- Keep future change records in this documentation folder.
