# UniFi Firewall Zones

**Created:** 2026-07-09  
**Last updated:** 2026-07-28

I track 16 firewall zones and their assigned networks here.

I verified every LAN row against the controller on 2026-07-28 by reading `firewall_zone_id` from all 19 routed LAN networks. `unifi_list_firewall_zones` still reports `"networks": []` for every zone and can't prove membership; see [UniFi zone membership is absent from the zone-matrix endpoint](../Documentation/Troubleshooting/UniFi%20Zone%20Membership%20Absent%20From%20Zone-Matrix%20Endpoint%20-%202026-07-27.md).

## Zone Membership

| Zone | Type | Networks (interfaces) in zone |
|---|---|---|
| Internal | Built-in | Management, Trusted (VLAN 10), Personal-A (VLAN 40), Secure (VLAN 50), Secure Client (VLAN 60) |
| Untrusted | Built-in | IoT (VLAN 20) |
| Dmz | Built-in | DMZ (VLAN 30), DMZ-A (VLAN 90) |
| External | Built-in | Internet 1 (WAN), Internet 2 (WAN), ProtonVPN (VPN client) |
| Vpn | Built-in | FamilyVPN, Management Access, Game-Access, One-Click VPN, Temp |
| Gateway | Built-in | *(none)* |
| Hotspot | Built-in | *(none)* |
| `AlphaSec-Servers` | Custom | SERVERS-A (VLAN 80) |
| `AlphaSec-Mgmt` | Custom | MGMT-A (VLAN 70), Cluster-Net (VLAN 71) |
| `AlphaSec-Observability` | Custom | Security-A (VLAN 72), MONITOR-A (VLAN 73) |
| `AlphaSec-Access` | Custom | Access-A (VLAN 85) |
| KASM-BROWSER | Custom | KASM-BROWSER (VLAN 74) |
| KASM-TRUSTED | Custom | KASM-TRUSTED (VLAN 75) |
| MALWARE-OFFLINE | Custom | MALWARE-OFFLINE (VLAN 77) |
| LAB-MGMT | Custom | LAB-MGMT (VLAN 78) |
| EVIDENCE-QUARANTINE | Custom | EVIDENCE-QUARANTINE (VLAN 79) |

The controller has seven built-in and nine custom zones. The custom set is `AlphaSec-Servers`, `AlphaSec-Mgmt`, `AlphaSec-Observability`, `AlphaSec-Access`, KASM-BROWSER, KASM-TRUSTED, MALWARE-OFFLINE, LAB-MGMT, and EVIDENCE-QUARANTINE.

## Consolidation Result

I moved Cluster-Net into `AlphaSec-Mgmt` and deleted the empty cluster zone. I moved Security-A into the former monitor zone, deleted the empty security zone, and renamed the survivor `AlphaSec-Observability`. The two shortened organisation prefixes were corrected before either merge. The three Kasm zones stayed unchanged because their mutual unreachability is the design.

The 2026-07-27 consolidation reduced the live result to 14. I added LAB-MGMT on 2026-07-28 so a Kasm container escape no longer lands on SERVERS-A beside application workloads. I then added KASM-TRUSTED for ordinary-WAN development sessions during the [workspace build-out](../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md). The controller now has 16 zones.

`Allow Monitor to Security monitoring` explicitly limits the collector to `OBJ-Security-Stack` on `PG-Node-Exporter` inside the shared zone. The rest of the policy migration and service verification is in [Zone and Object Consolidation - 2026-07-27](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md).

The LAB-MGMT creation and its tested path restrictions are recorded in [Kasm Session Isolation](../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md). The KASM-TRUSTED creation and containment tests are recorded in [Kasm Workspace Build-Out](../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md).
