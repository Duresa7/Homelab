# Unifi Firewall Zones

**Created:** 2026-07-09  
**Last updated:** 2026-07-15

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
| REDACTED_PRIVATE_ORG_LABEL-Servers | Custom | SERVERS-A (VLAN 80) |
| REDACTED_PRIVATE_ORG_LABEL-Mgmt | Custom | MGMT-A (VLAN 70) |
| REDACTED_PRIVATE_ORG_LABEL-Security | Custom | Security-A (VLAN 72) |
| REDACTED_PRIVATE_ORG_LABEL-Access | Custom | Access-A (VLAN 85) |
| REDACTED_PRIVATE_ORG_LABEL-Cluster | Custom | Cluster-Net (VLAN 71) |
