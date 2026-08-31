# UniFi Flow Collection and Insights App

**Created:** 2026-08-28  
**Last updated:** 2026-08-29

**Date:** 2026-08-28  
**Status:** Complete

## Scope

I wanted the same view in Splunk that UniFi gives me under Insights: which connections were allowed and which were blocked, how the gateway rated them, which policy stopped them, and where the other end was.

The syslog export already in place does not carry that. It sends events: threat detections, client connect and disconnect, admin activity. The per-connection records behind Insights come from the controller's private v2 API and were not in Splunk at all. So this change adds a collector for that API, repairs a parsing fault in the syslog data that was already arriving, maps both sources onto the Common Information Model, and builds three dashboards and eight correlation searches over the result.

## What the two sources hold

`netops` receives CEF over syslog through SC4S and held 19,849 events at the start of the day. Its useful classes are 200 and 201 (threat detected, and detected and blocked), 203 (blocked by firewall), 400, 401, 403 and 404 (client connect and disconnect, wireless and wired), 520 and 521 (VPN), 544 (console access) and 545 through 549 (configuration changes).

`netfw` is new to this change and receives the flow records. Each one carries source and destination address, port, MAC, name, network, subnet and zone, the destination's resolved domains and region, the action, the risk band, the service, the protocol, byte and packet counts in both directions, and the list of policies that matched.

I measured the rate before building anything: 1,652 flows in a ten-minute window, and the controller's own summary reported 391,220 flows for the preceding day, of which 381,145 were allowed at low risk, 9,909 allowed at high risk, 46 allowed at medium, and 120 blocked. That is roughly 175 MB a day of raw JSON against a 10.74 GB daily licence, so the licence is not the constraint. Free disk is: 25 GB of 70 GB.

## Retention

Because a full disk would take the SIEM down and there are no backups to restore from, I capped both indexes before turning the collector on.

| Index | Size cap | Age cap |
| --- | --- | --- |
| `netfw` | 10240 MB | 15552000 s (180 days) |
| `netops` | 2048 MB | 31536000 s (365 days) |

Whichever limit is reached first rolls the oldest buckets out. At the measured rate `netfw` reaches its size cap before its age cap.

## The collector

`unifi_flow_collector.py` runs as `unifi-flow-collector.service` on `splunk-siem`. It authenticates to the controller at `192.168.1.1` with the existing `unifi-mcp` local account, posts to `/proxy/network/v2/api/site/default/traffic-flows`, and writes the results to HEC on `127.0.0.1:8088` with sourcetype `unifi:flow` into `netfw`.

It polls every 120 seconds over a window that reaches 300 seconds behind the last flow it saw, so a record that lands late is still picked up, and it drops repeats by flow id. State is a checkpoint file under `/var/lib/unifi-flow-collector/`, so a restart does not re-ingest or lose a window. Credentials sit in `/etc/unifi-flow-collector/env`, mode 600 and root-owned; the HEC token is also in the password manager as `Splunk HEC Token - unifi-flows`.

The script emits Common Information Model field names where the meaning matches, which is most of them. UniFi's own `allowed` and `blocked` are already the CIM action vocabulary, so those pass through unchanged.

One field needed a second pass. The controller returns an `ips_category` on a policy when an IPS signature is what classified the flow, and that is the only place the reason for a high risk band is stated. My first version dropped it. Corrected before the service was left running.

## The CEF parsing fault

CEF extension parsing splits `key=value` pairs on whitespace, so every UniFi value containing a space was being truncated at the first one. `UNIFIipsSignature=ET TOR Known Tor Exit Node Traffic group 25` was reaching Splunk as `ET`. The same fault hit device names, client aliases, policy names and interface names.

The practical effect was that the entire threat dataset had two distinct signature values, `ET` and `GPL`, and was useless for telling one detection from another.

I fixed it at search time rather than changing SC4S, because a search-time extraction is reversible and does not risk the ingest path. The extractions in `props.conf` re-read each value from `_raw` up to the next CEF key and write to new field names, so they never collide with the truncated automatic extraction they replace.

Before and after, over 60 days:

| Field | Before | After |
| --- | --- | --- |
| Signature | 2 values (`ET`, `GPL`) | 41 values, longest `ET TOR Known Tor Relay/Router (Not Exit) Node Traffic group 705` |
| Policy name | truncated at first word | `P2P` 10,849, `TOR` 361, `Scanning Activity` 138, `DNS` 64, `Web Infrastructure Servers` 45, `CINS Army Reputation List` 17, `Malicious User Agents` 1 |
| Device name | truncated at first word | `Ahsoka Gateway` 19,000, `Jango Switch` 3, `Anakin AP` 2, `Bane Switch POE` 2 |

The CEF header also carries the event name, which SC4S leaves in `_raw`. An extraction now pulls it into `cef_name`, giving readable values such as `Threat Detected` and `WiFi Client Disconnected` instead of the numeric class alone.

## The app

`unifi_insights` version 1.0.0 is installed at `/opt/splunk/etc/apps/unifi_insights` and tracked in this repository under [Configuration/unifi_insights](../../Configuration/unifi_insights). It holds the field mapping above, seven event types with CIM tags, five macros, eight correlation searches, and three dashboards.

The dashboards are Dashboard Studio views on a dark theme. Colours come from a palette I checked with the data-visualisation validator against the dark surface: the eight categorical hues pass the colourblind separation, normal-vision and contrast gates, and risk and action use the reserved status colours so a severity can never be mistaken for a series.

| Dashboard | What it answers |
| --- | --- |
| UniFi Flow Insights | Total, blocked, high risk, countries reached and volume; flow rate over time split by disposition; a world map of destinations; the risk mix; busiest clients, top external destinations and services by volume; the blocked-flow table; the zone-to-zone matrix and top destination domains |
| UniFi Threat Center | Detected, blocked, passed through, unique signatures and firewall blocks; detections over time banded by risk; signatures by frequency and threat categories; a map of where blocked traffic originates; blocking policies; recent detections |
| UniFi Client & Network Activity | Active clients, connects, disconnects, configuration changes and admin logins; the session timeline; clients and networks by volume; the WiFi split; admin activity and client session tables |

Two build details are worth recording because they are not obvious. `splunk.choropleth.svg` is not registered on this instance and renders `Missing property: svg`, so geography is drawn with `splunk.map` over `iplocation` coordinates instead. And `seriesColors` binds by position, so a series absent from the time window shifts every colour after it; the timecharts and the risk donut therefore emit fixed, named columns rather than splitting by a field whose values come and go.

## Correlation searches

Eight rules are scheduled, each writing notables. They are offset across the hour so they do not contend for search slots.

| Rule | Cron | Severity |
| --- | --- | --- |
| Intrusion detection not blocked | `12 * * * *` | medium |
| Threat reputation or malicious user agent match | `17 * * * *` | high |
| Outbound scanning activity | `22 * * * *` | high |
| Tor network traffic | `27 * * * *` | low |
| Blocked inbound flow spike from a single source | `*/15 * * * *` | medium |
| Controller configuration changed | `32 * * * *` | informational |
| Admin console access from an unexpected network | `37 * * * *` | medium |
| P2P signature activity from a new host | `42 * * * *` | low |

Three of them are tuned against what this network actually does, and the tuning is the reason the queue will be readable:

- 10,849 of the 11,477 detections on record are the P2P signature set firing on this network's own BitTorrent traffic. Alerting on UniFi's high-risk band as-is would make the notable queue about 95 percent torrent noise, so the threat rules exclude `P2P` by name. The last rule covers the gap: it fires only when P2P detections appear from a host that had none in the preceding week.
- The built-in `Unifi` and `Network` service accounts made 534 of the 767 configuration changes on record. Those are the controller acting on its own, so the configuration rule excludes them and reports changes made by a person.
- `ansible-01` produces scan signatures because probing managed hosts is its job, so the scanning rule excludes it. Remove that exclusion if the control node itself is ever in question.

## Verification

The collector's first run wrote 2,297 flows covering a 900-second window, and all 2,297 were present in `netfw` with distinct flow ids and timestamps spread correctly across that window. Steady state at 1:37 PM was `fetched=1268 new=261 written=261`, which shows the overlap and the deduplication both working: the poll retrieved 1,268 records and recognised 1,007 of them as already seen.

At 1:37 PM the service was `active` and `enabled`, and the checkpoint held 6,870 flow ids.

I ran every one of the 36 dashboard panel queries against live data. All 36 returned without error and 36 returned rows.

I ran all eight correlation searches over their production windows: all eight completed without error. Because a quiet hour proves only that they do not fail, I also ran each rule's logic over 60 days of history to confirm it matches real data. Each one did, including the reputation rule on `CINS Army Reputation List` and `Malicious User Agents`, and the console-access rule on four addresses outside the management networks.

The CIM data models return the data:

| Data model | Result |
| --- | --- |
| Network_Traffic | 6,875 allowed and 4 blocked, `vendor_product` `Ubiquiti UniFi Network` |
| Intrusion_Detection | 10,849 high, 635 medium, 2 informational |
| Authentication | UniFi console access resolving to the administrator's username |

Splunk Web is firewalled from my workstation, so rather than skip the visual check I rendered each dashboard server-side through `/services/pdfgen/render` and read the output. That caught four faults a query test cannot see: the broken choropleth, an unescaped `&` that silently truncated one dashboard's label to its view name, a donut that merged the high and medium bands into an "Other" slice and handed their colours to the wrong band, and raw CEF field names showing as truncated column headers. All four are fixed and re-rendered.

I have not committed the renders. They contain the WAN address and client MAC addresses.

## What remains open

- The flow records carry `ips_category` now, but no dashboard uses it yet. It is the cleanest way to break high-risk flows down by reason.
- `netfw` retention is capped by size at 10240 MB. I have not yet watched it reach the cap, so the first roll is unobserved.
- Risk-based alerting and the asset and identity framework are still untouched. The notables land in Incident Review as individual events rather than accumulating risk against a host.
- The remaining data-source work in [TODO.md](../TODO.md) is unchanged: the Rocky host's own OS logs, and Proxmox host logs.
- UniFi Protect events (classes 2008, 2161, 2305 and 2308) sit in `netops` and are not on any dashboard. That is secondary to the next point. **Closed on 2026-08-29.**
- **The UniFi OS and UniFi Protect syslog exports are dead.** Checking product coverage at the end of this work showed both stopped on 2026-07-08, eleven minutes apart, and have sent nothing in the 51 days since; `UniFi Network` has run without a gap. The Network application has gone from 9.3.33 to 10.6.101 in that window, so an update resetting the category selection is the likely cause. It is a UniFi OS setting and not reachable through the Network API, so it needs the console UI. **Closed on 2026-08-29, and the cause above was wrong: the categories were all still selected and the export destination had been cleared.** See [UniFi Syslog Export Restored and CIM Coverage Completed](UniFi%20Syslog%20Export%20Restored%20and%20CIM%20Coverage%20Completed%20-%202026-08-29.md).

## Related

- [UniFi Syslog Export Restored and CIM Coverage Completed](UniFi%20Syslog%20Export%20Restored%20and%20CIM%20Coverage%20Completed%20-%202026-08-29.md), which continues this work
- [UniFi CEF Reference](../UniFi-CEF-Reference.md) for the field mapping and the parsing fault
- [Build-Log.md](../Build-Log.md) for the original SC4S and HEC setup
- [Enterprise Security TODO](../../../Enterprise%20Security/Documentation/TODO.md) for the remaining ES work
