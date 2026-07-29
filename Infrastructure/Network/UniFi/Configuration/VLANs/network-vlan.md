# UniFi Networks and VLANs

**Created:** 2026-07-09  
**Last updated:** 2026-07-28

I verified this table against the controller after the [Kasm workspace build-out](../../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md) on 2026-07-28. Nineteen routed LAN networks remain. The controller reports 27 network objects when I include two WANs, the ProtonVPN client, and five remote-user VPN networks.

I deleted AD-SERVERS/65 and `Secure-V`/100 on 2026-07-27. The Active Directory retirement removed VLAN 65 and its three guests. The consolidation removed the `Non-tracking` route before deleting VLAN 100. Neither network is part of current placement.

## Networks / VLANs

| Network | VLAN ID | Subnet | Gateway IP | DHCP Range | Router |
|---|---|---|---|---|---|
| Management | (untagged) | 192.168.1.0/24 | 192.168.1.1 | .6 – .254 | Ahsoka Gateway |
| Trusted | 10 | 192.168.10.0/24 | 192.168.10.1 | .6 – .254 | Ahsoka Gateway |
| IoT | 20 | 192.168.20.0/24 | 192.168.20.1 | .6 – .254 | Ahsoka Gateway |
| DMZ | 30 | 192.168.30.0/24 | 192.168.30.1 | .6 – .254 | Ahsoka Gateway |
| Personal-A | 40 | 192.168.40.0/24 | 192.168.40.1 | .100 – .254 | Ahsoka Gateway |
| Secure | 50 | 192.168.50.0/24 | 192.168.50.1 | .6 – .254 | Ahsoka Gateway |
| Secure Client | 60 | 192.168.60.0/24 | 192.168.60.1 | .6 – .254 | Ahsoka Gateway |
| MGMT-A | 70 | 192.168.70.0/24 | 192.168.70.1 | .50 – .200 | Ahsoka Gateway |
| Cluster-Net | 71 | 192.168.71.0/24 | 192.168.71.1 | none | Ahsoka Gateway |
| Security-A | 72 | 192.168.72.0/24 | 192.168.72.1 | .6 – .254 | Ahsoka Gateway |
| MONITOR-A | 73 | 192.168.73.0/24 | 192.168.73.1 | .6 – .254 | Ahsoka Gateway |
| KASM-BROWSER | 74 | 192.168.74.0/24 | 192.168.74.1 | .100 – .199 | Ahsoka Gateway |
| KASM-TRUSTED | 75 | 192.168.75.0/24 | 192.168.75.1 | .100 – .199 | Ahsoka Gateway |
| MALWARE-OFFLINE | 77 | 192.168.77.0/24 | 192.168.77.1 | .100 – .199 | Ahsoka Gateway |
| LAB-MGMT | 78 | 192.168.78.0/24 | 192.168.78.1 | none | Ahsoka Gateway |
| EVIDENCE-QUARANTINE | 79 | 192.168.79.0/24 | 192.168.79.1 | .100 – .199 | Ahsoka Gateway |
| SERVERS-A | 80 | 192.168.80.0/24 | 192.168.80.1 | .6 – .254 | Ahsoka Gateway |
| Access-A | 85 | 192.168.85.0/24 | 192.168.85.1 | .6 – .254 | Ahsoka Gateway |
| DMZ-A | 90 | 192.168.90.0/24 | 192.168.90.1 | .50 – .100 | Ahsoka Gateway |

## Purpose and Device Placement

I use this table when placing a new device or workload. The **Zone** column names the [firewall zone](../Zones/zone.md) that controls its network paths. Names ending in **`-A`** belong to the segmented `<YOUR_ORG_NAME>` infrastructure tier, while unsuffixed VLANs serve household and general lab devices. The examples reflect controller state but don't list every client.

| Network (VLAN) | Zone | Trust tier | What belongs here: device types and examples |
|---|---|---|---|
| Management (untagged) | Internal | Infrastructure mgmt plane | Network fabric and appliances only: the UniFi gateway, switches, access points, and UniFi Protect cameras. I don't park general clients or servers here. |
| Trusted (10) | Internal | Trusted personal | Personal devices I trust but that are not admin machines: household phones, tablets, laptops, watches, and personal streaming/voice devices (iPhones, Pixels, MacBooks, Galaxy Watch, personal Fire TV / Alexa). Blocked from reaching Personal-A. |
| IoT (20) | Untrusted | Untrusted appliance | Smart-home and appliance-class gear with no admin need and no reason to reach the LAN: smart cameras (Wyze, Ring), thermostats (Nest), smart TVs and streamers (Samsung TV, Roku), smart appliances (Samsung FamilyHub), plugs and sensors. Isolated from Internal. |
| DMZ (30) | Dmz | Internet-facing (legacy) | General internet-exposed / untrusted workloads kept off the LAN. Blocked from Internal; can be pinned to ProtonVPN egress via the `isolate` policy. I prefer DMZ-A for new `<YOUR_ORG_NAME>` edge hosts. |
| Personal-A (40) | Internal | My lab / utility | My general-purpose lab and utility VMs and containers, **not** household user devices: Docker hosts (`docker-main`, `docker-blue`, `media-01`), automation (`ansible-01`), & pentest or development VMs (`kali-pen`, `debian-dev`). Reachable only from a defined admin device allow-list. |
| Secure (50) | Internal | Primary admin workstation | The trusted workstation I administer the homelab from: my main management PC, Jedi PC. Part of the MGMT-A allowed set. |
| Secure Client (60) | Internal | Secondary trusted workstation | Additional trusted desktops or workstations for specific users that need LAN trust but are not my primary admin box. |
| MGMT-A (70) | `<YOUR_ORG_NAME>`-Mgmt | Hypervisor mgmt plane | Proxmox node management interfaces and hypervisor administration: the cluster node mgmt IPs (grey/purple/blue/red = .10–.13), PVE GUI/API/SSH, Corosync link0. Out-of-band / IPMI belongs here. |
| Cluster-Net (71) | `<YOUR_ORG_NAME>`-Mgmt | Cluster interconnect | Proxmox east-west cluster traffic only: Corosync link1 and replication (node IPs .10–.13). No DHCP, no Internet access, and no general hosts. It shares the management trust zone with MGMT-A but remains a separate broadcast domain. |
| Security-A (72) | `<YOUR_ORG_NAME>`-Observability | Security and detection | SIEM and log workloads: `security-01` = .2 and `splunk-siem` = .3. It shares the observability posture with MONITOR-A. Egress is limited to approved web and NTP from the three-member observability object. |
| MONITOR-A (73) | `<YOUR_ORG_NAME>`-Observability | Monitoring collector | CT 104 `monitor-01` at static 192.168.73.2 runs Prometheus, Grafana, and their backend exporters. DHCP remains enabled from .6 through .254. The shared zone does not merge VLANs 72 and 73. |
| KASM-BROWSER (74) | KASM-BROWSER | Lab tools | Kasm browser containers and pentest tooling use `192.168.74.208/28` through the `lab74` macvlan network. Proton egress with the kill switch on is supplied by `KASM Lab Proton Egress`. |
| KASM-TRUSTED (75) | KASM-TRUSTED | Trusted disposable sessions | Claude Code, Codex CLI, and Terminal sessions use `192.168.75.208/28` through `lab75`. They have ordinary WAN egress, no access to the other session lanes, and persistent storage only through their assigned per-user profile directories. |
| MALWARE-OFFLINE (77) | MALWARE-OFFLINE | Detonation & targets | Disposable Linux samples and targets use `192.168.77.208/28` through `lab77`. External egress is blocked and DHCP no longer advertises the retired `.10` resolver. |
| LAB-MGMT (78) | LAB-MGMT | Isolated control plane | VM 122 `kasm-01` uses static `192.168.78.10/24`. DHCP is disabled. Only Trusted, Personal-A, and the Management Access VPN may reach TCP 22 and 443. |
| EVIDENCE-QUARANTINE (79) | EVIDENCE-QUARANTINE | Evidence review | Disposable review sessions use `192.168.79.208/28` through `lab79`. They have no Internet and no routed path to another session lane. |
| SERVERS-A (80) | `<YOUR_ORG_NAME>`-Servers | Internal app/data | Internal (non-internet-facing) application and database servers/VMs: app servers, databases (app-01 = .10, supabase-01 = .20, db-13-host = .228). |
| Access-A (85) | `<YOUR_ORG_NAME>`-Access | Ingress / remote access | Network-access, ingress, and remote-access tooling: reverse proxies and VPN/mesh gateways (docker-network = .2 running Nginx Proxy Manager and NetBird). Tightly restricted egress. |
| DMZ-A (90) | Dmz | Internet-facing edge | `<YOUR_ORG_NAME>` public-facing edge workloads that accept inbound from the internet (edge-01 = .10), monitored from Security-A. Blocked from reaching Internal. |

### Placement by Workload

- Phone, tablet, or personal laptop (mine or family) → **Trusted (10)**
- Smart-home gadget, camera, TV, or appliance → **IoT (20)**
- Workstation I manage the lab from → **Secure (50)**; another user's trusted desktop → **Secure Client (60)**
- Proxmox node management IP → **MGMT-A (70)**; that node's Corosync/cluster link → **Cluster-Net (71)**
- Internal application or database VM → **SERVERS-A (80)**
- Security or logging tool → **Security-A (72)**; the central monitoring collector → **MONITOR-A (73)**. Both use the `<YOUR_ORG_NAME>`-Observability zone.
- Kasm control plane → **LAB-MGMT (78)**; Kasm sessions → **KASM-BROWSER (74)**, **KASM-TRUSTED (75)**, **MALWARE-OFFLINE (77)**, or **EVIDENCE-QUARANTINE (79)** according to their workspace override
- Reverse proxy, VPN, or remote-access ingress → **Access-A (85)**
- Public / internet-facing service → **DMZ-A (90)** (legacy: **DMZ (30)**)
- General lab, automation, or utility VM/container → **Personal-A (40)**
- Switch, AP, gateway, or Protect camera → **Management (untagged)**

## Retired Networks

| Network | Deleted | Reason | Durable record |
|---|---|---|---|
| AD-SERVERS (65) | 2026-07-27 | The Windows domain, both domain controllers, and the domain-joined test VM were retired. | [Windows Servers retirement](../../../../../Platforms/Windows%20Servers/README.md) |
| Secure-V (100) | 2026-07-27 | Its domain SSID was already gone. I deleted the `Non-tracking` ProtonVPN route first, then removed the unused network. | [Zone and Object Consolidation](../../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md) |

The disabled `<YOUR_ORG_NAME>`-IoT WLAN now points to IoT/VLAN 20. It stayed disabled during the correction.
