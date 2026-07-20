# UniFi System Logs / SIEM: CEF Reference

**Created:** 2026-07-01  
**Last updated:** 2026-07-20

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
CEF:0|Ubiquiti|UniFi Network|9.3.33|544|Admin Accessed UniFi Network|1|UNIFIcategory=System UNIFIsubCategory=Admin UNIFIhost=Office UDM Pro UNIFIaccessMethod=web UNIFIadmin=Craig src=<YOUR_CLIENT_IP> msg=Craig accessed UniFi Network using the web. Source IP: <YOUR_CLIENT_IP>
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

## Notes on parsing in this deployment

SC4S parses the CEF at ingest: the header vendor/product become `sc4s_vendor` / `sc4s_product`, and the extension keys become `UNIFI*` fields directly. The `cefutils` (CEF Extraction Add-on) does not need to add anything for the data to be searchable. My go-to base search:

```spl
index=netops sourcetype=cef | table _time sc4s_vendor sc4s_product UNIFIhost UNIFIadmin msg
```
