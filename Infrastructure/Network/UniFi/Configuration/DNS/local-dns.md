# UniFi Local DNS

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

I track one local DNS record on the UniFi gateway. Public authoritative DNS stays in the Cloudflare records.

## Host Records

| Hostname | Type | Value | TTL | Enabled | Record ID | Purpose |
|---|---|---|---:|---|---|---|
| `<YOUR_NETBIRD_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `<YOUR_NETBIRD_DNS_RECORD_ID>` | Internal resolution for the NetBird dashboard through Nginx Proxy Manager on `docker-network` |

## Verification

I created and verified the record on 2026-07-11:

- The `docker-network` LXC resolved the record through its configured gateway resolver, `192.168.85.1`, and received `192.168.85.2`.
- A Windows Internal-zone client resolved the same A record to `192.168.85.2`.

![Enabled UniFi internal DNS record showing the address and 300-second TTL](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)

The record exists only on the UniFi resolver. It doesn't change the public Cloudflare zone.
