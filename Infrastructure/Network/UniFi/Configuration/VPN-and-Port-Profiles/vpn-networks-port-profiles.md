# Unifi VPN, Networks & Port Profiles

**Created:** 2026-07-09  
**Last updated:** 2026-07-17

## VPN Servers

All servers are WireGuard, remote-user-VPN type, bound to the WAN interface.

| Name | Type | Subnet | Listen Port | Status |
|---|---|---|---|---|
| FamilyVPN | WireGuard Server | 192.168.3.1/24 | 51821 | Disabled |
| Management Access | WireGuard Server | 10.6.0.1/24 | 51822 | Enabled |
| Game-Access | WireGuard Server | 10.66.200.1/24 | 51823 | Enabled |
| One-Click VPN | WireGuard Server | 192.168.12.1/24 | 51820 | Enabled |
| Temp | WireGuard Server | 10.6.10.1/24 | 51824 | Enabled |

## VPN Clients

| Name | Type | Config File | Tunnel IP | Status |
|---|---|---|---|---|
| ProtonVPN | WireGuard Client | wg-US-GA-568.conf | 10.2.0.2/32 | Disabled |

## Network List (Firewall Groups)

Reusable port/address groups referenced by firewall policies.

| Name | Type | Members |
|---|---|---|
| Wazuh Ports | Port group | 1514, 1515 |
| App Access | Port group | 80, 8000 |
| Proxmox-Admin-Ports | Port group | 22, 8006 |
| Portainer Edge Agents | Port group | 8000, 9443 |
| Allow Identity Sync Service Connection-9543 | Port group | 9543 |

## Port Profiles

| Profile | Port Mode | Native VLAN / Network | Tagged VLAN Management | Tagged VLANs | PoE | STP | 802.1X | PTP | Flow Control |
|---|---|---|---|---|---|---|---|---|---|
| Management | Uplink | Management | Allow All | All | Auto | On | Force Authorized | — | — |
| Trusted | Edge | Trusted (VLAN 10) | — | — | Auto | On | Force Authorized | — | — |
| IoT | Edge | IoT (VLAN 20) | — | — | Auto | On | Force Authorized | — | — |
| Proxmox-Trunk | Uplink | None | Custom | Personal-A (40), Secure Client (60), AD-SERVERS (65), MGMT-A (70), Cluster-Net (71), Security-A (72), SERVERS-A (80), Access-A (85), DMZ-A (90) | Off | On (STP Uplink) | Force Authorized | On | On |
