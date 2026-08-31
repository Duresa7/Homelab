# Detection Mode to Notify and Block

**Created:** 2026-08-31  
**Last updated:** 2026-08-31

## Date

I made this change on 2026-08-31, shortly before the 11:16 AM verification below. I did not note the exact minute.

## Scope

I moved Detection Mode under CyberSecure, Threat Management, on the Ahsoka Gateway from Notify to Notify and Block. A signature match is now dropped rather than alerted and forwarded.

This decides the question [DMZ Added to Threat Management](DMZ%20Added%20to%20Threat%20Management%20-%202026-08-30.md) left open on 2026-08-30.

## This is not DMZ only

Worth stating plainly, because the decision was framed around DMZ. Detection Mode is one gateway-wide control rather than a per-network setting. The 2026-08-30 capture records it as a single value beside a seven-entry Selected Networks list, which is why it is one setting and not seven. Enforcement therefore applies to every inspected network: Trusted, IoT, Personal-A, Secure, Secure Client, MGMT-A and DMZ.

A false positive can now drop traffic on Trusted and MGMT-A, not only on the edge path. That is a wider blast radius than the DMZ framing implies, and it is the part worth watching.

## What changed

| Setting | Before | After |
|---|---|---|
| Detection Mode | Notify | Notify and Block |

Selected Networks, the Active Detections categories, Region Blocking and the honeypot list are unchanged from the 2026-08-30 capture.

## Verification

Checked at 11:16 AM on 2026-08-31. Every check is read-only.

| Check | Result |
|---|---|
| UniFi site health | `wlan`, `wan`, `www`, `lan` and `vpn` all `ok` |
| `edge-01` overall | healthy, up 3 weeks 25 minutes, so it has not restarted |
| `edge-01` load average | 0.00, 0.01, 0.00 |
| `edge-01` memory | 431 MiB used of 3,854 MiB, 11.18 percent |
| `edge-01` root filesystem | 1.9 GiB used of 27 GiB, 8 percent |
| `caddy` | active (running), enabled, PID 746 |
| `cloudflared` | active (running), enabled, PID 747 |
| `unifi_get_ips_events` | 0 events over the daily window and the weekly window |

The externally served path is intact. Both `caddy` and the Cloudflare tunnel client are running on `edge-01`, and the host has not rebooted, so nothing on the one Internet-reachable path went down with the switch.

## What I could not verify

The UniFi Network MCP does not read Detection Mode. I checked every path in the 187-tool index: `unifi_get_gateway_settings` returns only the `usg` settings key and carries no IPS block, `unifi_get_site_settings` returns site identity alone, a search for `threat` and for `ips` returns `unifi_get_ips_events` and nothing else, and no raw passthrough tool exists. The value in the table above is what the Threat Management page shows, which is the same basis the 2026-08-30 record used. I retained no page capture for this change, so it has no Evidence folder.

`unifi_get_ips_events` returning zero is not evidence either way. That tool documents its legacy endpoint as often unpopulated on current UniFi OS and points to Traffic Flows instead.

## The stated precondition was not met

The 2026-08-30 record said the switch should wait until there was a run of signature matches to look at. There is no such run. No IPS event is retrievable over either window, so nothing was reviewed before enforcement went on. I am recording that rather than leaving the earlier reasoning looking satisfied.

## Pre-change baseline

Traffic Flow statistics for the site, read shortly before the change:

| Risk band | Allowed | Blocked |
|---|---:|---:|
| Low | 359,942 | 604 |
| Medium | 133 | 0 |
| High | 649 | 0 |

649 high-risk and 133 medium-risk flows were allowed with no block above the low band, which is what Notify produces. If Notify and Block is doing anything, the high and medium blocked counts should stop being zero. These risk bands are DPI reputation rather than IPS signature verdicts, and the low-band blocks come from firewall and content-filter policy, so this is a baseline to compare against and not an IPS measurement.

## Record updates

- [DMZ Added to Threat Management](DMZ%20Added%20to%20Threat%20Management%20-%202026-08-30.md) keeps its Notify sections as written, because they describe the 2026-08-30 capture and the reasoning that held then, with a line pointing here.
- [TODO.md](../../../../../TODO.md) narrows its Threat Management item to the coverage question.

## Remaining work

- Watch for a false positive on Trusted or MGMT-A, which now drop on a match rather than only alerting.
- Recheck Traffic Flow statistics against the baseline above once a day of traffic has passed, to confirm blocking is happening at all. A high and medium blocked count still at zero would mean the switch changed nothing observable.
- Decide whether SERVERS-A, Security-A, MONITOR-A and Access-A are worth the gateway throughput. Unchanged from 2026-08-30.
