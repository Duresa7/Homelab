# UniFi VPNs and Port Profiles

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

Five WireGuard servers, one WireGuard client and five switch port profiles. The Network Lists and the traffic route are in [Policy objects](objects.md).

**Last verified against the controller:** 2026-09-24 for the VPN networks (`unifi_list_networks`). The port profiles were last read on 2026-09-06, and `Proxmox-Trunk` again on 2026-09-07.

## VPN Servers

All servers are WireGuard, remote-user-VPN type, bound to the WAN interface.

| Name | Type | Subnet | Listen Port | Status |
|---|---|---|---|---|
| FamilyVPN | WireGuard Server | 192.168.3.1/24 | 51821 | Disabled |
| Management Access | WireGuard Server | 10.6.0.1/24 | 51822 | Enabled |
| Game-Access | WireGuard Server | 10.66.200.1/24 | 51823 | Disabled |
| One-Click VPN | WireGuard Server | 192.168.12.1/24 | 51820 | Not returned as a network on 2026-09-06 or 2026-09-24 |
| Temp | WireGuard Server | 10.6.10.1/24 | 51824 | Disabled |

On 2026-09-24 the controller returned four remote-user VPN networks, FamilyVPN, Management Access, Game-Access and Temp, with only Management Access enabled. `One-Click VPN` is not returned as a network; UniFi presents it as its own feature, and I have not confirmed in the interface whether it is still configured, so its row stays until I do.

## VPN Clients

| Name | Type | Config File | Tunnel IP | Status |
|---|---|---|---|---|
| ProtonVPN | WireGuard Client | wg-US-GA-568.conf | 10.2.0.2/32 | Enabled |

## Port Profiles

| Profile | Port Mode | Native VLAN / Network | Tagged VLAN Management | Tagged VLANs | PoE | STP | 802.1X | PTP | Flow Control |
|---|---|---|---|---|---|---|---|---|---|
| Management | Uplink | Management | Allow All | All | Auto | On | Force Authorized | - | - |
| Trusted | Edge | Trusted (VLAN 10) | - | - | Auto | On | Force Authorized | - | - |
| IoT | Edge | IoT (VLAN 20) | - | - | Auto | On | Force Authorized | - | - |
| Proxmox-Trunk | Uplink | None | Custom exclusion list | All networks except Management, IoT (20), Trusted (10), Secure (50), and Proton-WiFi (45) | Off | On (STP Uplink) | Force Authorized | On | On |
| Server-Provision | Uplink | Server-Provision (VLAN 5) | Custom exclusion list | All networks except Management, IoT (20), Trusted (10), DMZ (30), Secure (50), and Proton-WiFi (45) | Off | On | Force Authorized | On | On |

The controller stores `Proxmox-Trunk` as an exclusion list, not a list of tagged VLANs, and adds every new network to that exclusion list automatically. A new VLAN reaches the Proxmox nodes only after I remove it from the list.

DMZ (30) came off the `Proxmox-Trunk` exclusions during the [edge-01 move](../Documentation/Change%20Records/edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md), and IDENTITY-A (65) came off on 2026-09-07 ([Identity Plane Network Preparation](../Documentation/Change%20Records/Identity%20Plane%20Network%20Preparation%20-%202026-09-07.md)). `Server-Provision` still excludes DMZ (30). VLAN 45 stays excluded on both, because a wireless VPN-egress network has no reason to reach a hypervisor.

`Server-Provision` adds native VLAN 5 for bare-metal installs; UniFi DHCP advertises `192.168.40.36` and `galaxy-ipxe.efi` on that network. Bane port 4 carried it for the `green-server` install and has used `Proxmox-Trunk` since Green joined on 2026-07-31.

`Proxmox-Trunk` carries `Server-Provision`/VLAN 5 tagged since 2026-07-31, so a node can PXE-boot a guest on VLAN 5. [Galaxy PXE provisioning service](../../../../Platforms/Galaxy%20PXE/Documentation/Change%20Records/Provisioning%20Service%20-%202026-07-30.md).
