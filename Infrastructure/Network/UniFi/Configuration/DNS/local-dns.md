# UniFi Local DNS

**Created:** 2026-07-11  
**Last updated:** 2026-07-17

This record inventories local DNS entries owned by the UniFi gateway. Public authoritative DNS remains under the Cloudflare infrastructure records.

## Host Records

| Hostname | Type | Value | TTL | Enabled | Record ID | Purpose |
|---|---|---|---:|---|---|---|
| `REDACTED_CUSTOM_DOMAIN_016` | A | `192.168.85.2` | 300 | Yes | `REDACTED_UNIFI_DNS_RECORD_ID_001` | Internal resolution for the NetBird dashboard through Nginx Proxy Manager on `docker-network` |

## Verification

Created and verified on 2026-07-11:

- The `docker-network` LXC resolved the record through its configured gateway resolver, `192.168.85.1`, and received `192.168.85.2`.
- A Windows Internal-zone client resolved the same A record to `192.168.85.2`.
- [Step S06 screenshot](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg) shows the enabled UniFi record, address, and 300-second TTL.

This local record does not create or modify the public Cloudflare DNS zone.
