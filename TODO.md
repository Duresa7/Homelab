# Homelab TODO

**Created:** 2026-07-09  
**Last updated:** 2026-07-17

This is the central workspace backlog. Keep high-level priorities and links here; maintain detailed implementation steps in the owning infrastructure or platform TODO so work is not duplicated.

## Inbox

_No untriaged items._

## Active Priorities

- [ ] Plan the bounded MGMT-A lockdown in the [UniFi network segmentation plan](Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md).

## System Backlogs

- [Ansible TODO](Platforms/Ansible/Documentation/TODO.md) — currently has no open platform items
- [Galaxy TODO](Infrastructure/Compute/Galaxy/Documentation/TODO.md) — includes the deferred recurring `pvestatd` failure on `blue-server`
- [Media Stack TODO](Platforms/Media%20Stack/Documentation/TODO.md) — remaining bounded end-to-end acquisition test plus the operations backlog
- [Splunk Enterprise TODO](Platforms/Splunk/Splunk%20Enterprise/Documentation/TODO.md)
- [Splunk Enterprise Security TODO](Platforms/Splunk/Splunk%20ES/Documentation/TODO.md)
- [UniFi network segmentation TODO](Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md)
- [NetBird TODO](Platforms/Netbird/Documentation/TODO.md)
- [Nginx Proxy Manager TODO](Platforms/Nginx%20Proxy%20Manager/Documentation/TODO.md)
- [Prometheus TODO](Platforms/Prometheus/Documentation/TODO.md)
- [Wazuh TODO](Platforms/Wazuh/Documentation/TODO.md)

## Recently Completed

- [x] 2026-07-17 — [Media Stack application onboarding](Platforms/Media%20Stack/Documentation/Change%20Records/Media%20Stack%20Application%20Onboarding%20-%202026-07-17.md): Jellyfin libraries and Quick Sync transcoding, Sonarr/Radarr media management, first Prowlarr indexer, and confirmed Seerr connections, evidenced by 16 screenshots; the bounded end-to-end acquisition test remains in the platform TODO
- [x] 2026-07-14 — [SSH authorized-key baseline cleanup](Operations/Maintenance/SSH%20Authorized%20Key%20Cleanup%20-%202026-07-14.md): removed two retired keys across every readable scope, normalized 15 reachable targets to the three-key fleet baseline, and placed five verified private identities under 1Password custody
- [x] 2026-07-14 — [Termix SSH host onboarding](Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md): dedicated encrypted Termix identity, nine verified hosts, four-folder inventory, and a TCP/22-only Galaxy firewall path for the four Proxmox nodes
- [x] 2026-07-14 — [Ansible and Semaphore upgrade](Platforms/Ansible/Documentation/Change%20Records/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14.md): Ansible 14.2.0/core 2.21.2, Semaphore 2.18.27, verified recovery backups, systemd startup, and Proxmox LXC auto-start
- [x] 2026-07-14 — [Ansible SSH identity automation](Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md): portable per-identity audit/onboard/stage/verify/retire playbooks, safety gates, and 18 Semaphore templates using the retained encrypted controller credential
- [x] 2026-07-13 — [Galaxy datacenter firewall IPSet restructure](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Datacenter%20Firewall%20IPSet%20Restructure%20-%202026-07-13.md): reorganized `pve_mgmt` into IPSets, narrowed management-VLAN `8006` to the cluster nodes, and removed the redundant `grey-server` host.fw
- [x] 2026-07-13 — [Wazuh endpoint re-enrollment](Platforms/Wazuh/Documentation/Change%20Records/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13.md): fresh `app-01` and `edge-01` identities active as IDs `004` and `005`
- [x] 2026-07-13 — [Wazuh endpoint agent removal](Platforms/Wazuh/Documentation/Change%20Records/Wazuh%20Endpoint%20Agent%20Removal%20-%202026-07-13.md): purged `app-01` and `edge-01` agent packages and client data for clean operator reinstall
- [x] 2026-07-13 — [Security monitoring baseline cleanup](Platforms/Prometheus/Documentation/Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md): Proxmox exporter coverage, Wazuh registration reset, and seven healthy Prometheus jobs
- [x] 2026-07-12 — [Security-A migration of Wazuh/monitoring and Splunk SIEM from MGMT-A to VLAN 72](Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md), including verified UniFi CEF ingestion at the new SIEM address
- [x] 2026-07-12 — [NetBird/NPM operational follow-ups and hardening descope](Platforms/Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md)
- [x] 2026-07-12 — [NetBird first peer and routed VPN path into Access-A](Platforms/Netbird/Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md)
- [x] 2026-07-11 — [NetBird and Nginx Proxy Manager HTTPS access stack on `docker-network`](Platforms/Netbird/Documentation/Deployment.md)
- [x] [Galaxy docker-network LXC and Access-A egress foundation](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Docker-Network%20LXC%20Deployment%20-%202026-07-10.md)
- [x] [Galaxy Cluster-Net Corosync link addition](Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md)
- [x] [Enterprise workspace restructure](Governance/Change%20Records/Workspace%20Enterprise%20Restructure%20-%202026-07-09.md)
- [x] [TNIO and Windows working-tree organization](Governance/Change%20Records/Platform%20Working%20Tree%20Reorganization%20-%202026-07-09.md)
