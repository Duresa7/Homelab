# UniFi Syslog Export Restored and CIM Coverage Completed

**Created:** 2026-08-29  
**Last updated:** 2026-08-29

**Date:** 2026-08-29  
**Status:** Complete

## Scope

The [UniFi flow collection work on 2026-08-28](UniFi%20Flow%20Collection%20and%20Insights%20App%20-%202026-08-28.md) closed with two products missing. UniFi OS and UniFi Protect had stopped exporting on 2026-07-08 and had sent nothing in the 51 days since, so a third of the console's events were absent from the SIEM and the `unifi_insights` app only knew about UniFi Network's event classes.

This change restores the export, extends the app to all three products, corrects two mistakes in the CIM mapping, and adds the health and camera detection events to a dashboard.

## Restoring the export

The 2026-08-28 record guessed that the Network application update from 9.3.33 to 10.6.101 had reset the category selection. That was wrong, and checking it first is what saved the time. Integrations, System Logging / SIEM Server showed every category still ticked: Network 9 of 9, UniFi OS 5 of 5, Protect 5 of 5.

The destination was what had gone. The SIEM Server address field was empty and the port read 514. Port 514 would have failed on its own: SC4S listens for CEF on 1514, 514 is its generic non-CEF listener, and the firewall on `splunk-siem` only opens 1514/tcp and 1514/udp. Re-entering `192.168.1.60` on port 1514 restored it.

Include Raw Logs stays off. It sends the console's own service logs beside the CEF stream; they are not CEF, so they miss the app's parsing entirely, and they are most of the volume.

Verified over 90 days, before and after:

| Product | Last event on 2026-08-28 | Last event on 2026-08-29 |
| --- | --- | --- |
| `UniFi Network` | 1:34 PM, 2026-08-28 | 2:34 AM, 2026-08-29 |
| `UniFi OS` | 9:34 PM, 2026-07-08 | 2:28 AM, 2026-08-29 |
| `UniFi Protect` | 9:23 PM, 2026-07-08 | 2:31 AM, 2026-08-29 |

All three arrive at sourcetype `cef`, which is what confirms they reached the CEF listener rather than the generic one.

## The parsing fault that hid the restoration

After the export came back, UniFi OS events were indexing but carried no `cef_name`, `cef_product` or `cef_severity`. That reads like a delivery problem and is not one.

UniFi Network and UniFi Protect begin the line at `CEF:0|`. UniFi OS puts a truncated ISO date first, in the shape `YYYY-MM-DDTHH:`, on all 477 of its events. The header extraction was anchored with `^CEF:`, so it matched two products and silently skipped the third. Removing the anchor fixed it, and UniFi Network showed no regression from the change. Detail and a redacted sample are in the [CEF reference](../UniFi-CEF-Reference.md#unifi-os-prefixes-a-partial-timestamp-before-the-cef-header).

## Extending the app to all three products

The three products use separate class ranges that do not overlap, so the event types stayed grouped by meaning rather than splitting by product. What changed:

| Event type | Added |
| --- | --- |
| `unifi_cef_admin_auth` | 1000 UniFi OS console access, 2008 Protect access |
| `unifi_cef_config_change` | 510, 578 device and network updated, 1005 UniFi OS config change, 1103 backup created, 2163 codec change, 2305 video deleted, 2308 Protect admin activity |
| `unifi_cef_session_start` | 2168 camera connected |
| `unifi_cef_session_end` | 2150 camera disconnect |
| `unifi_cef_device_alert` | New. 100, 107, 112, 113 internet health, 414 power cycle, 512, 513 device offline and back, 528, 530 channel change, 539 address conflict |
| `unifi_protect_detection` | New. 2159 motion, 2161 the four smart detections |

`unifi_cef_device_alert` is the part of UniFi's own Insights that neither the flow records nor the threat events cover: an outage, a flapping uplink, a duplicate address.

One class stays deliberately untyped. UniFi OS class 1 is the Send Test Event button's own event. It carries no subject, and typing it would put a test into a data model as a real event. It is the only untyped class left out of 41.

## Two corrections to the CIM mapping

**IDS detections were being counted as network traffic.** `unifi_cef_firewall` was defined as `UNIFIcategory=Security`, and that category covers classes 200, 201 and 203, not just 203. Tagging it `network` and `communicate` therefore put 11,819 IDS detections into Network_Traffic alongside the 25 real firewall blocks, where every detection would have been counted a second time as a connection. The event type is now `sc4s_class=203`.

**Every non-threat event was severity `informational`.** The severity mapping read `UNIFIrisk`, which only the threat classes carry. The CEF header severity is the grading UniFi puts on everything else and it is meaningful, so it is now the fallback:

| Event | CEF severity | CIM severity |
| --- | ---: | --- |
| Internet Down | 10 | critical |
| Device IP Address Conflict, Device Offline | 8 | high |
| Device Power Cycled, Internet Restored | 6 | medium |
| High Latency Detected, Packet Loss Detected | 4 | low |
| AP Channel Change | 2 | informational |

`UNIFIrisk` still wins where it exists, so nothing about the threat events changed.

The Alerts data model also wanted a subject, a body and a type. None of the other five models this sourcetype feeds read those three names, so setting them for every CEF event costs nothing and populates Alerts.

## Dashboard

The client activity dashboard gained a **Network health and camera detections** section: health events by type, camera detections by type, and a table of both with the graded severity. That closes the 2026-08-28 open item about Protect events not being on any dashboard.

The dashboards are generated, so the change was made in [build_unifi_dashboards.py](../../Scripts/build_unifi_dashboards.py) rather than in the view XML.

## Verification

Every check below ran against the live instance after the app was redeployed, the knowledge objects reloaded and `Splunkd` restarted.

The checks are not one-off. They are [Tests/verify_unifi_insights.py](../../Tests/verify_unifi_insights.py), which reads the deployed views and `savedsearches.conf` off disk and runs whatever it finds, so it does not go stale when a panel is added. It takes its credentials from a netrc file so the password never reaches a command line or a process listing, and it writes nothing. Its final line on this run was `PASS: every check ran without error`.

**Dashboard panels.** 39 of 39 panel queries ran without error and 39 returned rows. The three new panels are included in that count.

**Correlation searches.** All eight ran clean over their production windows. Because a quiet hour proves only that they do not fail, each was also run over 60 days of history: seven matched real data, at 31, 8, 6, 12, 1, 1 and 8 results. The eighth, P2P activity from a new host, correctly returned nothing, which is what it is built to do while the torrent traffic stays on the host it has always been on.

**CIM data models**, over 24 hours:

| Data model | Result |
| --- | --- |
| Network_Traffic | 182,492 allowed, 60 blocked, all `Ubiquiti UniFi Network`, no IDS events |
| Intrusion_Detection | 321 high, 37 medium |
| Authentication | UniFi console access on both Network and UniFi OS |
| Network_Sessions | 16 session starts, 25 session ends |
| Change | UniFi configuration changes attributed to a named administrator |
| Alerts | Device Offline at high, camera detections graded low to high |

**Event type coverage.** One class out of 41 is untyped over 60 days, and it is UniFi OS class 1, the test event, by design.

**Notables reach Incident Review.** The scheduler ran the eight rules 150 times in 24 hours with `status=success` on every execution and no failures. Seven notables are in `index=notable`: three from the intrusion rule at medium, two from the Tor rule at low, two from the configuration rule at informational. That is the last link in the chain, and running clean in an ad-hoc search would not have proved it.

**Services and capacity.** `unifi-flow-collector`, `Splunkd` and `sc4s` are all active and enabled. The collector's last six polls read `fetched=865 new=261`, `814/205`, `817/250`, `830/235`, `900/301`, `941/265`, so the overlap window and the deduplication are both still working. Disk is 25 GB free of 70 GB.

`netfw` holds 182,210 events in 43 MB after roughly fourteen hours, which is about 74 MB a day on disk. Against the 10240 MB cap that is 139 days, so the size cap is still what rolls the index first, ahead of the 180-day age cap.

## Cross-checked against published practice

Neither Splunkbase nor SC4S covers this. SC4S's Ubiquiti page defines `ubnt`, `ubnt:fw`, `ubnt:threat`, `ubnt:switch` and `ubnt:wireless` for the legacy BSD syslog format the USG and EdgeRouter emit, and says nothing about the CEF export, CIM mapping or the whitespace fault. Its one recommendation this deployment does follow is the index split, `netops` for events and `netfw` for traffic.

The Unifi Cloud Add-on for Splunk collects devices, hosts and sites from the cloud API. It has no traffic flows, no CIM mapping, and supports Splunk 9.1 to 9.4 where this instance is on 10.4.0.

The community add-ons on GitHub target the same legacy BSD format as SC4S. So there is no existing CIM-compliant add-on for UniFi's CEF export or for the traffic flow records, which is why this app exists rather than a Splunkbase install.

## What remains open

- `ips_category` reaches Splunk on the flow records and no dashboard uses it yet. It is still the cleanest way to break high-risk flows down by reason.
- `netfw` has not reached its size cap, so the first bucket roll is unobserved.
- `_internal` is 8.7 GB against a 30-day retention and is the largest index on the host. It is not a problem at 25 GB free, but it is the first thing to look at if disk gets tight.
- Risk-based alerting and the asset and identity framework are untouched. Notables land in Incident Review as individual events rather than accumulating risk against a host.
- The remaining data-source work in [TODO.md](../TODO.md) is unchanged: the Rocky host's own OS logs, and Proxmox host logs.

## Related

- [UniFi Flow Collection and Insights App](UniFi%20Flow%20Collection%20and%20Insights%20App%20-%202026-08-28.md), the change this continues
- [UniFi CEF Reference](../UniFi-CEF-Reference.md) for the class tables, the timestamp prefix and the whitespace fault
- [Build-Log.md](../Build-Log.md) for the original SC4S and HEC setup
