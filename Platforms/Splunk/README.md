# Splunk

**Created:** 2026-08-03  
**Last updated:** 2026-08-29

I run Splunk Enterprise 10.4.0 on `splunk-siem` at `192.168.72.3`, a Rocky Linux VM on the Security-A VLAN. Splunk Enterprise indexes and searches the data. Splunk Enterprise Security is the premium app installed on top of it and supplies the SIEM features.

| Folder | What it covers |
| --- | --- |
| [Enterprise](Enterprise/) | The indexing and search platform, its build log, VM specifications, the UniFi CEF reference, and its backlog |
| [Enterprise Security](Enterprise%20Security/) | The ES app, its configuration log, and its backlog |

Both products share one host and one set of indexes. A change to Splunk Enterprise can affect ES, so a record that touches both belongs with Enterprise and is cross-linked from Enterprise Security rather than written twice.

## UniFi data

Two pipelines bring UniFi data in, and they carry different things.

SC4S runs on the same host and receives CEF syslog from the console on port 1514, landing in `netops`. Three products export to it: UniFi Network, UniFi OS and UniFi Protect. That carries events: threat detections with their IPS signature, client connect and disconnect, VPN sessions, admin activity, internet and device health, and camera detections. The field mapping it depends on, including a space-truncation fault and its repair, is in the [UniFi CEF reference](Enterprise/Documentation/UniFi-CEF-Reference.md).

`unifi-flow-collector.service` polls the controller's Traffic Flows API and writes to `netfw` through HEC. That carries the per-connection records behind the Insights view: action, risk band, matched policy, byte and packet counts, and the destination's domain and region. The script is [unifi_flow_collector.py](Enterprise/Scripts/unifi_flow_collector.py) and its unit is [in Configuration](Enterprise/Configuration/systemd/unifi-flow-collector.service).

The [unifi_insights](Enterprise/Configuration/unifi_insights) app sits over both. It holds the CIM mapping that populates six ES data models, three Dashboard Studio views, and eight correlation searches. The build is recorded in [UniFi Flow Collection and Insights App - 2026-08-28](Enterprise/Documentation/Change%20Records/UniFi%20Flow%20Collection%20and%20Insights%20App%20-%202026-08-28.md), and the follow-up that restored the UniFi OS and Protect exports and extended the mapping to them is in [UniFi Syslog Export Restored and CIM Coverage Completed - 2026-08-29](Enterprise/Documentation/Change%20Records/UniFi%20Syslog%20Export%20Restored%20and%20CIM%20Coverage%20Completed%20-%202026-08-29.md). On 2026-09-12 I dropped `ubuntu-dev` from the scanning exclusion in `UniFi - Intrusion detection blocked`, where it had been listed by address and so had never matched, in [UniFi Scan Exclusion Correction - 2026-09-12](Enterprise/Documentation/Change%20Records/UniFi%20Scan%20Exclusion%20Correction%20-%202026-09-12.md).
