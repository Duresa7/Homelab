# Cloudflare Domains

**Created:** 2026-07-09  
**Last updated:** 2026-10-09

These are the domains I manage through Cloudflare. I last read all four zones back through the API on 2026-09-06; [Account Verification](../Documentation/Change%20Records/Account%20Verification%20-%202026-09-06.md) summarizes what each zone held that day. `duresakadi.me` is paused, so Cloudflare serves its DNS without proxying any of its records.

| Domain |
| --- |
| `alphasecunited.com` |
| `alphsec.com` |
| `duresakadi.com` |
| `duresakadi.me` |

## Minecraft publication

I deleted the Minecraft CNAME and SRV on 2026-09-12 when I retired Game 01. At 3:25 PM Eastern on 2026-10-09, I queried the live zone for names containing `minecraft` and for `*.alphasecunited.com`; both requests succeeded with zero records. I changed no records during that check and did not retain a separate evidence export for it. At 5:01 PM Eastern I restored the Minecraft names for the [new server](../../../../Platforms/Minecraft/README.md), using the retained Playit allocation.

| Type | Name | Target | Port | TTL | Proxy |
|---|---|---|---|---:|---|
| CNAME | `minecraft.alphasecunited.com` | `<REDACTED_MINECRAFT_RELAY>` | | 300 seconds | DNS only |
| SRV | `_minecraft._tcp.minecraft.alphasecunited.com` | `<REDACTED_MINECRAFT_SRV_TARGET>` | `<REDACTED_RELAY_PORT>` | 300 seconds | DNS only |

The SRV priority and weight are 0. API readback matched both records, and 1.1.1.1 and 8.8.8.8 resolved them. The SRV connection and login transport reached Minecraft 26.3; Playit still rejects the entered custom hostname in the separate server-list ping. The [publication record](../../../../Platforms/Minecraft/Documentation/Change%20Records/DNS%20Publication%20-%202026-10-09.md) holds the verification and limitation. The former relay configuration remains in the [archived platform](../../../../Archive/Platforms/Game%20Servers/README.md).
