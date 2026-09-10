# UniFi Networks and VLANs

**Created:** 2026-07-09  
**Last updated:** 2026-09-09

I verified IDENTITY-A on 2026-09-07: VLAN 65, gateway 192.168.65.1/24, DHCP 192.168.65.100 through 192.168.65.120, enabled, and assigned to AlphaSec-Identity. The network reports `mdns_enabled: false`, `ipv6_interface_type: none`, and `ipv6_ra_enabled: false`. The mDNS field is a controller mirror, not an independent verification of the site-wide mDNS setting. I retained the [network readback](../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Initial%20Controller%20Readback.json). The current count is 23 networks, including 16 routed corporate LANs.

I removed only IDENTITY-A from the Proxmox-Trunk exclusion list. VLANs 65 and 60 are now admitted; grey-server is online at 192.168.70.10 through Bane Switch POE port 14, which uses that profile and reports a 2.5 GbE link. The [trunk readback](../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Trunk%20Update%20and%20Readback.json) confirms every other profile field stayed unchanged.

On 2026-09-09 I changed DHCP DNS on Secure and Secure Client to 192.168.65.10 followed by 192.168.65.11. I verified both saved network panels with Auto DNS Server unchecked. Their gateways, /24 subnets and DHCP ranges stayed unchanged. The [change record](../Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md) retains final screenshots.

I re-read all 22 networks on 2026-09-06 and every row present then matched: names, VLAN IDs, subnets, and DHCP ranges. I verified this table against the controller after the [Galaxy PXE provisioning service](../../../../Platforms/Galaxy%20PXE/Documentation/Change%20Records/Galaxy%20PXE%20Provisioning%20Service%20-%202026-07-30.md) on 2026-07-31. I admitted `Server-Provision`/VLAN 5 as tagged traffic on `Proxmox-Trunk`, completed the disposable UEFI test, and then completed Green's physical NVMe install and cluster join through VLAN 5.

I added `Proton-WiFi`/VLAN 45 on 2026-08-10 for wireless clients that egress through ProtonVPN. After I retired the five Kasm networks on 2026-08-19, 16 routed LAN networks remained out of 23 controller networks. I deleted the empty DMZ-A/VLAN 90 on 2026-08-29, leaving 15 routed LAN networks out of 22 at that point. The other seven networks are two WANs, the ProtonVPN client, and four remote-user VPN networks. The Proton WiFi build is in [Proton-WiFi VLAN 45](../Documentation/Change%20Records/Proton-WiFi%20VLAN%2045%20-%202026-08-10.md).

I removed deleted VM 117 `supabase-01` from the SERVERS-A placement examples on 2026-08-20. This was a documentation correction only; I did not query or change the UniFi controller during that retirement pass.

I deleted DMZ-A/VLAN 90 on 2026-08-29, after the soak period that began when `edge-01` moved to DMZ (30) on 2026-08-07. It held no clients, no firewall policy, no static route, and no port forward, and it was never pinned into a port profile. See [DMZ-A VLAN 90 Removal](../Documentation/Change%20Records/DMZ-A%20VLAN%2090%20Removal%20-%202026-08-29.md).

I deleted AD-SERVERS/65 and `Secure-V`/100 on 2026-07-27. The Active Directory retirement removed the old VLAN 65 network and its three guests. I reused VLAN 65 for the separate IDENTITY-A network on 2026-09-07. The consolidation removed the `Non-tracking` route before deleting VLAN 100. The retired AD-SERVERS and Secure-V networks are not part of current placement.

## Networks / VLANs

| Network | VLAN ID | Subnet | Gateway IP | DHCP Range | Router |
|---|---|---|---|---|---|
| Management | (untagged) | 192.168.1.0/24 | 192.168.1.1 | .6 – .254 | Ahsoka Gateway |
| Server-Provision | 5 | 192.168.5.0/24 | 192.168.5.1 | .6 – .254 | Ahsoka Gateway |
| Trusted | 10 | 192.168.10.0/24 | 192.168.10.1 | .6 – .254 | Ahsoka Gateway |
| IoT | 20 | 192.168.20.0/24 | 192.168.20.1 | .6 – .254 | Ahsoka Gateway |
| DMZ | 30 | 192.168.30.0/24 | 192.168.30.1 | .50 – .100 | Ahsoka Gateway |
| Personal-A | 40 | 192.168.40.0/24 | 192.168.40.1 | .100 – .254 | Ahsoka Gateway |
| Proton-WiFi | 45 | 192.168.45.0/24 | 192.168.45.1 | .100 – .199 | Ahsoka Gateway |
| Secure | 50 | 192.168.50.0/24 | 192.168.50.1 | .6 – .254 | Ahsoka Gateway |
| Secure Client | 60 | 192.168.60.0/24 | 192.168.60.1 | .6 – .254 | Ahsoka Gateway |
| IDENTITY-A | 65 | 192.168.65.0/24 | 192.168.65.1 | .100 – .120 | Ahsoka Gateway |
| MGMT-A | 70 | 192.168.70.0/24 | 192.168.70.1 | .50 – .200 | Ahsoka Gateway |
| Cluster-Net | 71 | 192.168.71.0/24 | 192.168.71.1 | none | Ahsoka Gateway |
| Security-A | 72 | 192.168.72.0/24 | 192.168.72.1 | .6 – .254 | Ahsoka Gateway |
| MONITOR-A | 73 | 192.168.73.0/24 | 192.168.73.1 | .6 – .254 | Ahsoka Gateway |
| SERVERS-A | 80 | 192.168.80.0/24 | 192.168.80.1 | .6 – .254 | Ahsoka Gateway |
| Access-A | 85 | 192.168.85.0/24 | 192.168.85.1 | .6 – .254 | Ahsoka Gateway |

## Purpose and Device Placement

I use this table when placing a new device or workload. The **Zone** column names the [firewall zone](zone.md) that controls its network paths. Names ending in **`-A`** belong to the segmented `AlphaSec` infrastructure tier, while unsuffixed VLANs serve household and general lab devices. The examples reflect controller state but don't list every client.

| Network (VLAN) | Zone | Trust tier | What belongs here: device types and examples |
|---|---|---|---|
| Management (untagged) | Internal | Infrastructure mgmt plane | Network fabric and appliances only: the UniFi gateway, switches, access points, and UniFi Protect cameras. I don't park general clients or servers here. |
| Server-Provision (5) | Internal | Temporary deployment lane | Bare-metal Galaxy nodes use DHCP and UEFI PXE here before first boot moves them to tagged MGMT-A and Cluster-Net. DHCP network boot advertises `192.168.40.36` and `galaxy-ipxe.efi`. |
| Trusted (10) | Internal | Trusted personal | Personal devices I trust but that are not admin machines: household phones, tablets, laptops, watches, and personal streaming/voice devices (iPhones, Pixels, MacBooks, Galaxy Watch, personal Fire TV / Alexa). Blocked from reaching Personal-A. |
| IoT (20) | Untrusted | Untrusted appliance | Smart-home and appliance-class gear with no admin need and no reason to reach the LAN: smart cameras (Wyze, Ring), thermostats (Nest), smart TVs and streamers (Samsung TV, Roku), smart appliances (Samsung FamilyHub), plugs and sensors. Isolated from Internal. |
| DMZ (30) | Dmz | Internet-facing edge | I place internet-exposed / untrusted workloads here, including `edge-01` at static `192.168.30.10` with gateway `192.168.30.1`. I block this network from Internal and can pin it to ProtonVPN egress via the `isolate` policy. On 2026-08-07 I removed DMZ from the `Proxmox-Trunk` exclusions and left only Management, IoT (20), Trusted (10), and Secure (50) excluded. Before that change, I could not place virtualised workloads on VLAN 30 because the trunk did not carry it. That restriction was likely why I created DMZ-A. |
| Personal-A (40) | Internal | My lab / utility | My general-purpose lab and utility VMs and containers, **not** household user devices: Docker hosts (`docker-main`, `docker-blue`, `media-01`), automation (`ansible-01`), & pentest or development VMs (`kali-pen`, `ubuntu-dev`). Reachable only from a defined admin device allow-list. |
| Proton-WiFi (45) | Internal | Isolated VPN egress | Wireless clients whose traffic must leave through ProtonVPN rather than the WAN. Network isolation blocks it from every other network, the SSID carries L2 isolation so its own clients cannot address each other, and DHCP hands out Quad9 so lookups travel the tunnel. Egress and the kill switch come from the `VPN - Proton` route. No servers and no wired ports. |
| Secure (50) | Internal | Primary admin workstation | I keep Jedi PC at 192.168.50.241 as my privileged workstation. It remains part of the MGMT-A allowed set. |
| Secure Client (60) | Internal | End-user workstations | I place every end-user PC and the Windows 11 test VM here with DHCP. |
| IDENTITY-A (65) | `AlphaSec-Identity` | Active Directory identity plane | I reserve HQ-DC01 at 192.168.65.10, HQ-DC02 at 192.168.65.11, and HQ-MGT01 at 192.168.65.12 on grey-server for Windows Server 2025. This is the intended guest placement; this network verification does not establish that the guests are deployed. |
| MGMT-A (70) | `AlphaSec-Mgmt` | Hypervisor mgmt plane | Proxmox node management interfaces and hypervisor administration: the registered cluster node IPs from `.10` through `.14`, PVE GUI/API/SSH, and Corosync link0. Out-of-band / IPMI belongs here. |
| Cluster-Net (71) | `AlphaSec-Mgmt` | Cluster interconnect | Proxmox east-west cluster traffic only: Corosync link1 and replication on node IPs `.10` through `.14`. No DHCP, no Internet access, and no general hosts. It shares the management trust zone with MGMT-A but remains a separate broadcast domain. |
| Security-A (72) | `AlphaSec-Observability` | Security and detection | SIEM and log workloads: `security-01` = .2 and `splunk-siem` = .3. It shares the observability posture with MONITOR-A. Egress is limited to approved web and NTP from the three-member `AG-Observability-Hosts` Network List. |
| MONITOR-A (73) | `AlphaSec-Observability` | Monitoring collector | CT 104 `monitor-01` at static 192.168.73.2 runs Prometheus, Grafana, and their backend exporters. DHCP remains enabled from .6 through .254. The shared zone does not merge VLANs 72 and 73. |
| SERVERS-A (80) | `AlphaSec-Servers` | Internal app/data | Internal (non-internet-facing) application and database servers/VMs: app servers and databases (`app-01` = .10, `db-13-host` = .228). |
| Access-A (85) | `AlphaSec-Access` | Ingress / remote access | Network-access, ingress, and remote-access tooling: reverse proxies and VPN/mesh gateways (docker-network = .2 running Nginx Proxy Manager and NetBird). Tightly restricted egress. |

### Placement by Workload

- Phone, tablet, or personal laptop (mine or family) → **Trusted (10)**; the same device when it must egress through ProtonVPN instead → **Proton-WiFi (45)**
- Smart-home gadget, camera, TV, or appliance → **IoT (20)**
- Jedi PC, my privileged workstation at 192.168.50.241 → **Secure (50)**; every end-user PC and the Windows 11 test VM, using DHCP → **Secure Client (60)**
- HQ-DC01, HQ-DC02, and HQ-MGT01 on grey-server → **IDENTITY-A (65)**
- Proxmox node management IP → **MGMT-A (70)**; that node's Corosync/cluster link → **Cluster-Net (71)**
- Internal application or database VM → **SERVERS-A (80)**
- Security or logging tool → **Security-A (72)**; the central monitoring collector → **MONITOR-A (73)**. Both use the `AlphaSec-Observability` zone.
- Reverse proxy, VPN, or remote-access ingress → **Access-A (85)**
- Public / internet-facing service → **DMZ (30)**
- General lab, automation, or utility VM/container → **Personal-A (40)**
- Switch, AP, gateway, or Protect camera → **Management (untagged)**
- Bare-metal Galaxy node during automated installation → **Server-Provision (5)**; the installed node moves to **MGMT-A (70)** and **Cluster-Net (71)**

## Retired Networks

| Network | Deleted | Reason | Durable record |
|---|---|---|---|
| AD-SERVERS (65) | 2026-07-27 | The Windows domain, both domain controllers, and the domain-joined test VM were retired. | [Windows Servers retirement](../../../../Archive/Platforms/Windows%20Servers/README.md) |
| Secure-V (100) | 2026-07-27 | Its domain SSID was already gone. I deleted the `Non-tracking` ProtonVPN route first, then removed the unused network. | [Zone and Object Consolidation](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md) |
| KASM-BROWSER (74) | 2026-08-19 | The disposable browser lane ended with the Kasm platform. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| KASM-TRUSTED (75) | 2026-08-19 | The trusted disposable-session lane ended with the Kasm platform. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| MALWARE-OFFLINE (77) | 2026-08-19 | The offline detonation lane ended with the Kasm platform. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| LAB-MGMT (78) | 2026-08-19 | VM 122 and its isolated control-plane network were destroyed. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| EVIDENCE-QUARANTINE (79) | 2026-08-19 | The evidence-review lane ended with the Kasm platform. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |

The disabled `Alpha-Sec-IoT` WLAN, which earlier records spell `AlphaSec-IoT`, now points to IoT/VLAN 20. It stayed disabled during the correction, and the 2026-09-06 WLAN readback still shows it disabled under the controller's hyphenated name.
