# UniFi Firewall Zones

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

The controller has 12 firewall zones: seven built-in and five custom (`AlphaSec-Servers`, `AlphaSec-Mgmt`, `AlphaSec-Observability`, `AlphaSec-Access`, `AlphaSec-Identity`).

**Last verified against the controller:** 2026-09-24 for the zone names and count (`unifi_list_firewall_zones`). That call returns `"networks": []` for every zone, so membership comes from each network's `firewall_zone_id`, last read on 2026-09-07 ([Identity Plane Network Preparation](../Documentation/Change%20Records/Identity%20Plane%20Network%20Preparation%20-%202026-09-07.md)). See [zone membership is absent from the zone-matrix endpoint](../Documentation/Troubleshooting/Zone%20Membership%20Absent%20From%20Zone-Matrix%20Endpoint%20-%202026-07-27.md).

## Zone Membership

| Zone | Type | Networks (interfaces) in zone |
|---|---|---|
| Internal | Built-in | Management, Trusted (VLAN 10), Personal-A (VLAN 40), Proton-WiFi (VLAN 45), Secure (VLAN 50), Secure Client (VLAN 60) |
| Untrusted | Built-in | IoT (VLAN 20) |
| Dmz | Built-in | DMZ (VLAN 30) |
| External | Built-in | Internet 1 (WAN), Internet 2 (WAN), ProtonVPN (VPN client) |
| Vpn | Built-in | FamilyVPN, Management Access, Game-Access, Temp; One-Click VPN was not returned as a network on 2026-09-06 |
| Gateway | Built-in | *(none)* |
| Hotspot | Built-in | *(none)* |
| `AlphaSec-Servers` | Custom | SERVERS-A (VLAN 80) |
| `AlphaSec-Mgmt` | Custom | MGMT-A (VLAN 70), Cluster-Net (VLAN 71) |
| `AlphaSec-Observability` | Custom | Security-A (VLAN 72), MONITOR-A (VLAN 73) |
| `AlphaSec-Access` | Custom | Access-A (VLAN 85) |
| `AlphaSec-Identity` | Custom | IDENTITY-A (VLAN 65) |

`Proton-WiFi`/VLAN 45 sits in `Internal`. Its containment is the network isolation toggle, not a zone, so it needs no policy of its own. [Proton-WiFi VLAN 45](../Documentation/Change%20Records/Proton-WiFi%20VLAN%2045%20-%202026-08-10.md).

## History

The 2026-07-27 consolidation moved Cluster-Net into `AlphaSec-Mgmt`, merged Security-A into the former monitor zone as `AlphaSec-Observability`, and left 14 zones ([Zone and Object Consolidation](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md)). Two Kasm zones raised that to 16 on 2026-07-28, and deleting the five Kasm zones on 2026-08-19 left 11 ([Kasm Workspaces Decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md)). `AlphaSec-Identity` made 12 on 2026-09-07.

`Allow Monitor to Security monitoring` limits the collector to `AG-Security-Stack` on `PG-Node-Exporter` inside the shared observability zone.
