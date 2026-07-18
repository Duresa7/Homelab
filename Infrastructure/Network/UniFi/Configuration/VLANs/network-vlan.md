# Unifi Network

**Created:** 2026-07-09  
**Last updated:** 2026-07-18

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
| AD-SERVERS | 65 | 192.168.65.0/24 | 192.168.65.1 | .6 – .254 | Ahsoka Gateway |
| MGMT-A | 70 | 192.168.70.0/24 | 192.168.70.1 | .50 – .200 | Ahsoka Gateway |
| Cluster-Net | 71 | 192.168.71.0/24 | 192.168.71.1 | none | Ahsoka Gateway |
| Security-A | 72 | 192.168.72.0/24 | 192.168.72.1 | .6 – .254 | Ahsoka Gateway |
| SERVERS-A | 80 | 192.168.80.0/24 | 192.168.80.1 | .6 – .254 | Ahsoka Gateway |
| Access-A | 85 | 192.168.85.0/24 | 192.168.85.1 | .6 – .254 | Ahsoka Gateway |
| DMZ-A | 90 | 192.168.90.0/24 | 192.168.90.1 | .50 – .100 | Ahsoka Gateway |

## Purpose and Device Placement

This table says what each network is for; I use it to decide where a new device or workload belongs. The **Zone** column is the firewall zone the network sits in (see [zones](../Zones/zone.md)); it governs what the network may talk to. Networks with an **`-A`** suffix are the segmented REDACTED_PRIVATE_ORG_LABEL infrastructure tier; each lives in its own custom zone under least-privilege policies. The unsuffixed VLANs are the general household tier. Device examples are drawn from the live controller and are illustrative, not exhaustive.

| Network (VLAN) | Zone | Trust tier | What belongs here: device types and examples |
|---|---|---|---|
| Management (untagged) | Internal | Infrastructure mgmt plane | Network fabric and appliances only: the UniFi gateway, switches, access points, and UniFi Protect cameras. I don't park general clients or servers here. |
| Trusted (10) | Internal | Trusted personal | Personal devices I trust but that are not admin machines: household phones, tablets, laptops, watches, and personal streaming/voice devices (iPhones, Pixels, MacBooks, Galaxy Watch, personal Fire TV / Alexa). Blocked from reaching Personal-A. |
| IoT (20) | Untrusted | Untrusted appliance | Smart-home and appliance-class gear with no admin need and no reason to reach the LAN: smart cameras (Wyze, Ring), thermostats (Nest), smart TVs and streamers (Samsung TV, Roku), smart appliances (Samsung FamilyHub), plugs and sensors. Isolated from Internal. |
| DMZ (30) | Dmz | Internet-facing (legacy) | General internet-exposed / untrusted workloads kept off the LAN. Blocked from Internal; can be pinned to ProtonVPN egress via the `isolate` policy. I prefer DMZ-A for new REDACTED_PRIVATE_ORG_LABEL edge hosts. |
| Personal-A (40) | Internal | My lab / utility | My general-purpose lab and utility VMs and containers, **not** household user devices: Docker hosts (docker-main, docker-grey), automation (ansible-01), AI/experiment boxes (ai-alpha-01), and pentest/lab VMs (kali, debian-vm). Reachable only from a defined admin device allow-list. |
| Secure (50) | Internal | Primary admin workstation | The trusted workstation I administer the homelab from: my main management PC, Jedi PC. Part of the MGMT-A allowed set. |
| Secure Client (60) | Internal | Secondary trusted workstation | Additional trusted desktops/workstations for specific users that need LAN trust but are not my primary admin box (Obi PC). |
| AD-SERVERS (65) | Internal | Identity infrastructure | Active Directory and identity infrastructure plus domain-joined servers/test hosts: Windows domain controllers (WS-DC-1, WS-DC-02), identity/sync services, domain-joined test PCs. |
| MGMT-A (70) | REDACTED_PRIVATE_ORG_LABEL-Mgmt | Hypervisor mgmt plane | Proxmox node management interfaces and hypervisor administration: the cluster node mgmt IPs (grey/purple/blue/red = .10–.13), PVE GUI/API/SSH, Corosync link0. Out-of-band / IPMI belongs here. |
| Cluster-Net (71) | REDACTED_PRIVATE_ORG_LABEL-Cluster | Cluster interconnect | Proxmox east-west cluster traffic only: Corosync link1 and replication (node IPs .10–.13). No DHCP and no general hosts; nothing else should join. |
| Security-A (72) | REDACTED_PRIVATE_ORG_LABEL-Security | Security & monitoring | Security, detection, and monitoring workloads: SIEM, log, and metrics servers (wazuh-01 = .2, splunk-siem = .3). Egress is default-deny except approved web/NTP. |
| SERVERS-A (80) | REDACTED_PRIVATE_ORG_LABEL-Servers | Internal app/data | Internal (non-internet-facing) application and database servers/VMs: app servers, databases (app-01 = .10, supabase-01 = .20, db-13-host = .228). |
| Access-A (85) | REDACTED_PRIVATE_ORG_LABEL-Access | Ingress / remote access | Network-access, ingress, and remote-access tooling: reverse proxies and VPN/mesh gateways (docker-network = .2 running Nginx Proxy Manager and NetBird). Tightly restricted egress. |
| DMZ-A (90) | Dmz | Internet-facing edge | REDACTED_PRIVATE_ORG_LABEL public-facing edge workloads that accept inbound from the internet (edge-01 = .10), monitored from Security-A. Blocked from reaching Internal. |

### Placement Quick Reference

- Phone, tablet, or personal laptop (mine or family) → **Trusted (10)**
- Smart-home gadget, camera, TV, or appliance → **IoT (20)**
- Workstation I manage the lab from → **Secure (50)**; another user's trusted desktop → **Secure Client (60)**
- Proxmox node management IP → **MGMT-A (70)**; that node's Corosync/cluster link → **Cluster-Net (71)**
- Internal application or database VM → **SERVERS-A (80)**
- Security, logging, or monitoring tool → **Security-A (72)**
- Reverse proxy, VPN, or remote-access ingress → **Access-A (85)**
- Public / internet-facing service → **DMZ-A (90)** (legacy: **DMZ (30)**)
- General lab, automation, or utility VM/container → **Personal-A (40)**
- Domain controller, identity server, or domain-joined machine → **AD-SERVERS (65)**
- Switch, AP, gateway, or Protect camera → **Management (untagged)**
