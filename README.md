# AlphaSec United Homelab

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

This is my homelab, AlphaSec United (`alphasecunited.com`): a five-node Proxmox VE cluster behind a zone-segmented UniFi network, running an Active Directory forest, a Wazuh and Splunk security stack, Prometheus and Grafana monitoring, and self-hosted services such as Immich, Jellyfin, Forgejo, Coolify, and TeamSpeak.

![Proxmox VE](https://img.shields.io/badge/Proxmox_VE-5--node_cluster-E57000?logo=proxmox&logoColor=white)
![UniFi](https://img.shields.io/badge/UniFi-16_routed_LANs,_12_zones-0559C9?logo=ubiquiti&logoColor=white)
![Splunk](https://img.shields.io/badge/Splunk-Enterprise_10.4_+_ES-000000?logo=splunk&logoColor=white)
![Wazuh](https://img.shields.io/badge/Wazuh-15_active_remote_agents-3585BB)
![Prometheus](https://img.shields.io/badge/Prometheus-57_targets,_7_jobs-E6522C?logo=prometheus&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare-DNS_+_Tunnel-F38020?logo=cloudflare&logoColor=white)
![Ansible](https://img.shields.io/badge/Ansible-23_Semaphore_templates-EE0000?logo=ansible&logoColor=white)
![NetBird](https://img.shields.io/badge/NetBird-WireGuard_mesh-F78F1E)

[![Homelab overview: Cloudflare and the internet edge in front of the UniFi gateway and its 12 firewall zones, the five Galaxy Proxmox nodes with their 18 guests, and the security, monitoring, identity, and access flows between them](Assets/Diagrams/homelab-overview.svg)](Assets/Diagrams/homelab-overview.svg)

## At a glance

| Area | Current state | Checked |
|---|---|---|
| Cluster | Five Proxmox VE 9.2.11 nodes (grey, purple, blue, red, green), five of five votes, no shared storage, no HA resources | 2026-09-24 |
| Guests | 18 (12 VMs, 6 LXCs) plus 3 templates; 16 running | 2026-09-24 |
| Network | UniFi Network 10.6.106 on the Ahsoka gateway, three switches, one access point; 23 networks, 16 routed LANs in 12 zones | 2026-09-24 |
| Identity | Forest `ad.alphasecunited.com` on `HQ-DC01` and `HQ-DC02` (Windows Server 2025); `HQ-MGT01` runs Windows Admin Center 2.7 and the Entra Cloud Sync agent for Microsoft 365 | 2026-09-25 |
| Security | Wazuh 4.14.7 with 15 remote agents; Splunk Enterprise 10.4.0 with Enterprise Security 8.5.1 and SC4S taking UniFi CEF | 2026-09-24 |
| Monitoring | Prometheus 3.14.0 with 57 targets in 7 jobs, all up; Grafana 13.2.2 with 24 alert rules posting to one Discord channel | 2026-09-24 |
| Access | Public services through a Cloudflare Tunnel to `edge-01`; 24 internal HTTPS names on Nginx Proxy Manager 2.15.1 with a DNS-01 wildcard; NetBird 0.79.0 for remote access | 2026-09-24 |
| Automation | Ansible 14.2.0 and Semaphore 2.18.27 (3 projects, 23 templates); Dockhand 1.0.48 with Hawser agents on six hosts; Executor 1.6.10 in front of the SSH Manager, UniFi, Cloudflare, and Wazuh MCP servers | 2026-09-24 |
| Workstations | Jedi PC, my admin workstation, on Secure VLAN 50; ObiPC, a domain-joined Windows 11 PC on Secure Client VLAN 60, offline since the afternoon of 2026-09-24 | 2026-09-25 |

The current guest list is in the [Galaxy inventory](Operations/Inventory/Galaxy/Galaxy%20Inventory.md).

## Where things live

| Folder | What it holds |
|---|---|
| [Guides](Guides/README.md) | Step-by-step builds for readers |
| [Architecture](Architecture/README.md) | Designs that span several systems |
| [Infrastructure](Infrastructure/README.md) | Network, Proxmox cluster, physical hardware |
| [Platforms](Platforms/README.md) | One folder per deployed service |
| [Engineering](Engineering/README.md) | Shared tooling not run as a service |
| [Operations](Operations/README.md) | Inventories and cross-system maintenance |
| [Security](Security/README.md) | Incident reports and security assessments |
| [Backups](Backups/README.md) | Redacted config copies taken before edits |
| [Archive](Archive/README.md) | Retired systems and superseded records |
| [Assets](Assets/Diagrams/README.md) | The eighteen diagrams and the generator that builds them |

## Start here

1. [Galaxy Proxmox Cluster](Guides/Galaxy-Proxmox-Cluster.md): the five nodes and both Corosync links.
2. [UniFi Network](Guides/UniFi-Network.md): VLANs, zones, and the policy order that holds them apart.
3. [Linux Host Baseline](Guides/Linux-Host-Baseline.md): what every Linux guest gets before it carries a workload.
4. [Active Directory](Guides/Active-Directory.md): two domain controllers, tiered OUs, and Windows LAPS.
5. [Wazuh Alerts in Splunk](Guides/Wazuh-Alerts-in-Splunk.md): endpoint alerts, malware detection, and one Splunk dashboard.

## Open work

The full list is in [TODO.md](TODO.md); closed work is in [COMPLETED.md](COMPLETED.md).

- Repair `green-server`'s memory and activate `win11-dev` ([Galaxy backlog](Infrastructure/Compute/Galaxy/Documentation/TODO.md)).
- Finish the MeshCentral pilot on `docker-blue` ([deployment record](Platforms/MeshCentral/Documentation/Change%20Records/Deployment%20-%202026-09-12.md)).
- Complete the Action1 Deployer on `HQ-MGT01` ([preparation record](Platforms/Action1/Documentation/Change%20Records/AD%20Deployer%20Preparation%20-%202026-09-12.md)).
- Finish the App Portal rollout for ObiPC ([App Portal](Platforms/App%20Portal/README.md)).
- Decide how many of the 16 routed LANs UniFi Threat Management inspects ([Notify and Block record](Infrastructure/Network/UniFi/Documentation/Change%20Records/Detection%20Mode%20to%20Notify%20and%20Block%20-%202026-08-31.md)).
