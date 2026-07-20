# Unifi Firewall Zones

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

This is my inventory of firewall zones and the networks each zone contains. I keep it in sync with the controller.

## Firewall Zones → Networks

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
| `<YOUR_ORG_NAME>`-Access | Custom | Access-A (VLAN 85) |
| `<YOUR_ORG_NAME>`-Cluster | Custom | Cluster-Net (VLAN 71) |
