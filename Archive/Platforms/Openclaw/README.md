# OpenClaw

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

Retired. I ran OpenClaw 2026.4.25 as a Discord assistant on Galaxy CT 104 `ai-alpha-01` (grey-server, `192.168.40.37`, VLAN 40). The guest was already gone from Galaxy when I checked the cluster on 2026-07-25; I did not keep the exact deletion date.

| Fact | Recorded value |
|---|---|
| Guest | LXC 104 `ai-alpha-01`, 2 vCPU, 4 GiB memory, 40 GiB `ssd-lvm1` root volume |
| Service | `openclaw-gateway.service`, user service under `openclaw`, bound to `127.0.0.1:18789` |
| Discord scope | One guild, one channel (`#alpha-ai`), mention required, direct messages off |
| Last change | 2026-04-27, upgrade from 2026.4.15 to 2026.4.25 |

## Records

- [Setup overview](Documentation/OpenClaw-Setup-Overview.md): the captured configuration, system prompt, and channel rules as of 2026-04-27.
- [Change record, 2026-04-27](Documentation/OpenClaw-Change-Record-2026-04-27.md): the upgrade, gateway service, channel allowlist, session reset, and member resolver.
- [Retired guest record](../../Operations/Inventory/Galaxy/AI%20Alpha%2001%20Retired%20Guest%20-%202026-07-25.md): the last recorded CT 104 configuration and the 2026-07-25 absence check.
- [Walkthrough](../../Guides/OpenClaw.md): the archived guide.

The folder keeps its original `Platforms/Openclaw/` spelling so the archived path matches the one the older records cite.
