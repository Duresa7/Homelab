# UniFi Firewall Zones

**Created:** 2026-07-09  
**Last updated:** 2026-08-29

I track 11 firewall zones and their assigned networks here.

I verified the current 15 LAN rows from the network records after deleting the empty DMZ-A/VLAN 90 on 2026-08-29. `unifi_list_firewall_zones` still reports `"networks": []` for every zone and can't prove membership; see [UniFi zone membership is absent from the zone-matrix endpoint](../Documentation/Troubleshooting/UniFi%20Zone%20Membership%20Absent%20From%20Zone-Matrix%20Endpoint%20-%202026-07-27.md).

## Zone Membership

| Zone | Type | Networks (interfaces) in zone |
|---|---|---|
| Internal | Built-in | Management, Trusted (VLAN 10), Personal-A (VLAN 40), Proton-WiFi (VLAN 45), Secure (VLAN 50), Secure Client (VLAN 60) |
| Untrusted | Built-in | IoT (VLAN 20) |
| Dmz | Built-in | DMZ (VLAN 30) |
| External | Built-in | Internet 1 (WAN), Internet 2 (WAN), ProtonVPN (VPN client) |
| Vpn | Built-in | FamilyVPN, Management Access, Game-Access, One-Click VPN, Temp |
| Gateway | Built-in | *(none)* |
| Hotspot | Built-in | *(none)* |
| `AlphaSec-Servers` | Custom | SERVERS-A (VLAN 80) |
| `AlphaSec-Mgmt` | Custom | MGMT-A (VLAN 70), Cluster-Net (VLAN 71) |
| `AlphaSec-Observability` | Custom | Security-A (VLAN 72), MONITOR-A (VLAN 73) |
| `AlphaSec-Access` | Custom | Access-A (VLAN 85) |

The controller has seven built-in and four custom zones. The custom set is `AlphaSec-Servers`, `AlphaSec-Mgmt`, `AlphaSec-Observability`, and `AlphaSec-Access`.

`Proton-WiFi`/VLAN 45 joined `Internal` on 2026-08-10 and added no zone. Its containment is the network isolation toggle rather than a zone relationship, so it needs no policy of its own and nothing else in `Internal` changed. See [Proton-WiFi VLAN 45](../Documentation/Change%20Records/Proton-WiFi%20VLAN%2045%20-%202026-08-10.md).

## Consolidation Result

I moved Cluster-Net into `AlphaSec-Mgmt` and deleted the empty cluster zone. I moved Security-A into the former monitor zone, deleted the empty security zone, and renamed the survivor `AlphaSec-Observability`. The two shortened organisation prefixes were corrected before either merge.

The 2026-07-27 consolidation reduced the live result to 14. Two Kasm zones were added on 2026-07-28, bringing that historical platform state to 16. I deleted all five Kasm zones on 2026-08-19 after removing their policies and networks. The controller now has 11 zones.

`Allow Monitor to Security monitoring` explicitly limits the collector to `OBJ-Security-Stack` on `PG-Node-Exporter` inside the shared zone. The rest of the policy migration and service verification is in [Zone and Object Consolidation - 2026-07-27](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md).

The retired zone design and its tests remain in [Kasm Session Isolation](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md) and [Kasm Workspace Build-Out](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md). The deletion result is in [Kasm Workspaces Decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md).
