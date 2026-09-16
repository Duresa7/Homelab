# UniFi VPNs, Network Lists & Port Profiles

**Created:** 2026-07-09  
**Last updated:** 2026-09-16

I removed the unused Portainer Edge Agents port group on 2026-09-16. The controller now holds 22 Network Lists. That readback also returned the six identity groups and `AG-Automation-Hosts`, none of which this table carried, so I added their rows and the table now matches the controller. The historical VPN verification below is unchanged.

I track five WireGuard servers, one WireGuard client, one traffic route, 22 reusable Network Lists, and five switch port profiles here. I read the networks, port profiles, and traffic routes back on 2026-09-06, and the Network Lists back on 2026-09-16.

## VPN Servers

All servers are WireGuard, remote-user-VPN type, bound to the WAN interface.

| Name | Type | Subnet | Listen Port | Status |
|---|---|---|---|---|
| FamilyVPN | WireGuard Server | 192.168.3.1/24 | 51821 | Disabled |
| Management Access | WireGuard Server | 10.6.0.1/24 | 51822 | Enabled |
| Game-Access | WireGuard Server | 10.66.200.1/24 | 51823 | Disabled on the 2026-09-06 readback |
| One-Click VPN | WireGuard Server | 192.168.12.1/24 | 51820 | Not among the networks the controller returned on 2026-09-06 |
| Temp | WireGuard Server | 10.6.10.1/24 | 51824 | Disabled |

The 2026-09-06 network readback returned four remote-user VPN networks, not five: FamilyVPN, Management Access, Game-Access, and Temp, with only Management Access enabled. `Game-Access` had been recorded as enabled here since 2026-07-09 and is disabled on the controller. `One-Click VPN` was not returned as a network at all; UniFi presents One-Click VPN as its own feature, and I have not confirmed through the interface whether it is still configured, so its row stays until I do.

## VPN Clients

| Name | Type | Config File | Tunnel IP | Status |
|---|---|---|---|---|
| ProtonVPN | WireGuard Client | wg-US-GA-568.conf | 10.2.0.2/32 | Enabled |

## Traffic Routes

| Name | Interface | Target networks | Destination | Kill switch | Status |
| --- | --- | --- | --- | --- | --- |
| VPN - Proton | ProtonVPN | Proton-WiFi (VLAN 45) | Any Internet destination | Enabled | Enabled |

On 2026-07-27 I deleted `Non-tracking` before deleting Secure-V/VLAN 100. The [consolidation change record](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md) holds that dependency order and readback.

On 2026-08-10 I repointed `VPN - Proton` from a single client MAC to `Proton-WiFi`/VLAN 45 and enabled it, which is what supplies that network its VPN egress and its kill switch. It had been disabled since it was created, so the client it used to name never routed through it. The build is in [Proton-WiFi VLAN 45](../Documentation/Change%20Records/Proton-WiFi%20VLAN%2045%20-%202026-08-10.md).

On 2026-08-19 I disabled and deleted the Kasm-specific route before deleting its target network. The shared ProtonVPN client and `VPN - Proton` route remained enabled and unchanged.

## Network Lists

Reusable port/address groups referenced by firewall policies.

| Name | Type | Members |
|---|---|---|
| Wazuh Ports | Port group | 1514, 1515 |
| App Access | Port group | 80, 8000 |
| Proxmox-Admin-Ports | Port group | 22, 8006, 3128 |
| Allow Identity Sync Service Connection-9543 | Port group | 9543 |
| AG-Monitor-Collector | IPv4 address group | 192.168.73.2 |
| AG-Reverse-Proxy | IPv4 address group | 192.168.85.2 |
| AG-Security-Stack | IPv4 address group | 192.168.72.2, 192.168.72.3 |
| AG-Proxmox-Nodes | IPv4 address group | 192.168.70.10 through 192.168.70.14 |
| AG-Observability-Hosts | IPv4 address group | 192.168.72.2, 192.168.72.3, 192.168.73.2 |
| PG-Node-Exporter | Port group | 9100, 9101, 9102 |
| PG-Egress-Web | Port group | 80, 443 |
| PG-NTP | Port group | 123 |
| AG-Galaxy-PXE-Service | IPv4 address group | 192.168.40.36 |
| PG-Galaxy-PXE-Callback | Port group | 8080 |
| PG-Printing | Port group | 631, 9100 |
| AG-Domain-Controllers | IPv4 address group | 192.168.65.10, 192.168.65.11 |
| AG-Identity-Servers | IPv4 address group | 192.168.65.10, 192.168.65.11, 192.168.65.12 |
| AG-PAW | IPv4 address group | 192.168.50.241 |
| AG-Automation-Hosts | IPv4 address group | 192.168.40.179, 192.168.40.39 |
| PG-AD-Client | Port group | 53, 88, 123, 135, 389, 445, 464, 636, 3268, 3269, 49152-65535 |
| PG-Windows-Admin | Port group | 22, 3389, 5985, 5986 |
| PG-Windows-Exporter | Port group | 9182 |

## Port Profiles

| Profile | Port Mode | Native VLAN / Network | Tagged VLAN Management | Tagged VLANs | PoE | STP | 802.1X | PTP | Flow Control |
|---|---|---|---|---|---|---|---|---|---|
| Management | Uplink | Management | Allow All | All | Auto | On | Force Authorized | - | - |
| Trusted | Edge | Trusted (VLAN 10) | - | - | Auto | On | Force Authorized | - | - |
| IoT | Edge | IoT (VLAN 20) | - | - | Auto | On | Force Authorized | - | - |
| Proxmox-Trunk | Uplink | None | Custom exclusion list | All networks except Management, IoT (20), Trusted (10), Secure (50), and Proton-WiFi (45) | Off | On (STP Uplink) | Force Authorized | On | On |
| Server-Provision | Uplink | Server-Provision (VLAN 5) | Custom exclusion list | All networks except Management, IoT (20), Trusted (10), DMZ (30), Secure (50), and Proton-WiFi (45) | Off | On | Force Authorized | On | On |

The controller stores `Proxmox-Trunk` as an exclusion list, not a positive tagged-VLAN list. It automatically adds a new network to that exclusion list. The five former Kasm VLANs were deleted on 2026-08-19, so neither port profile can carry them now.

I read both profiles back on 2026-08-10 and they no longer carry the same list. `Proxmox-Trunk` excludes Management, IoT (20), Trusted (10), Secure (50), and Proton-WiFi (45): DMZ (30) came off during the [edge-01 move](../Documentation/Change%20Records/edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md) and VLAN 45 was added automatically when I created the network. `Server-Provision` excludes those five plus DMZ (30), because the 2026-08-07 removal touched only `Proxmox-Trunk`. I left VLAN 45 excluded on both, since a wireless VPN-egress network has no reason to reach a hypervisor.

`Server-Provision` adds native VLAN 5. I assigned it to Bane switch port 4 for the `green-server` installation. UniFi DHCP advertises `192.168.40.36` and `galaxy-ipxe.efi` on that network. Green completed the installation and cluster join on 2026-07-31, after which I changed Bane port 4 to `Proxmox-Trunk`.

On 2026-07-31 I explicitly admitted `Server-Provision`/VLAN 5 as tagged traffic on `Proxmox-Trunk`. The profile readback still uses the same five exclusions, and VLAN 5 is not one of them. A disposable UEFI VM on Red received `192.168.5.143`, completed the automatic Proxmox install, reported `/dev/sda`, and powered off. The final Bane port 4 readback showed `Proxmox-Trunk`, VLANs 70 and 71 admitted, a 1 GbE link, and PoE off.
