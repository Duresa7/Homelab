# UniFi VPNs, Groups & Port Profiles

**Created:** 2026-07-09  
**Last updated:** 2026-08-11

I track five WireGuard servers, one WireGuard client, two traffic routes, 13 reusable firewall groups, and five switch port profiles here.

## VPN Servers

All servers are WireGuard, remote-user-VPN type, bound to the WAN interface.

| Name | Type | Subnet | Listen Port | Status |
|---|---|---|---|---|
| FamilyVPN | WireGuard Server | 192.168.3.1/24 | 51821 | Disabled |
| Management Access | WireGuard Server | 10.6.0.1/24 | 51822 | Enabled |
| Game-Access | WireGuard Server | 10.66.200.1/24 | 51823 | Enabled |
| One-Click VPN | WireGuard Server | 192.168.12.1/24 | 51820 | Enabled |
| Temp | WireGuard Server | 10.6.10.1/24 | 51824 | Disabled |

## VPN Clients

| Name | Type | Config File | Tunnel IP | Status |
|---|---|---|---|---|
| ProtonVPN | WireGuard Client | wg-US-GA-568.conf | 10.2.0.2/32 | Enabled |

## Traffic Routes

| Name | Interface | Target networks | Destination | Kill switch | Status |
| --- | --- | --- | --- | --- | --- |
| VPN - Proton | ProtonVPN | Proton-WiFi (VLAN 45) | Any Internet destination | Enabled | Enabled |
| KASM Lab Proton Egress | ProtonVPN | KASM-BROWSER | Any Internet destination | Enabled | Enabled |

On 2026-07-23 I retargeted the Kasm route to KASM-BROWSER/VLAN 74 only, down from four VLANs, during the [Kasm lab network simplification](../Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md). On 2026-07-27 I deleted `Non-tracking` before deleting Secure-V/VLAN 100. The [consolidation change record](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md) holds that dependency order and readback.

On 2026-08-10 I repointed `VPN - Proton` from a single client MAC to `Proton-WiFi`/VLAN 45 and enabled it, which is what supplies that network its VPN egress and its kill switch. It had been disabled since it was created, so the client it used to name never routed through it. The build is in [Proton-WiFi VLAN 45](../Documentation/Change%20Records/Proton-WiFi%20VLAN%2045%20-%202026-08-10.md).

I retested the Kasm route on 2026-07-28. An enabled VPN with a failed tunnel blocks VLAN 74 while the Kasm host retains ordinary WAN. Administratively disabling the ProtonVPN object causes UniFi to fall back to WAN, so I keep the client enabled whenever a KASM-BROWSER session may run. The exact test is in [Kasm Session Isolation](../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md).

## Network List (Firewall Groups)

Reusable port/address groups referenced by firewall policies.

| Name | Type | Members |
|---|---|---|
| Wazuh Ports | Port group | 1514, 1515 |
| App Access | Port group | 80, 8000 |
| Proxmox-Admin-Ports | Port group | 22, 8006 |
| Portainer Edge Agents | Port group | 8000, 9443 |
| Allow Identity Sync Service Connection-9543 | Port group | 9543 |
| OBJ-Monitor-Collector | IPv4 address group | 192.168.73.2 |
| OBJ-Reverse-Proxy | IPv4 address group | 192.168.85.2 |
| OBJ-Security-Stack | IPv4 address group | 192.168.72.2, 192.168.72.3 |
| OBJ-Proxmox-Nodes | IPv4 address group | 192.168.70.10 through 192.168.70.14 |
| OBJ-Observability-Hosts | IPv4 address group | 192.168.72.2, 192.168.72.3, 192.168.73.2 |
| PG-Node-Exporter | Port group | 9100, 9101 |
| PG-Egress-Web | Port group | 80, 443 |
| PG-NTP | Port group | 123 |

## Port Profiles

| Profile | Port Mode | Native VLAN / Network | Tagged VLAN Management | Tagged VLANs | PoE | STP | 802.1X | PTP | Flow Control |
|---|---|---|---|---|---|---|---|---|---|
| Management | Uplink | Management | Allow All | All | Auto | On | Force Authorized | - | - |
| Trusted | Edge | Trusted (VLAN 10) | - | - | Auto | On | Force Authorized | - | - |
| IoT | Edge | IoT (VLAN 20) | - | - | Auto | On | Force Authorized | - | - |
| Proxmox-Trunk | Uplink | None | Custom exclusion list | All networks except Management, IoT (20), Trusted (10), Secure (50), and Proton-WiFi (45) | Off | On (STP Uplink) | Force Authorized | On | On |
| Server-Provision | Uplink | Server-Provision (VLAN 5) | Custom exclusion list | All networks except Management, IoT (20), Trusted (10), DMZ (30), Secure (50), and Proton-WiFi (45) | Off | On | Force Authorized | On | On |

The controller stores `Proxmox-Trunk` as an exclusion list, not a positive tagged-VLAN list. It automatically adds a new network to that exclusion list. I removed LAB-MGMT/VLAN 78 during the session-isolation change and KASM-TRUSTED/VLAN 75 during the [workspace build-out](../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md). VLANs 74, 75, 77, 78, and 79 are admitted.

I read both profiles back on 2026-08-10 and they no longer carry the same list. `Proxmox-Trunk` excludes Management, IoT (20), Trusted (10), Secure (50), and Proton-WiFi (45): DMZ (30) came off during the [edge-01 move](../Documentation/Change%20Records/edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md) and VLAN 45 was added automatically when I created the network. `Server-Provision` excludes those five plus DMZ (30), because the 2026-08-07 removal touched only `Proxmox-Trunk`. I left VLAN 45 excluded on both, since a wireless VPN-egress network has no reason to reach a hypervisor.

`Server-Provision` adds native VLAN 5. I assigned it to Bane switch port 4 for the `green-server` installation. UniFi DHCP advertises `192.168.40.36` and `galaxy-ipxe.efi` on that network. Green completed the installation and cluster join on 2026-07-31, after which I changed Bane port 4 to `Proxmox-Trunk`.

On 2026-07-31 I explicitly admitted `Server-Provision`/VLAN 5 as tagged traffic on `Proxmox-Trunk`. The profile readback still uses the same five exclusions, and VLAN 5 is not one of them. A disposable UEFI VM on Red received `192.168.5.143`, completed the automatic Proxmox install, reported `/dev/sda`, and powered off. The final Bane port 4 readback showed `Proxmox-Trunk`, VLANs 70 and 71 admitted, a 1 GbE link, and PoE off.
