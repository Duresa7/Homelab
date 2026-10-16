# Cloudflare Domains

**Created:** 2026-07-09  
**Last updated:** 2026-10-15

These are the domains I manage through Cloudflare. I last read all four zones back through the API on 2026-09-06; [Account Verification](../Documentation/Change%20Records/Account%20Verification%20-%202026-09-06.md) summarizes what each zone held that day. `duresakadi.me` is paused, so Cloudflare serves its DNS without proxying any of its records. `alphsec.com` has served HSTS with a 180-day max-age and subdomains included since 2026-10-15; [Security Insights review](../Documentation/Change%20Records/Security%20Insights%20Review%20-%202026-10-15.md). Mail posture since the same day: `alphsec.com` and `duresakadi.com` send no mail and publish `v=spf1 -all`, an empty DKIM key and DMARC `p=reject`; `alphasecunited.com` sends through Microsoft 365 and Resend and publishes DMARC `p=none` with reports going to Cloudflare's DMARC Management.

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

## UniFi console names

`duresakadi.com` carries the public name for the UniFi console. Ahsoka Gateway's dynamic DNS maintains the A record with the token `UniFi DDNS`; the [UniFi README](../../UniFi/README.md#dynamic-dns-and-the-console-name) describes the client and how I check it.

| Type | Name | Content | Notes |
|---|---|---|---|
| A | `unifi-ddns.duresakadi.com` | `<REDACTED_WAN_IP>` | Created by hand at 9:27:44 AM Eastern on 2026-08-13. Dynamic DNS first updated it at 6:29:26 PM on 2026-10-13 ([incident](../../../../Security/Incidents/UniFi/Dynamic%20DNS%20Never%20Updated%20the%20Console%20Name%20-%202026-10-13.md)) |
| CNAME | `unifi.duresakadi.com` | `unifi-ddns.duresakadi.com` | DNS only. Created at 10:11 AM Eastern on 2026-08-13 |

At 8:58:14 AM Eastern on 2026-10-15 I deleted a stale TXT record, `_acme-challenge.unifi.duresakadi.com`. UniFi's certificate manager on Ahsoka Gateway wrote it at 3:49:32 AM on 2026-10-13 for that day's renewal and did not remove it. Afterwards the two records above were the only `unifi` records in the zone. After the next renewal I'll check whether the certificate manager leaves another one behind ([open item](../Documentation/Change%20Records/UniFi%20DDNS%20Token%20Separation%20-%202026-10-13.md#open)).
