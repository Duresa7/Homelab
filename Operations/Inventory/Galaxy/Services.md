# Galaxy Services

**Created:** 2026-07-08  
**Last updated:** 2026-07-17

## Summary
| Guest | Type | Node | Role | Key workloads |
| --- | --- | --- | --- | --- |
| ansible-01 | LXC 100 | grey-server | Automation | Ansible 14.2.0 / core 2.21.2<br>Semaphore 2.18.27<br>SSH<br>cron |
| debian-dev | VM 102 | grey-server | Development workstation | GNOME Shell 48.7<br>GDM 48.0<br>Claude Desktop 1.21459.0<br>SSH |
| docker-main | LXC 110 | grey-server | Docker apps | Immich<br>Forgejo<br>Homelab Dashboard<br>Termix / Guacamole<br>Portainer |
| docker-network | LXC 107 | blue-server | Network access control plane | Nginx Proxy Manager 2.15.1<br>NetBird 0.74.4 (control plane + Access-A routing peer) |
| docker-blue | LXC 108 | blue-server | Remote access | RustDesk hbbs / hbbr |
| app-01 | VM 116 | grey-server | App platform | Coolify<br>Traefik<br>Postgres / Redis / Realtime<br>Wazuh agent 4.14.5 |
| edge-01 | VM 121 | grey-server | Edge ingress | Caddy<br>cloudflared<br>Wazuh agent 4.14.5 |
| security-01 / wazuh-01 | VM 200 | grey-server | Security + monitoring (`192.168.72.2`, VLAN 72) | Wazuh<br>Prometheus<br>Grafana<br>Proxmox exporter |
| alpha-prod-01 | VM 401 | grey-server | Voice/game services | TeamSpeak<br>TS3 Manager<br>Playit<br>Portainer Edge Agent |
| splunk-siem | VM 109 | grey-server | SIEM (`192.168.72.3`, VLAN 72) | Splunkd<br>SC4S |
| media-01 | LXC 842 | red-server | Media automation and playback; applications onboarded, end-to-end acquisition test pending | Jellyfin<br>Seerr<br>Sonarr / Radarr / Prowlarr<br>FlareSolverr<br>qBittorrent through Gluetun / Proton VPN |

## ansible-01

| Workload | Details |
| --- | --- |
| Ansible | Control node; community 14.2.0 with ansible-core 2.21.2 selected from `/opt/ansible-current` |
| Semaphore | 2.18.27; systemd enabled/active; HTTP UI on TCP 3000 |
| System services | Semaphore, SSH, cron |
| Containers | No Docker or Podman containers detected |

## debian-dev

| Workload | Details |
| --- | --- |
| GNOME desktop | Debian GNOME metapackages `gnome` and `gnome-core` 48; GNOME Shell 48.7-0+deb13u2 |
| Display manager | GDM 48.0-2; Wayland greeter active; graphical target is the default boot target |
| Network | NetworkManager profile `Wired connection 1` owns `ens18`; autoconnect; static `192.168.40.135/24`; gateway/DNS `192.168.40.1` |
| Desktop privilege policy | Polkit grants all actions without authentication to user `REDACTED_USER_001` only from an active local session; remote Polkit requests remain subject to normal policy |
| Claude Desktop | 1.21459.0 from Anthropic's APT repository; GNOME Keyring/Secret Service supplies encrypted credential storage; fresh login verification pending after first-run collection creation |
| Cowork virtualization | `/dev/kvm` available through AMD KVM; `REDACTED_USER_001` is a persistent member of group `kvm`; new-session activation pending |
| Remote administration | SSH Manager target `debian_dev` (`REDACTED_USER_001@192.168.40.135`) using the Jedi-PC Ed25519 identity; compatibility alias `db_13_test` |
| Rollback | Proxmox snapshot `pre-gnome-20260715` retained on VM 102; post-reboot validation passed |

## docker-main

| Workload | Details |
| --- | --- |
| Immich | Photo/video stack: server, Postgres, machine learning, Valkey |
| Forgejo | Git service: `codeberg.org/forgejo/forgejo:15` |
| Homelab Dashboard | `ghcr.io/REDACTED_REGISTRY_ACCOUNT/homelab-dashboard-aio:latest` |
| Termix / Guacamole | Termix 2.5.0 (`ghcr.io/lukegus/termix:latest`, verified digest `sha256:4d3371311087d6757aa9d1c94117e854d749b1c5e8fd07bd36e7a99e0686d26c`); `guacamole/guacd:1.6.0` |
| Portainer CE | `portainer/portainer-ce:latest` |

## docker-blue

| Workload | Details |
| --- | --- |
| RustDesk | `hbbs` and `hbbr` using `rustdesk/rustdesk-server:latest` |

## docker-network

| Workload | Details |
| --- | --- |
| Nginx Proxy Manager | Version 2.15.1; Docker Compose project under `/opt/docker/nginx-proxy-manager`; administrator initialized; wildcard/apex Let's Encrypt certificate assigned with Force SSL and HTTP/2 |
| NetBird | Version 0.74.4; dashboard and server containers deployed under `/opt/docker/netbird`; authenticated dashboard live at `https://REDACTED_CUSTOM_DOMAIN_016`; also runs as the Access-A routing peer (overlay `100.121.111.204`) advertising the `REDACTED_PRIVATE_ORG_LABEL-Access` network `192.168.85.0/24` |
| Shared proxy network | External Docker network `proxy`, subnet `172.31.85.0/24`; Nginx Proxy Manager uses `172.31.85.10` |
| Operational status | First peer/VPN path, non-interactive ACME renewal, and bounded logging verified; no further hardening tracked after the 2026-07-12 descope decision |

## app-01

| Workload | Details |
| --- | --- |
| Coolify | Coolify app, Sentinel, Realtime, Postgres, Redis |
| Traefik | Coolify ingress proxy: `traefik:v3.6` |
| Generated apps | Opaque Coolify-generated app names omitted |
| Wazuh agent | 4.14.5-1; enabled/active; fresh manager ID `004` as `app-01`; connected to `192.168.72.2:1514` |

## edge-01

| Workload | Details |
| --- | --- |
| Caddy | Web/reverse proxy |
| cloudflared | Cloudflare Tunnel |
| Wazuh agent | 4.14.5-1; enabled/active; fresh manager ID `005` as `edge-01`; connected to `192.168.72.2:1514` |
| Containers | No Docker or Podman runtime detected |

## security-01 / wazuh-01

| Workload | Details |
| --- | --- |
| Wazuh | Manager, indexer, dashboard |
| Prometheus | `prom/prometheus:latest`; seven jobs `UP`: security host, edge host, four Galaxy nodes, and PVE exporter |
| Grafana | `grafana/grafana:latest` |
| Proxmox exporter | `prompve/prometheus-pve-exporter:latest` |
| Network | Static `192.168.72.2/24` on Security-A/VLAN 72 |

## alpha-prod-01

| Workload | Details |
| --- | --- |
| TeamSpeak | Three `teamspeak` containers |
| TS3 Manager | `joni1802/ts3-manager` |
| Playit agent | `ghcr.io/playit-cloud/playit-agent:0.17` |
| Portainer Edge Agent | `portainer/agent:2.39.1` |

## splunk-siem

| Workload | Details |
| --- | --- |
| Splunkd | `Splunkd.service` active |
| SC4S | `sc4s.service` active; Podman host-network container receives CEF on TCP/UDP 1514 and forwards to Splunk HEC over HTTPS 8088 |
| Network | Static `192.168.72.3/24` on Security-A/VLAN 72 |

## media-01

| Workload | Details |
| --- | --- |
| Jellyfin | `jellyfin/jellyfin:latest`; Intel Quick Sync render device available; LAN port 8096 |
| Seerr | `ghcr.io/seerr-team/seerr:latest` 3.3.0; migrated from Jellyseerr with its existing configuration retained; setup wizard completed 2026-07-17 with confirmed Jellyfin, Sonarr, and Radarr connections |
| Arr services | LinuxServer Sonarr, Radarr, and Prowlarr `latest`; Sonarr and Radarr linked to qBittorrent using separate categories; first public indexer added to Prowlarr 2026-07-17 with the Standard sync profile; end-to-end acquisition test pending |
| FlareSolverr | `ghcr.io/flaresolverr/flaresolverr:latest`; internal challenge proxy selected only through the `flaresolverr` Prowlarr tag; real-indexer challenge validation pending |
| Download path | LinuxServer qBittorrent `latest` shares `qmcgaw/gluetun:latest` network namespace; Proton WireGuard, kill switch, and provider-side port synchronization verified; qBittorrent rejects the documented 100-pattern executable/script payload baseline for new torrents |
| Storage | One 100 GiB local LVM root volume contains configuration, downloads, media, and transcodes |
| Network | Static `192.168.40.42` on VLAN 40; no gateway inbound port forward |

## Galaxy Proxmox node monitoring

| Node | Exporter | Service | Endpoint | State |
|---|---|---|---|---|
| grey-server | Manual `node_exporter` 1.9.0 | `node_exporter.service` | `192.168.70.10:9100` | Enabled, active, Prometheus `UP` |
| purple-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.11:9100` | Enabled, active, Prometheus `UP` |
| blue-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.12:9100` | Enabled, active, Prometheus `UP` |
| red-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.13:9100` | Enabled, active, Prometheus `UP` |
