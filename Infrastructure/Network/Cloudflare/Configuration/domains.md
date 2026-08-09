# Cloudflare Domains

**Created:** 2026-07-09  
**Last updated:** 2026-08-09

These are the domains I manage through Cloudflare.

| Domain |
| --- |
| `alphasecunited.com` |
| `alphsec.com` |
| `duresakadi.com` |
| `duresakadi.me` |

## Public service records

| Zone | Type | Name | Value | TTL | Proxy |
| --- | --- | --- | --- | --- | --- |
| `alphasecunited.com` | CNAME | `minecraft.alphasecunited.com` | `<REDACTED_MINECRAFT_RELAY_HOST>` | 300 | DNS-only |
| `alphasecunited.com` | SRV | `_minecraft._tcp.minecraft.alphasecunited.com` | priority 1, weight 1, port 26328, target `<REDACTED_MINECRAFT_RELAY_HOST>` | 300 | n/a |

The relay target is withheld from this public repository. These records publish only the Minecraft path; the Pelican panel and Wings API are not part of the Playit tunnel. [Better Realism MC and Playit Publication - 2026-08-09](../../../../Platforms/Game%20Servers/Documentation/Change%20Records/Better%20Realism%20MC%20and%20Playit%20Publication%20-%202026-08-09.md) records the initial publication. [Better Realism Shutdown and Vanilla Minecraft Deployment - 2026-08-09](../../../../Platforms/Game%20Servers/Documentation/Change%20Records/Better%20Realism%20Shutdown%20and%20Vanilla%20Minecraft%20Deployment%20-%202026-08-09.md) records the current Vanilla backend and its verification.
