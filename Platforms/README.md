# Platforms

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

This directory holds my deployed applications and services, one folder per platform. Versions are the live readback of 2026-09-24 and 2026-09-25 unless the row says otherwise. Retired platforms are in the [Archive](../Archive/README.md).

## Platforms

| Platform | Host | What it does |
|---|---|---|
| [Action1](Action1/README.md) | Cloud, agents on the domain PCs | Endpoint management for `ObiPC`: software deployment, patching and remote access; Deployer on `HQ-MGT01` |
| [Active Directory](Active%20Directory/README.md) | HQ-DC01, HQ-DC02 | The `ad.alphasecunited.com` forest on two Windows Server 2025 domain controllers in IDENTITY-A, VLAN 65 |
| [Ansible](Ansible/README.md) | ansible-01 | ansible-core 2.21.2 and Semaphore 2.18.27: SSH key identities, OS and Compose updates, exporters, host access baseline |
| [App Portal](App%20Portal/README.md) | docker-main | My self-service software catalog for Windows PCs, server 0.6.0 |
| [Azure Arc](Azure%20Arc/README.md) | HQ-MGT01 | Arc agent 1.67.03504.3207, Connected; represents `HQ-MGT01` in Azure |
| [BookLore](BookLore/README.md) | docker-main | Book library, v2.4.0 with MariaDB 11.4.8 |
| [Caddy](Caddy/README.md) | edge-01 | Caddy 2.6.2, the public origin behind the Cloudflare Tunnel (cloudflared 2026.8.3), forwarding to Coolify |
| [CLI Proxy API](CLI%20Proxy%20API/README.md) | docker-main | v7.3.16 at `https://aiproxy.alphasecunited.com` |
| [Coolify](Coolify/README.md) | app-01 | Coolify 4.3.23 with Traefik 3.7.12: builds and publishes the public services |
| [Discord Alert Bot](Discord%20Alert%20Bot/README.md) | monitor-01 | Posts Grafana and Splunk alerts to `#bots` |
| [Docker MCP Gateway](Docker%20MCP%20Gateway/README.md) | docker-blue | Two v0.43.3 gateways, one for UniFi Network MCP and one for SSH Manager MCP |
| [Dockhand](Dockhand/README.md) | docker-main | Dockhand 1.0.48; manages the Docker hosts through six Hawser agents |
| [Executor](Executor/README.md) | docker-blue | Executor 1.6.10, one MCP endpoint in front of SSH Manager, UniFi, Wazuh, Cloudflare and other integrations |
| [Galaxy PXE](Galaxy%20PXE/README.md) | ansible-01 | Bare-metal provisioning for Galaxy Proxmox nodes |
| [Immich](Immich/README.md) | docker-main | Immich 3.2.2, photo library with NVENC transcoding on the GTX 1080 Ti |
| [Media Stack](Media%20Stack/README.md) | media-01 | Jellyfin 12.1.0, Seerr 3.4.1, Sonarr, Radarr, Prowlarr, FlareSolverr and qBittorrent behind Gluetun |
| [MeshCentral](MeshCentral/README.md) | docker-blue | Remote support pilot, running beside RustDesk |
| [Microsoft Intune](Microsoft%20Intune/README.md) | Cloud | Device management for the `alphasecunited.com` tenant |
| [NetBird](Netbird/README.md) | docker-network | NetBird 0.79.0 and dashboard 2.93.0, the WireGuard mesh with a routed path into the lab |
| [Nginx Proxy Manager](Nginx%20Proxy%20Manager/README.md) | docker-network | NPM 2.15.1, 24 internal HTTPS hosts on one DNS-01 wildcard certificate |
| [Ollama](Ollama/README.md) | docker-main | Ollama 0.33.3 on the GTX 1080 Ti |
| [Open WebUI](Open%20WebUI/README.md) | docker-main | Open WebUI 0.11.4, the authenticated frontend for Ollama |
| [PeaNUT](PeaNUT/README.md) | monitor-01 | PeaNUT 6.0.0, browser view of the NUT servers on red-server and grey-server |
| [Prometheus](Prometheus/README.md) | monitor-01 | Prometheus 3.14.0 (57 targets in seven jobs) and Grafana 13.2.2 (24 alert rules) |
| [RustDesk](RustDesk/README.md) | docker-blue | Self-hosted remote desktop, `hbbs` and `hbbr` 1.1.16 |
| [Samba](Samba/README.md) | ubuntu-dev | File server for my own machines |
| [Splunk](Splunk/README.md) | splunk-siem | Splunk Enterprise 10.4.0 with Enterprise Security 8.5.1 and SC4S |
| [TeamSpeak Hosting](Teamspeak%20Hosting/README.md) | alpha-prod-01 | Two TeamSpeak 3 Server 3.13.8 instances published through Playit, with TS3 Manager |
| [Wazuh](Wazuh/README.md) | security-01 | Wazuh 4.14.7 manager with 15 active remote agents |
| [Windows Admin Center](Windows%20Admin%20Center/README.md) | HQ-MGT01 | Windows Admin Center 2.7.21.5 |

## Platform layout

Each platform uses only the directories its workload needs:

- `Documentation/`: architecture, change records, runbooks, troubleshooting, and TODOs.
- `Source/`: application source when the project can keep it here safely.
- `Configuration/`: versioned service configuration and reference exports.
- `Scripts/`: deployment, migration, maintenance, and recovery automation.
- `Tests/`: automated validation.
- `Evidence/`: screenshots, exports, logs, and evidence indexes.

When I move active source, I verify its imports, tooling, and deployment path after the change.
