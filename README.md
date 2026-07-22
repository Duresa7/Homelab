# My Homelab

**Created:** 2026-07-09  
**Last updated:** 2026-07-21

![Proxmox VE](https://img.shields.io/badge/Proxmox_VE-4--node_cluster-E57000?logo=proxmox&logoColor=white)
![UniFi](https://img.shields.io/badge/UniFi-14_networks,_12_zones-0559C9?logo=ubiquiti&logoColor=white)
![Splunk](https://img.shields.io/badge/Splunk-Enterprise_10.4_SIEM-000000?logo=splunk&logoColor=white)
![Wazuh](https://img.shields.io/badge/Wazuh-security_monitoring-3585BB)
![Prometheus](https://img.shields.io/badge/Prometheus-7_scrape_jobs-E6522C?logo=prometheus&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare-DNS_+_Tunnel-F38020?logo=cloudflare&logoColor=white)
![Ansible](https://img.shields.io/badge/Ansible-18_Semaphore_templates-EE0000?logo=ansible&logoColor=white)
![NetBird](https://img.shields.io/badge/NetBird-WireGuard_mesh-F78F1E)

This repository documents my four-node Proxmox cluster, segmented UniFi network, deployed platforms, automation, monitoring, & security work. The [walkthrough guides](Guides/README.md) are the quickest way to follow a build from its first command to the checks I ran afterward.

## Start Here

- [Guides](Guides/README.md): chronological walkthroughs with commands, screenshots, checks, recovery notes, & links to the original records.
- [Lab architecture](#lab-architecture): the environment in one view.
- [Repository layout](#repository-layout): where the detailed records and configuration live.
- [Build and change records](#build-and-change-records): longer records for several completed projects.
- [Roadmap](#roadmap): the current work queue.

## Lab architecture

[![Homelab architecture: two WAN uplinks and Cloudflare in front of a UniFi zone-based firewall, the four-node Galaxy Proxmox cluster, and workload VLANs for security, access, and applications](Architecture/Diagrams/homelab-overview.svg)](Architecture/Diagrams/homelab-overview.svg)

Traffic enters through two WAN uplinks. Cloudflare Tunnel carries the published HTTP services without an inbound port forward. The UniFi gateway enforces zone policy across 14 networks and 12 zones. The Galaxy cluster hosts the workloads; UniFi sends CEF events to Splunk on Security-A, Wazuh watches the app and edge hosts, & Prometheus scrapes the cluster, edge, and security targets.

## Repository layout

The guides provide the reading path. Detailed records stay with the system that owns the work, and screenshots remain beside the change that produced them.

| Category | What it holds | Example |
|---|---|---|
| [Guides](Guides/README.md) | Visitor walkthroughs across infrastructure and platforms | [Galaxy Proxmox Cluster](Guides/Galaxy-Proxmox-Cluster.md) |
| [Governance](Governance/README.md) | Documentation rules and naming conventions | [Documentation Standard](Governance/Documentation-Standard.md) |
| [Architecture](Architecture/README.md) | Environment-wide designs and research | [Persistent remote development research](Architecture/Remote-AI-Development-Research-2026-07-12.md) |
| [Infrastructure](Infrastructure/README.md) | Network, compute cluster, and physical hardware | [Galaxy cluster](Infrastructure/Compute/Galaxy/README.md) |
| [Platforms](Platforms/README.md) | Deployed services with their docs, config, and source | [Splunk SIEM build log](Platforms/Splunk/Splunk%20Enterprise/Documentation/Build-Log.md) |
| [Engineering](Engineering/README.md) | Shared automation and pre-deployment projects | Currently empty by design |
| [Operations](Operations/README.md) | Cross-system inventories and maintenance records | [Galaxy inventory](Operations/Inventory/Galaxy/Galaxy%20Inventory.md) |
| [Security](Security/README.md) | Incident reports, hardening standards, assessments | [Linux host baseline](Security/Hardening/Linux-Host-Baseline-Standard.md) |
| [Archive](Archive/README.md) | Superseded records kept for history | Currently empty by design |

## Build and Change Records

| Record | What it covers |
|---|---|
| [Splunk SIEM build log](Platforms/Splunk/Splunk%20Enterprise/Documentation/Build-Log.md) | Rocky Linux VM, Splunk Enterprise 10.4.0, HEC, SC4S, UniFi CEF ingestion, `netops` routing, & 40 screenshots |
| [Security-A migration](Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md) | VLAN 72, the Security-A zone, address changes, firewall policy, service moves, & post-migration checks |
| [Galaxy Corosync link addition](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md) | VLAN 71 interfaces, Corosync `link1`, four-node rollout, quorum checks, & link-failure tests |
| [April 2026 incident response](Security/Incidents/security-incident-response-2026-04-19.md) | Review, containment, corrective actions, service validation, & closure after the Vercel disclosure |
| [TeamSpeak UDP relay outage](Security/Incidents/TeamSpeak-Incident-Report-2026-04-24-UDP-Relay-Outage.md) | UDP relay symptoms, Docker proxy diagnosis, network-path rebuild, & voice checks |
| [NetBird routed VPN path](Platforms/Netbird/Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md) | First peer enrollment, routed resource, access policy, routing peer, masquerade, & HTTPS tunnel test |
| [SSH authorized-key cleanup](Operations/Maintenance/SSH%20Authorized%20Key%20Cleanup%20-%202026-07-14.md) | Nineteen-host inventory, 15 reachable targets, fingerprint comparison, authorized-key cleanup, & final access checks |

## Roadmap

Current priorities from my [central TODO](TODO.md):

1. Lock down MGMT-A per the [network segmentation plan](Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md).
2. Finish the media stack's operations backlog: backups and a restore test, capacity alerts, an update cadence, and the HTTPS ingress decision. The end-to-end acquisition test passed on 2026-07-21.
3. Give the SIEM a proper domain name and put a reverse proxy with a CA-signed certificate in front of Splunk Web.
4. Continue Splunk ES data readiness: scope the CIM data models to the indexes in use.
