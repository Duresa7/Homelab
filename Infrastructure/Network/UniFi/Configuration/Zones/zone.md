# UniFi Firewall Zones

**Created:** 2026-07-09  
**Last updated:** 2026-07-26

I track 16 firewall zones and their assigned networks here.

## Zone Membership

| Zone | Type | Networks (interfaces) in zone |
|---|---|---|
| Internal | Built-in | Management, Personal-A (VLAN 40), Secure (VLAN 50), Secure Client (VLAN 60), AD-SERVERS (VLAN 65) |
| Untrusted | Built-in | IoT (VLAN 20) |
| Dmz | Built-in | DMZ (VLAN 30), DMZ-A (VLAN 90) |
| External | Built-in | Internet 1 (WAN), Internet 2 (WAN), ProtonVPN (VPN client) |
| Vpn | Built-in | FamilyVPN, Management Access, Game-Access, One-Click VPN, Temp |
| Gateway | Built-in | *(none)* |
| Hotspot | Built-in | *(none)* |
| `<YOUR_ORG_NAME>`-Servers | Custom | SERVERS-A (VLAN 80) |
| `<YOUR_ORG_NAME>`-Mgmt | Custom | MGMT-A (VLAN 70) |
| `<YOUR_ORG_NAME>`-Security | Custom | Security-A (VLAN 72) |
| Org-Monitor | Custom | MONITOR-A (VLAN 73) |
| `<YOUR_ORG_NAME>`-Access | Custom | Access-A (VLAN 85) |
| `<YOUR_ORG_NAME>`-Cluster | Custom | Cluster-Net (VLAN 71) |
| KASM-BROWSER | Custom | KASM-BROWSER (VLAN 74) |
| MALWARE-OFFLINE | Custom | MALWARE-OFFLINE (VLAN 77) |
| EVIDENCE-QUARANTINE | Custom | EVIDENCE-QUARANTINE (VLAN 79) |

`Org-Monitor` is written literally because that's the live name on the controller, and it's the one zone that breaks the naming pattern. It should read `<YOUR_ORG_NAME>`-Monitor like its four siblings. The name came from taking this repository's redaction placeholder at face value while creating the zone on 2026-07-26. Renaming it is safe, since policies bind to `zone_id` rather than to the name, but the plugin has no zone-rename operation so it has to happen in the controller UI. Tracked in the [root backlog](../../../../../TODO.md).
