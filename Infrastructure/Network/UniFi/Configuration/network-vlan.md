# UniFi Networks and VLANs

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

The controller holds 23 networks: 16 routed corporate LANs (below), two WANs, the ProtonVPN client network and four remote-user VPN servers. Ahsoka Gateway routes every LAN.

**Last verified against the controller:** 2026-09-24. `unifi_list_networks` returned all 23, and the 16 LANs matched this table on name, VLAN and subnet. `Internet 1` is up. `Internet 2` is configured as a DHCP failover WAN (priority 2, `failover-only`) with its enabled flag unset, and the gateway reported no WAN2 address and no link. Of the remote-user VPNs only Management Access (`10.6.0.1/24`) is enabled; see [VPNs and port profiles](vpn-networks-port-profiles.md).

## Recent changes

- 2026-09-21: DHCP reservation for `win11-dev` at `192.168.40.117`. [win11-dev Completion](../../../Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Completion%20-%202026-09-21.md).
- 2026-09-09: DHCP DNS on Secure and Secure Client moved to `192.168.65.10`, then `192.168.65.11`. [Identity NTP and Client DNS](../Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md).
- 2026-09-07: IDENTITY-A verified and admitted on `Proxmox-Trunk`. [Identity Plane Network Preparation](../Documentation/Change%20Records/Identity%20Plane%20Network%20Preparation%20-%202026-09-07.md).

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

I use this table when placing a new device or workload. The **Zone** column names the [firewall zone](zone.md) that controls its network paths. Names ending in **`-A`** belong to the segmented `AlphaSec` infrastructure tier, while unsuffixed VLANs serve household and general lab devices. The examples are the current guests, not every client.

| Network (VLAN) | Zone | Trust tier | What belongs here: device types and examples |
|---|---|---|---|
| Management (untagged) | Internal | Infrastructure mgmt plane | Network fabric and appliances only: the UniFi gateway, switches, access points, and UniFi Protect cameras. I don't park general clients or servers here. |
| Server-Provision (5) | Internal | Temporary deployment lane | Bare-metal Galaxy nodes use DHCP and UEFI PXE here before first boot moves them to tagged MGMT-A and Cluster-Net. DHCP network boot advertises `192.168.40.36` and `galaxy-ipxe.efi`. |
| Trusted (10) | Internal | Trusted personal | Personal devices I trust but that are not admin machines: household phones, tablets, laptops, watches, and personal streaming/voice devices (iPhones, Pixels, MacBooks, Galaxy Watch, personal Fire TV / Alexa). Blocked from reaching Personal-A. |
| IoT (20) | Untrusted | Untrusted appliance | Smart-home and appliance-class gear with no admin need and no reason to reach the LAN: smart cameras (Wyze, Ring), thermostats (Nest), smart TVs and streamers (Samsung TV, Roku), smart appliances (Samsung FamilyHub), plugs and sensors. Isolated from Internal. |
| DMZ (30) | Dmz | Internet-facing edge | Internet-exposed workloads: `edge-01` at static `192.168.30.10`, gateway `192.168.30.1`. Blocked from Internal; can be pinned to ProtonVPN egress through the `isolate` policy. `Proxmox-Trunk` has carried VLAN 30 since 2026-08-07 ([edge-01 Move to DMZ](../Documentation/Change%20Records/edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md)). |
| Personal-A (40) | Internal | My lab / utility | My general-purpose lab and utility VMs and containers, **not** household user devices: Docker hosts (`docker-main` = .35, `docker-blue` = .39, `media-01` = .42), automation (`ansible-01` = .36), and pentest or development VMs (`kali-pen`, `ubuntu-dev` = .179, `win11-dev` = .117). Reachable only from a defined admin device allow-list. |
| Proton-WiFi (45) | Internal | Isolated VPN egress | Wireless clients whose traffic must leave through ProtonVPN rather than the WAN. Network isolation blocks it from every other network, the SSID carries L2 isolation so its own clients cannot address each other, and DHCP hands out Quad9 so lookups travel the tunnel. Egress and the kill switch come from the `VPN - Proton` route. No servers and no wired ports. |
| Secure (50) | Internal | Primary admin workstation | I keep Jedi PC at 192.168.50.241 as my privileged workstation. It remains part of the MGMT-A allowed set. |
| Secure Client (60) | Internal | End-user workstations | End-user PCs on DHCP: `ObiPC`, last seen at `192.168.60.102`. |
| IDENTITY-A (65) | `AlphaSec-Identity` | Active Directory identity plane | The `ad.alphasecunited.com` guests on grey-server: HQ-DC01 = .10, HQ-DC02 = .11, HQ-MGT01 = .12 (Windows Server 2025) and the HQ-WS001 test workstation = .20. |
| MGMT-A (70) | `AlphaSec-Mgmt` | Hypervisor mgmt plane | Proxmox node management interfaces and hypervisor administration: the registered cluster node IPs from `.10` through `.14`, PVE GUI/API/SSH, and Corosync link0. Out-of-band / IPMI belongs here. |
| Cluster-Net (71) | `AlphaSec-Mgmt` | Cluster interconnect | Proxmox east-west cluster traffic only: Corosync link1 and replication on node IPs `.10` through `.14`. No DHCP, no Internet access, and no general hosts. It shares the management trust zone with MGMT-A but remains a separate broadcast domain. |
| Security-A (72) | `AlphaSec-Observability` | Security and detection | SIEM and log workloads: `security-01` = .2 and `splunk-siem` = .3. It shares the observability posture with MONITOR-A. Egress is limited to web and NTP from the three-member `AG-Observability-Hosts` Network List. |
| MONITOR-A (73) | `AlphaSec-Observability` | Monitoring collector | CT 104 `monitor-01` at static 192.168.73.2 runs Prometheus, Grafana, and their backend exporters. DHCP remains enabled from .6 through .254. The shared zone does not merge VLANs 72 and 73. |
| SERVERS-A (80) | `AlphaSec-Servers` | Internal app/data | Internal (non-internet-facing) application and database servers/VMs: app servers and databases (`app-01` = .10, `alpha-prod-01` = .118). |
| Access-A (85) | `AlphaSec-Access` | Ingress / remote access | Network-access, ingress, and remote-access tooling: reverse proxies and VPN/mesh gateways (docker-network = .2 running Nginx Proxy Manager and NetBird). Tightly restricted egress. |

### Placement by Workload

- Phone, tablet, or personal laptop (mine or family) → **Trusted (10)**; the same device when it must egress through ProtonVPN instead → **Proton-WiFi (45)**
- Smart-home gadget, camera, TV, or appliance → **IoT (20)**
- Jedi PC, my privileged workstation at 192.168.50.241 → **Secure (50)**; every end-user PC, using DHCP → **Secure Client (60)**
- HQ-DC01, HQ-DC02, HQ-MGT01 and domain test workstations on grey-server → **IDENTITY-A (65)**
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
| AD-SERVERS (65) | 2026-07-27 | The Windows domain, both domain controllers, and the domain-joined test VM were retired. VLAN 65 was reused for IDENTITY-A on 2026-09-07. | [Windows Servers retirement](../../../../Archive/Platforms/Windows%20Servers/README.md) |
| DMZ-A (90) | 2026-08-29 | Empty since `edge-01` moved to DMZ (30) on 2026-08-07; no clients, policy, route, port forward or profile reference. | [DMZ-A VLAN 90 Removal](../Documentation/Change%20Records/DMZ-A%20VLAN%2090%20Removal%20-%202026-08-29.md) |
| Secure-V (100) | 2026-07-27 | Its domain SSID was already gone. I deleted the `Non-tracking` ProtonVPN route first, then removed the unused network. | [Zone and Object Consolidation](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md) |
| KASM-BROWSER (74) | 2026-08-19 | The disposable browser lane ended with the Kasm platform. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| KASM-TRUSTED (75) | 2026-08-19 | The trusted disposable-session lane ended with the Kasm platform. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| MALWARE-OFFLINE (77) | 2026-08-19 | The offline detonation lane ended with the Kasm platform. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| LAB-MGMT (78) | 2026-08-19 | VM 122 and its isolated control-plane network were destroyed. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| EVIDENCE-QUARANTINE (79) | 2026-08-19 | The evidence-review lane ended with the Kasm platform. | [Kasm Workspaces decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |

The `Alpha-Sec-IoT` WLAN (earlier records spell it `AlphaSec-IoT`) points to IoT/VLAN 20 and was disabled on the 2026-09-06 WLAN readback.

## Records

- [Proton-WiFi VLAN 45](../Documentation/Change%20Records/Proton-WiFi%20VLAN%2045%20-%202026-08-10.md), 2026-08-10
- [DMZ-A VLAN 90 Removal](../Documentation/Change%20Records/DMZ-A%20VLAN%2090%20Removal%20-%202026-08-29.md), 2026-08-29
- [Galaxy PXE provisioning service](../../../../Platforms/Galaxy%20PXE/Documentation/Change%20Records/Provisioning%20Service%20-%202026-07-30.md), 2026-07-30: `Server-Provision` VLAN 5 on `Proxmox-Trunk`
- [Documentation Staleness Audit](../../../../Operations/Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md), 2026-09-06: full network readback
