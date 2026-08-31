# UniFi System Logs / SIEM: CEF Reference

**Created:** 2026-07-01  
**Last updated:** 2026-08-29

I use this reference for the UniFi to SC4S to Splunk pipeline in [Build-Log.md](Build-Log.md#step-6-unifi-log-ingestion-cef-via-sc4s). The format comes from Ubiquiti's *UniFi System Logs & SIEM Integration* documentation.

UniFi's **System Logging / SIEM** integration (Integration → System Logging / SIEM → *SIEM Server*) exports activity logs over syslog in **Common Event Format (CEF)**. I select the exported categories and destination IP/port there.

## CEF header format

```
CEF:Version|Device Vendor|Device Product|Device Version|Device Event Class ID|Name|Severity|[Extension]
```

The `[Extension]` is a space-separated list of `key=value` pairs (the `UNIFI*` keys plus a few standard ones like `src`, `msg`, `suser`).

## Routing nuance: three product strings

SC4S routes by the CEF `device_vendor`_`device_product` key. With all categories exported (Network + UniFi OS + Protect), my deployment emits **three** product values, which I confirmed via `stats count by sc4s_product`:

| CEF `device_product` | Metadata key | Source subsystem |
|---|---|---|
| `UniFi Network` | `Ubiquiti_UniFi Network` | Network application |
| `UniFi OS` | `Ubiquiti_UniFi OS` | Console OS |
| `UniFi Protect` | `Ubiquiti_UniFi Protect` | Protect (cameras / NVR) |

To make sure **all three** land in `netops`, `/opt/sc4s/local/context/splunk_metadata.csv` should contain:

```csv
Ubiquiti_UniFi OS,index,netops
Ubiquiti_UniFi Network,index,netops
Ubiquiti_UniFi Protect,index,netops
```

I can separate Protect camera events later by pointing `Ubiquiti_UniFi Protect` at a different index.

Restart SC4S after editing (`sudo systemctl restart sc4s`). If UniFi events ever fall back to `main`, check the actual `device_product` string and add the matching key.

## The UniFi OS and Protect exports stopped on 2026-07-08 and came back on 2026-08-29

The routing table above expects three `device_product` values. For 51 days only one was arriving. Measured on 2026-08-28 over 90 days:

| Product | Events | First seen | Last seen |
| --- | ---: | --- | --- |
| `UniFi Network` | 18,568 | 2026-07-01 8:28 PM | 2026-08-28 1:34 PM |
| `UniFi OS` | 460 | 2026-06-30 1:46 PM | 2026-07-08 9:34 PM |
| `UniFi Protect` | 842 | 2026-07-01 8:12 PM | 2026-07-08 9:23 PM |

UniFi OS and UniFi Protect stopped within eleven minutes of each other and sent nothing afterwards, while UniFi Network ran without a gap. SC4S stayed up and kept accepting Network events on the same port throughout, so the transport was never the problem.

My first guess was that the Network application update from 9.3.33 to 10.6.101 had reset the category selection. That was wrong. Opening Integrations, System Logging / SIEM Server showed every category still ticked: Network 9 of 9, UniFi OS 5 of 5, Protect 5 of 5. The destination was what had gone: the SIEM Server address field was empty and the port read 514.

Port 514 matters as much as the empty address. SC4S listens for CEF on **1514**, and 514 is its generic non-CEF listener, so an export pointed at 514 does not reach the `cef` sourcetype even when it arrives. The firewall on `splunk-siem` allows 1514/tcp and 1514/udp for this reason.

Re-entering the destination as `192.168.1.60` on port 1514 restored it. Measured on 2026-08-29 over 90 days:

| Product | Events | First seen | Last seen |
| --- | ---: | --- | --- |
| `UniFi Network` | 18,942 | 2026-07-01 8:28 PM | 2026-08-29 2:34 AM |
| `UniFi OS` | 477 | 2026-06-30 1:46 PM | 2026-08-29 2:28 AM |
| `UniFi Protect` | 954 | 2026-07-01 8:12 PM | 2026-08-29 2:31 AM |

All three arrive at sourcetype `cef`, which is the confirmation that they reached the CEF listener rather than the generic one. The check:

```spl
index=netops sourcetype=cef earliest=-1h | stats count by sc4s_product
```

`splunk_metadata.csv` already routed all three to `netops`, so nothing changed on the SC4S side.

**Include Raw Logs stays off.** It sends the console's own service logs alongside the CEF stream. They are not CEF, so they miss the parsing above, and they are the bulk of the volume.

## UniFi OS prefixes a partial timestamp before the CEF header

UniFi Network and UniFi Protect start the line at `CEF:0|`. UniFi OS does not. Every one of its 477 events carries a truncated ISO date first, in the shape `YYYY-MM-DDTHH:`, with the minutes and seconds already consumed by the syslog parser:

```
2026-08-28T17:CEF:0|Ubiquiti|UniFi OS|5.1.31|1005|Admin Made Config Changes|2|UNIFIhost=Host UNIFIdeviceName=Ahsoka Gateway UNIFIdeviceModel=UCGF UNIFIdeviceIp=<REDACTED_WAN_IP> UNIFIdeviceMac=<REDACTED_GATEWAY_MAC> UNIFIdeviceVersion=5.1.31 msg=Duresa Kadi changed Syslog Settings Mode setting from "internal" to "external". Source IP: 192.168.50.241
```

A header extraction anchored with `^CEF:` therefore matches Network and Protect and silently skips UniFi OS. The app's `EXTRACT-cef_header` is deliberately unanchored. This cost a debugging pass on 2026-08-29: UniFi OS events were arriving and indexing correctly but carried no `cef_name`, `cef_product` or `cef_severity`, which reads exactly like a delivery problem rather than a parsing one.

The sample also shows why the rendered dashboards are not committed. UniFi OS puts `UNIFIdeviceIp` and `UNIFIdeviceMac` on every event, and on this console those are the WAN address and the gateway's MAC.

## Product versions seen

| Product | Versions in 60 days to 2026-08-29 |
| --- | --- |
| UniFi Network | 10.4.57, 10.5.67, 10.6.97, 10.6.101 |
| UniFi OS | 5.1.19, 5.1.31 |
| UniFi Protect | 7.1.83, 7.2.105 |

## Log categories

| Category | Types | Example events |
|---|---|---|
| Monitoring | Guest Hotspot, WiFi, Wired, Status | Client Connected/Disconnected, WiFi Client Roaming |
| Internet | Outage & Failover, Performance | WAN Failover, High Latency, Packet Loss |
| Power | PoE, Redundancy | Insufficient PoE Output, AP Underpowered |
| Security | Firewall, Honeypot, Intrusion Prevention | Threat Detected and Blocked, Honeypot Triggered, Blocked by Firewall |
| System | Admin Activity, Devices, Network, VPN, WiFi, Wired | Admin Made Config Changes, Device Adopted, Device Offline |

## Example events

**Admin Accessed UniFi Network**

```
CEF:0|Ubiquiti|UniFi Network|9.3.33|544|Admin Accessed UniFi Network|1|UNIFIcategory=System UNIFIsubCategory=Admin UNIFIhost=Office UDM Pro UNIFIaccessMethod=web UNIFIadmin=Craig src=<REDACTED_CLIENT_IP> msg=Craig accessed UniFi Network using the web. Source IP: <REDACTED_CLIENT_IP>
```

**WiFi Client Disconnected**

```
CEF:0|Ubiquiti|UniFi Network|9.3.33|401|WiFi Client Disconnected|2|UNIFIcategory=Monitoring UNIFIsubCategory=WiFi UNIFIhost=Office UDM Pro UNIFIlastConnectedToDeviceName=Lobby AP UNIFIclientIp=192.168.10.178 UNIFIwifiName=Employee WiFi UNIFInetworkVlan=10 msg=Apple Watch 0d:87 disconnected from Employee WiFi...
```

## Supported CEF keys

Standard: `cnt`, `deviceOutboundInterface`, `msg`, `reason`, `src`, `suser`

UniFi-specific (`UNIFI*`):

```
UNIFI2GHzChannel, UNIFI5GHzChannel, UNIFI6GHzChannel, UNIFIWiFiRssi, UNIFIaccessMethod,
UNIFIadmin, UNIFIattemptedConnectionMethod, UNIFIattemptedConnectionSource, UNIFIauthMethod,
UNIFIbackupPowerDevice, UNIFIbssid, UNIFIcellularCarrier, UNIFIcellularLimit, UNIFIcellularSim,
UNIFIcellularUsage, UNIFIcertExpiryDate, UNIFIcertName, UNIFIclientAlias, UNIFIclientHostname,
UNIFIclientIP, UNIFIclientIp, UNIFIclientMac, UNIFIconflictIp, UNIFIconflictList,
UNIFIconnectedToDeviceIp, UNIFIconnectedToDeviceMac, UNIFIconnectedToDeviceModel,
UNIFIconnectedToDeviceName, UNIFIconnectedToDevicePort, UNIFIconnectedToDeviceVersion,
UNIFIcopiedFromDeviceMAC, UNIFIcopiedFromDeviceName, UNIFIcta, UNIFIcurrentChannel,
UNIFIcurrentRootBridgeDeviceIp, UNIFIcurrentRootBridgeDeviceMac, UNIFIcurrentRootBridgeDeviceModel,
UNIFIcurrentRootBridgeDeviceName, UNIFIcurrentRootBridgeDeviceVersion, UNIFIdetectedByApAndSignalStrength,
UNIFIdetectedByQty, UNIFIdeviceIp, UNIFIdeviceLagPorts, UNIFIdeviceList, UNIFIdeviceMac,
UNIFIdeviceModel, UNIFIdeviceName, UNIFIdevicePort, UNIFIdevicePortList, UNIFIdevicePowerAvailability,
UNIFIdevicePowerRequirement, UNIFIdevicePowerUsage, UNIFIdevicePriorVersion, UNIFIdeviceRequiredPower,
UNIFIdeviceSuppliedPower, UNIFIdeviceUpdateUrl, UNIFIdeviceUpdateVersion, UNIFIdnsServerIp,
UNIFIfailoverCellularCarrier, UNIFIfailoverCellularLimit, UNIFIfailoverCellularSim,
UNIFIfailoverCellularUsage, UNIFIfailoverWanId, UNIFIfailoverWanIp, UNIFIfailoverWanIsp,
UNIFIfailoverWanName, UNIFIfailoverWanPort, UNIFIfailoverWanSubnet, UNIFIfanId, UNIFIhost,
UNIFIlastConnectedToDeviceIp, UNIFIlastConnectedToDeviceMac, UNIFIlastConnectedToDeviceModel,
UNIFIlastConnectedToDeviceName, UNIFIlastConnectedToDevicePort, UNIFIlastConnectedToDeviceVersion,
UNIFIlastConnectedToWiFiBand, UNIFIlastConnectedToWiFiChannel, UNIFIlastConnectedToWiFiChannelWidth,
UNIFIlastConnectedToWiFiRssi, UNIFIlastSuccessfulConfiguration, UNIFImclagBottomSwitchIp,
UNIFImclagBottomSwitchMac, UNIFImclagBottomSwitchModel, UNIFImclagBottomSwitchName,
UNIFImclagBottomSwitchPorts, UNIFImclagBottomSwitchVersion, UNIFImclagGroup
```

## Parsing fault: values containing spaces

CEF extension parsing splits `key=value` pairs on whitespace, so any UniFi value containing a space is truncated at the first one. I found this on 2026-08-28. `UNIFIipsSignature=ET TOR Known Tor Exit Node Traffic group 25` arrives as `ET`, which left the whole threat dataset with two signature values, `ET` and `GPL`, and no way to tell one detection from another. Device names, client aliases, policy names and interface names are hit the same way.

The `unifi_insights` app repairs it at search time. The extractions in its [props.conf](../Configuration/unifi_insights/default/props.conf) re-read each value from `_raw` up to the next CEF key and write to new field names, so they do not collide with the truncated automatic extraction:

| Repaired field | Source key |
| --- | --- |
| `signature` | `UNIFIipsSignature` |
| `rule` | `UNIFIpolicyName` |
| `dvc_name` | `UNIFIdeviceName` |
| `unifi_gateway` | `UNIFIhost` |
| `src_alias`, `dest_alias`, `client_alias` | `UNIFIsrcClientAlias`, `UNIFIdstClientAlias`, `UNIFIclientAlias` |
| `wifi_name` | `UNIFIwifiName` |
| `inbound_interface`, `outbound_interface` | `deviceInboundInterface`, `deviceOutboundInterface` |

I fixed it at search time rather than in SC4S because the extraction is reversible and does not touch the ingest path.

## Event class IDs

SC4S puts the CEF Device Event Class ID in `sc4s_class` but leaves the header's Name in `_raw`; the app extracts it as `cef_name`. The three products use separate ranges and do not overlap, which is what lets the app's event types group by meaning rather than by product. Counts are over 60 days to 2026-08-29.

**UniFi Network**

| Class | Name | Category | CEF severity | Count |
| --- | --- | --- | ---: | ---: |
| 100 | Internet Down | Internet | 10 | 1 |
| 107 | Internet Restored | Internet | 6 | 1 |
| 112 | High Latency Detected | Internet | 4 | 13 |
| 113 | Packet Loss Detected | Internet | 4 | 4 |
| 200 | Threat Detected | Security | 7, 9 | 11,446 |
| 201 | Threat Detected and Blocked | Security | 7 | 373 |
| 203 | Blocked by Firewall | Security | 4 | 25 |
| 400 / 401 | WiFi Client Connected / Disconnected | Client | 1, 2 | 3,967 |
| 403 / 404 | Wired Client Connected / Disconnected | Client | 1, 2 | 1,842 |
| 414 | Device Power Cycled | Power | 6 | 2 |
| 510 | Device Updated | Software | 4 | 1 |
| 512 / 513 | Device Offline / Reconnected | UniFi | 8, 3 | 3 |
| 520 / 521 | VPN Client Connected / Disconnected | VPN | 1, 2 | 18 |
| 528 | DFS Channel Change | UniFi | 3 | 1 |
| 530 | AP Channel Change | UniFi | 2 | 1 |
| 539 | Device IP Address Conflict | UniFi | 8 | 3 |
| 544 | Network Accessed | Audit | 4 | 470 |
| 545 to 549 | Config Created, Modified, Paused, Resumed, Removed | Audit | 5, 6 | 768 |
| 578 | Network Updated | Software | 4 | 3 |

**UniFi OS**

| Class | Name | Count |
| --- | --- | ---: |
| 1 | Test Syslog | 2 |
| 1000 | Admin Accessed UniFi OS | 72 |
| 1005 | Admin Made Config Changes | 401 |
| 1103 | Backup Created | 2 |

**UniFi Protect**

| Class | Name | Category | Count |
| --- | --- | --- | ---: |
| 2008 | access | adminActivity | 205 |
| 2150 | disconnect | system | 2 |
| 2159 | motion | detection | 62 |
| 2161 | smartAudioDetect, smartDetectLine, smartDetectLoiterZone, smartDetectZone | detection | 617 |
| 2163 | videoCodecChanged | adminActivity | 2 |
| 2168 | cameraConnected | system | 1 |
| 2305 | videoDeleted | adminActivity | 17 |
| 2308 | adminActivity | adminActivity | 48 |

UniFi Network names its classes in prose and Protect names them in camelCase, so `cef_name` reads differently between the two. The event types normalise that; `cef_name` is left as the product sends it.

The CEF header severity is the only grading UniFi puts on the non-threat events, and it is meaningful: 10 for Internet Down, 8 for a device going offline or an address conflict, 4 for latency and packet loss. The app maps it to the CIM `severity` for every event that carries no `UNIFIrisk`, which is everything except the threat classes.

Class 1 is UniFi OS's own test event, sent from the Send Test Event button in the SIEM panel. It is deliberately left out of every event type: it carries no subject, and typing it would put a test into a data model as a real event.

## What CEF does not carry

The syslog export carries events. It does not carry the per-connection flow records behind Insights, which come from the controller's private v2 API at `/proxy/network/v2/api/site/default/traffic-flows` and reach Splunk through [unifi_flow_collector.py](../Scripts/unifi_flow_collector.py) into `netfw` at sourcetype `unifi:flow`. The two are complementary: CEF has the IPS signature detail, the flow records have every connection with its policy, risk band, byte counts and destination region.

## Notes on parsing in this deployment

SC4S parses the CEF at ingest: the header vendor/product become `sc4s_vendor` / `sc4s_product`, and the extension keys become `UNIFI*` fields directly, subject to the space truncation above. My go-to base search:

```spl
index=netops sourcetype=cef | table _time sc4s_vendor sc4s_product unifi_gateway cef_name signature rule msg
```
