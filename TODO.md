# Homelab TODO

**Created:** 2026-07-09  
**Last updated:** 2026-07-22

This file is my central backlog and index. It holds active priorities plus links to system backlogs; implementation steps stay in the owning system's TODO.

## Inbox

_No untriaged items._

## Active Priorities

- [ ] Plan the bounded MGMT-A lockdown in the [UniFi network segmentation plan](Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md).
- [ ] Build the isolated security lab (malware detonation & pentest practice) per the [isolated security lab plan](Architecture/Isolated-Security-Lab.md). Planning phase: VLAN, guests, & firewall rules not yet created.

## System Backlogs

| Backlog | Open items |
|---|---|
| [Agent Sandbox](Platforms/Agent%20Sandbox/Documentation/Agent%20Sandbox%20Plan.md) | On-demand throwaway VM & Docker sandbox for AI agents; design locked 2026-07-20, build not started |
| [Ansible](Platforms/Ansible/Documentation/TODO.md) | Add supabase-01 & the AI hosts to fleet-update compose group; decide sudo-password handling for OS updates |
| [Galaxy](Infrastructure/Compute/Galaxy/Documentation/TODO.md) | Includes the deferred recurring `pvestatd` failure on `blue-server` |
| [Media Stack](Platforms/Media%20Stack/Documentation/TODO.md) | Operations backlog: configuration backup and restore test, NVMe/HDD capacity alerts, update cadence, & the HTTPS ingress decision |
| [Syncthing](Platforms/Syncthing/Documentation/TODO.md) | Pair the laptop and add a recurring independent vault backup |
| [Splunk Enterprise](Platforms/Splunk/Splunk%20Enterprise/Documentation/TODO.md) | SIEM domain name, then a reverse proxy with a CA-signed certificate in front of the web UI |
| [Splunk Enterprise Security](Platforms/Splunk/Splunk%20ES/Documentation/TODO.md) | Post-install data readiness and CIM scoping |
| [UniFi network segmentation](Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md) | Segmentation plan and MGMT-A lockdown |
| [NetBird](Platforms/Netbird/Documentation/TODO.md) | No open items after the 2026-07-12 descope |
| [Nginx Proxy Manager](Platforms/Nginx%20Proxy%20Manager/Documentation/TODO.md) | No open items after the 2026-07-12 descope |
| [Prometheus](Platforms/Prometheus/Documentation/TODO.md) | No open baseline items; future monitoring changes land here first |
| [Wazuh](Platforms/Wazuh/Documentation/TODO.md) | No pending enrollments; `app-01` and `edge-01` are the only intended endpoints |

## Recently Completed

- [x] 2026-07-22: [PeaNUT UPS dashboard deployment](Platforms/PeaNUT/Documentation/Change%20Records/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22.md). I deployed read-only NUT 2.8.1-5 telemetry on Red and Grey and an authenticated, digest-pinned PeaNUT 6.0.0 dashboard on `docker-main`; both UPS feeds and existing Docker workloads passed verification.
- [x] 2026-07-22: [Syncthing Obsidian vault deployment](Platforms/Syncthing/Documentation/Deployment.md). I deployed Syncthing 2.1.2 on `docker-main`, paired the Windows vault over direct TLS 1.3, matched a 14-file, 6,425,692-byte canonical manifest on both peers, proved both transfer directions, & retained a deleted test file through 90-day staggered versioning.
- [x] 2026-07-22: [Media Stack HDD data migration](Platforms/Media%20Stack/Documentation/Change%20Records/Media%20Stack%20HDD%20Data%20Migration%20-%202026-07-22.md). I moved 10,615,586,954 logical bytes from CT 842's NVMe root to a 1 TB ext4 HDD, preserved all 19 file hashes & metadata, proved hard links and Quick Sync output on the new filesystem, blocked startup when the disk was absent, & reclaimed 9.9 GiB from NVMe.
- [x] 2026-07-21: [Media Stack end-to-end acquisition test](Platforms/Media%20Stack/Documentation/Change%20Records/Media%20Stack%20Application%20Onboarding%20-%202026-07-17.md). A television episode and a movie were acquired through the stack, hard-link imported, and played from Jellyfin with the GPU active, closing the application onboarding project; the acquisition capture is retained locally. The operations backlog (backups, capacity, update cadence, HTTPS ingress) continues in the [platform TODO](Platforms/Media%20Stack/Documentation/TODO.md).
- [x] 2026-07-20: [Ansible fleet update automation](Platforms/Ansible/Documentation/Change%20Records/Fleet%20Update%20Automation%20-%202026-07-20.md). Two playbooks on `ansible-01`: `os-update.yml` patches 10 Linux guests through apt or dnf with report-only reboots, & `docker-compose-update.yml` pulls and recreates the compose stacks on docker-main, docker-network, & alpha-prod-01. Proxmox nodes and Windows hosts excluded by design. Verified with no-change dry runs; an independent Codex review found and I fixed four reboot-path defects.
- [x] 2026-07-17: [Media Stack application onboarding](Platforms/Media%20Stack/Documentation/Change%20Records/Media%20Stack%20Application%20Onboarding%20-%202026-07-17.md). Jellyfin libraries and Quick Sync transcoding, Sonarr/Radarr media management, first Prowlarr indexer, and confirmed Seerr connections, evidenced by 16 screenshots. The bounded end-to-end acquisition test remains in the platform TODO.
- [x] 2026-07-14: [SSH authorized-key baseline cleanup](Operations/Maintenance/SSH%20Authorized%20Key%20Cleanup%20-%202026-07-14.md). I removed two retired keys across every readable scope, normalized 15 reachable targets to the three-key fleet baseline, and matched five retained identities to their known public fingerprints.
- [x] 2026-07-14: [Termix SSH host onboarding](Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md). One reusable Ed25519 identity, nine verified hosts, four folders, & a TCP/22-only Galaxy firewall path for the four Proxmox nodes.
- [x] 2026-07-14: [Ansible and Semaphore upgrade](Platforms/Ansible/Documentation/Change%20Records/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14.md). Ansible 14.2.0/core 2.21.2, Semaphore 2.18.27, recovery backups, systemd startup, & Proxmox LXC auto-start.
- [x] 2026-07-14: [Ansible SSH identity automation](Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md). Per-identity audit, onboard, stage, verify, & retire playbooks with safety gates and 18 Semaphore templates.
- [x] 2026-07-13: [Galaxy datacenter firewall IPSet restructure](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Datacenter%20Firewall%20IPSet%20Restructure%20-%202026-07-13.md). I reorganized `pve_mgmt` into IPSets, narrowed management-VLAN `8006` to the cluster nodes, and removed the redundant `grey-server` host.fw.
- [x] 2026-07-13: [Wazuh endpoint re-enrollment](Platforms/Wazuh/Documentation/Change%20Records/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13.md). Fresh `app-01` and `edge-01` identities active as IDs `004` and `005`.
- [x] 2026-07-13: [Wazuh endpoint agent removal](Platforms/Wazuh/Documentation/Change%20Records/Wazuh%20Endpoint%20Agent%20Removal%20-%202026-07-13.md). I purged the `app-01` and `edge-01` agent packages and client data for a clean reinstall.
- [x] 2026-07-13: [Security monitoring baseline cleanup](Platforms/Prometheus/Documentation/Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md). Proxmox exporter coverage, Wazuh registration reset, and seven healthy Prometheus jobs.
- [x] 2026-07-12: [Security-A migration of Wazuh/monitoring and Splunk SIEM from MGMT-A to VLAN 72](Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md), including verified UniFi CEF ingestion at the new SIEM address.
- [x] 2026-07-12: [NetBird/NPM operational follow-ups and hardening descope](Platforms/Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).
- [x] 2026-07-12: [NetBird first peer and routed VPN path into Access-A](Platforms/Netbird/Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).
- [x] 2026-07-11: [NetBird and Nginx Proxy Manager HTTPS access stack on `docker-network`](Platforms/Netbird/Documentation/Deployment.md).
- [x] 2026-07-10: [Galaxy docker-network LXC and Access-A egress foundation](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Docker-Network%20LXC%20Deployment%20-%202026-07-10.md).
- [x] 2026-07-10: [Galaxy Cluster-Net Corosync link addition](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md).
- [x] 2026-07-09: [Enterprise workspace restructure](Governance/Change%20Records/Workspace%20Enterprise%20Restructure%20-%202026-07-09.md).
- [x] 2026-07-09: [TNIO and Windows working-tree organization](Governance/Change%20Records/Platform%20Working%20Tree%20Reorganization%20-%202026-07-09.md).
