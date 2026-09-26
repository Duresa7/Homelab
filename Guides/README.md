# Homelab Guides

**Created:** 2026-07-20  
**Last updated:** 2026-09-25

![Lab map: the guides placed on the layer of the lab each one builds](../Assets/Diagrams/lab-map.svg)

Each guide is one build in the order I ran it, with the commands and the output I checked. The dated records it links under Source Records hold the full detail.

`Verified` means the guide's Current Status section was checked against the running system on the date given. `Partial` would name the check still open; no guide is Partial today.

## Guides

| Guide | What it builds | Status |
|---|---|---|
| [Galaxy Proxmox Cluster](Galaxy-Proxmox-Cluster.md) | Joining nodes, Corosync link1 on VLAN 71, Datacenter firewall objects, the first Docker LXC | Verified 2026-09-24 |
| [UniFi Network](UniFi-Network.md) | VLANs and zones, the Security-A migration, Access-A egress order, local DNS, identity-zone NTP and client DNS | Verified 2026-09-24 |
| [Linux Host Baseline](Linux-Host-Baseline.md) | Package updates, one admin account, three SSH keys, key-only SSH, root password behind `Defaults rootpw`, locale | Verified 2026-09-07 |
| [SSH Key Lifecycle](SSH-Key-Lifecycle.md) | Key inventory, fleet cleanup, onboarding, staged rotation, retirement | Verified 2026-09-24 |
| [Ansible SSH Identity Automation](Ansible-SSH-Identity-Automation.md) | The controller, identity files, audit, onboarding, rotation, Semaphore templates | Verified 2026-09-24 |
| [Active Directory](Active-Directory.md) | Two domain controllers, site and subnets, DNS, tiered OUs, password policy, Windows LAPS, a member server, an offline workstation join | Verified 2026-09-09 |
| [Nginx Proxy Manager](Nginx-Proxy-Manager.md) | Compose deployment, the shared `proxy` network, the DNS-01 wildcard certificate, renewal | Verified 2026-09-24 |
| [NetBird](NetBird.md) | Self-hosted control plane behind NPM, first peer, routed path into VLAN 85 | Verified 2026-09-24 |
| [Prometheus](Prometheus.md) | Node exporters, config validation, the bind-mount reload trap, exact target assertions | Verified 2026-09-24 |
| [Splunk](Splunk.md) | Rocky VM, Splunk Enterprise 10.4.0, HEC, SC4S, UniFi CEF into `netops`, Enterprise Security | Verified 2026-09-24 |
| [Wazuh](Wazuh.md) | Manager health, agent enrollment, network checks, endpoint retirement | Verified 2026-09-24 |
| [Wazuh Alerts in Splunk](Wazuh-Alerts-in-Splunk.md) | Universal Forwarder on 9997, file-integrity groups, malware detection two ways, CIM mapping, one dashboard | Verified 2026-09-24 |
| [Media Stack](Media-Stack.md) | Jellyfin, Seerr, Sonarr, Radarr, Prowlarr, qBittorrent behind Gluetun, one request-to-play test | Verified 2026-09-24 |
| [Immich Storage Migration](Immich-Storage-Migration.md) | Moving the Immich library from a 4 TB WD pool to a 2 TB Toshiba pool | Verified 2026-09-24 |
| [Security Incident Response](Security-Incident-Response.md) | Scope, containment, credential rotation, service checks, residual risk, closure | Verified 2026-09-25 |

## Archived guides

| Guide | Retired |
|---|---|
| [TeamSpeak, three-server layout](../Archive/Guides/TeamSpeak.md) | 2026-08-09 |
| [Portainer](../Archive/Guides/Portainer.md) | 2026-09-16, replaced by [Dockhand](../Platforms/Dockhand/README.md) |
| [Termix](../Archive/Guides/Termix.md) | 2026-07-28 |
| [OpenClaw](../Archive/Guides/OpenClaw.md) | 2026-07-25, CT 104 `ai-alpha-01` deleted |
| [TNIO AI Bot](../Archive/Guides/TNIO-AI-Bot.md) | 2026-07-25, CT 105 `ai-bravo-02` deleted 2026-08-09 |
