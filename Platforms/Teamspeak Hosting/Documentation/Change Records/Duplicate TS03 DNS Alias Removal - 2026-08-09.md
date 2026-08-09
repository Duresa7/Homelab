# Duplicate TS03 DNS Alias Removal

**Created:** 2026-08-09  
**Last updated:** 2026-08-09

**Date:** 2026-08-09  
**Scope:** Remove the unused second public name for `ts-valorant-03` without changing its TeamSpeak container or Playit tunnel.

## Finding

Cloudflare held two complete DNS pairs for the same TeamSpeak endpoint:

| Role | CNAME | SRV |
|---|---|---|
| Current public address | `ts03.alphasecunited.com` | `_ts3._udp.ts03.alphasecunited.com` |
| Alternate alias | `ts-valorant-03.alphasecunited.com` | `_ts3._udp.ts-valorant-03.alphasecunited.com` |

Both pairs targeted the same Playit relay and UDP port, and both returned a valid TeamSpeak `TS3INIT1` handshake before the change. The living deployment record, platform README, reachability collector, and probe examples all use `ts03` as the current public name. Cloudflare's comments also identified the longer name as an alias.

## Change

I deleted the DNS-only CNAME `ts-valorant-03.alphasecunited.com` and the SRV record `_ts3._udp.ts-valorant-03.alphasecunited.com`. Both Cloudflare delete requests returned HTTP 200.

I did not change `ts03.alphasecunited.com`, `_ts3._udp.ts03.alphasecunited.com`, the `ts-valorant-03` container, UDP port 9989, or the Playit agent.

## Verification

| Check | Observed result |
|---|---|
| Cloudflare exact-name readback | Zero records for the removed alias; one CNAME and one SRV for `ts03` |
| Authoritative DNS | Alias CNAME count 0 and SRV count 0; primary CNAME count 1 and SRV count 1 |
| Public TeamSpeak probe | `ts03.alphasecunited.com` returned a valid `TS3INIT1` reply |
| Voice container | `ts-valorant-03` running |
| Local voice listener | UDP 9989 listening |
| Tunnel agent | `playit-agent` running |

I retained no separate evidence folder. I performed the checks against the live Cloudflare zone, its authoritative DNS, and `alpha-prod-01`, then recorded the observed state here.

## Remaining Work

None. `ts03.alphasecunited.com` is the only public DNS name for TeamSpeak server 03.
