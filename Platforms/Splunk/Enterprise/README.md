# Splunk Enterprise

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

I run Splunk Enterprise 10.4.0 (build `f798d4d49089`) on VM 109 `splunk-siem`, Rocky Linux 10.2, at `192.168.72.3` on Security-A, VLAN 72. It indexes UniFi CEF syslog, UniFi traffic flows and Wazuh alerts, and posts nine security searches to Discord. The figures below were read on 2026-09-24.

| Item | Value |
|---|---|
| Host | VM 109 on `grey-server`, 6 vCPU, 12 GiB, 150 GiB on `ssd-lvm1` ([VM Specs](Documentation/VM%20Specs.md)) |
| Web | `https://splunk.alphasecunited.com` through Nginx Proxy Manager; Splunk Web on 8000, splunkd management on 8089 |
| Inputs | SC4S (podman, `container3:latest`) on 1514 for UniFi CEF into `netops`; HEC on 8088 for SC4S and the flow collector; splunktcp on 9997 for the Wazuh Universal Forwarder |
| Indexes in use | `netops` (UniFi CEF), `netfw` (UniFi traffic flows), `wazuh` (Wazuh alerts, 30 days) |
| Flow collector | `unifi-flow-collector.service` runs [unifi_flow_collector.py](Scripts/unifi_flow_collector.py) from `/opt/unifi-flow-collector` and polls the controller's Traffic Flows API |
| My apps | [unifi_insights](Configuration/unifi_insights/) (CIM mapping, three dashboards, 11 saved searches) and [wazuh_insights](Configuration/wazuh_insights/) (dashboard, 5 saved searches), among 65 installed apps |
| Discord | Nine saved searches (five UniFi, four Wazuh) post through the webhook action to the [Discord Alert Bot](../../Discord%20Alert%20Bot/README.md) at `http://192.168.73.2:8080/splunk` |
| Premium app | [Enterprise Security](../Enterprise%20Security/README.md) 8.5.1 on the same instance |

## UniFi data

Two pipelines bring UniFi data in, and they carry different things.

SC4S runs on the same host and receives CEF syslog from the console on port 1514, landing in `netops`. Three products export to it: UniFi Network, UniFi OS and UniFi Protect. That carries events: threat detections with their IPS signature, client connect and disconnect, VPN sessions, admin activity, internet and device health, and camera detections. The field mapping it depends on, including a space-truncation fault and its repair, is in the [UniFi CEF reference](Documentation/UniFi%20CEF%20Reference.md).

`unifi-flow-collector.service` polls the controller's Traffic Flows API and writes to `netfw` through HEC. That carries the per-connection records behind the Insights view: action, risk band, matched policy, byte and packet counts, and the destination's domain and region. The script is [unifi_flow_collector.py](Scripts/unifi_flow_collector.py) and its unit is [in Configuration](Configuration/systemd/unifi-flow-collector.service).

The [unifi_insights](Configuration/unifi_insights) app sits over both. It holds the CIM mapping that populates six ES data models, three Dashboard Studio views, and 11 saved searches: the eight correlation searches from 2026-08-28 and three webhook-only searches added on 2026-09-03. The build is recorded in [UniFi Flow Collection and Insights App - 2026-08-28](Documentation/Change%20Records/UniFi%20Flow%20Collection%20and%20Insights%20App%20-%202026-08-28.md), and the follow-up that restored the UniFi OS and Protect exports and extended the mapping to them is in [UniFi Syslog Export Restored and CIM Coverage Completed - 2026-08-29](Documentation/Change%20Records/UniFi%20Syslog%20Export%20Restored%20and%20CIM%20Coverage%20Completed%20-%202026-08-29.md). On 2026-09-12 I dropped `ubuntu-dev` from the scanning exclusion in `UniFi - Intrusion detection blocked`, where it had been listed by address and so had never matched, in [UniFi Scan Exclusion Correction - 2026-09-12](Documentation/Change%20Records/UniFi%20Scan%20Exclusion%20Correction%20-%202026-09-12.md).

Wazuh alerts arrive from the Universal Forwarder on `security-01` into `wazuh`, and the `wazuh_insights` app puts them on one page; see [Alert Forwarding to Splunk - 2026-08-29](../../Wazuh/Documentation/Change%20Records/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29.md) and [Wazuh Insights App - 2026-08-29](Documentation/Change%20Records/Wazuh%20Insights%20App%20-%202026-08-29.md).

## Records

- [Build Log](Documentation/Build%20Log.md): the 2026-06-28 VM, OS, Splunk and SC4S build
- [VM Specs](Documentation/VM%20Specs.md)
- [UniFi CEF Reference](Documentation/UniFi%20CEF%20Reference.md): field mapping and the space-truncation repair
- [TODO](Documentation/TODO.md)
- [Troubleshooting](Documentation/Troubleshooting/README.md)
- Change records:
  - [UniFi Flow Collection and Insights App - 2026-08-28](Documentation/Change%20Records/UniFi%20Flow%20Collection%20and%20Insights%20App%20-%202026-08-28.md)
  - [Root Filesystem Expansion - 2026-08-29](Documentation/Change%20Records/Root%20Filesystem%20Expansion%20-%202026-08-29.md)
  - [UniFi Syslog Export Restored and CIM Coverage Completed - 2026-08-29](Documentation/Change%20Records/UniFi%20Syslog%20Export%20Restored%20and%20CIM%20Coverage%20Completed%20-%202026-08-29.md)
  - [Wazuh Insights App - 2026-08-29](Documentation/Change%20Records/Wazuh%20Insights%20App%20-%202026-08-29.md)
  - [Discord Delivery for UniFi and Wazuh Alerts - 2026-09-03](Documentation/Change%20Records/Discord%20Delivery%20for%20UniFi%20and%20Wazuh%20Alerts%20-%202026-09-03.md)
  - [UniFi Scan Exclusion Correction - 2026-09-12](Documentation/Change%20Records/UniFi%20Scan%20Exclusion%20Correction%20-%202026-09-12.md)
