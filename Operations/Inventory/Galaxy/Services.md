# Galaxy Services

**Created:** 2026-07-08  
**Last updated:** 2026-09-25

This inventory maps the workloads on Galaxy's 18 guests: 12 VMs and six LXCs. I read the versions below from the running services on 2026-09-24 and 2026-09-25, through SSH Manager, from each service's version endpoint, its OCI image label, or its package manager. On 2026-09-24 Prometheus scraped 57 targets across seven jobs with all 57 up, the Wazuh manager listed 15 remote agents with all 15 active, and six Docker hosts ran a Hawser Edge agent for Dockhand. A version marked with an earlier date is the last reading I have.

## Recent changes

- 2026-09-24: Weebarr, deployed on `media-01` on 2026-09-21, was absent: no container, image or Compose entry, and its proxy host and DNS record deleted. [Weebarr Retirement](../../../Archive/Platforms/Weebarr/Documentation/Change%20Records/Retirement%20-%202026-09-25.md).
- 2026-09-23: I moved VM 103 `win11-dev` from Green to Grey. [Migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md).
- 2026-09-22: The internal documentation site and Homelab Dashboard containers on `docker-main` stopped at 3:39 and 3:40 AM Eastern and were still stopped on 2026-09-24. No record covers the stop yet.

## Cluster State

All five nodes report `pve-manager/9.2.11` and their lowercase `.galaxy` FQDN, and quorum holds at five votes. On 2026-09-24 four nodes ran kernel `7.0.14-8-pve` and blue-server ran `7.0.14-15-pve`. The installed-kernel column is the 2026-09-06 reading.

| Node | FQDN | PVE | Running kernel (2026-09-24) | Installed kernel (2026-09-06) |
| --- | --- | --- | --- | --- |
| grey-server | `grey-server.galaxy` | 9.2.11 | `7.0.14-8-pve` | `7.0.14-15-pve` |
| purple-server | `purple-server.galaxy` | 9.2.11 | `7.0.14-8-pve` | `7.0.14-15-pve` |
| blue-server | `blue-server.galaxy` | 9.2.11 | `7.0.14-15-pve` | `7.0.14-15-pve` |
| red-server | `red-server.galaxy` | 9.2.11 | `7.0.14-8-pve` | `7.0.14-15-pve` |
| green-server | `green-server.galaxy` | 9.2.11 | `7.0.14-8-pve` | `7.0.14-15-pve` |

## Guest Workloads

| Guest | Type | Node | Role | Key workloads |
| --- | --- | --- | --- | --- |
| HQ-DC01 | VM 301 | grey-server | First domain controller for `ad.alphasecunited.com` (`192.168.65.10`, VLAN 65) | AD DS, AD-integrated DNS, global catalog, all five operations master roles<br>LDAPS on TCP 636 since 2026-09-20<br>OpenSSH |
| HQ-DC02 | VM 302 | grey-server | Second domain controller (`192.168.65.11`, VLAN 65) | AD DS, AD-integrated DNS, global catalog<br>LDAPS on TCP 636 since 2026-09-20<br>OpenSSH |
| HQ-MGT01 | VM 303 | grey-server | Windows management and hybrid identity (`192.168.65.12`, VLAN 65) | [Windows Admin Center](../../../Platforms/Windows%20Admin%20Center/README.md) 2.7.21.5, HTTPS 443<br>Azure Connected Machine agent 1.67.03504.3207, Connected<br>Entra provisioning agent service running<br>OpenSSH |
| HQ-WS001 | VM 310 | grey-server | Windows 11 test workstation (`192.168.65.20`, VLAN 65); stopped on 2026-09-24 | Windows 11 Pro 25H2<br>Windows LAPS and the Tier 2 local-administrator policy<br>OpenSSH since 2026-09-19 |
| kali-pen | VM 102 | grey-server | Penetration-testing VM on VLAN 40; stopped on 2026-09-24 | Kali Linux 2026.2 installer build |
| win11-dev | VM 103 | grey-server | Standalone Windows development workstation (`192.168.40.117`, VLAN 40) | Windows 11 Pro 25H2<br>OpenSSH Server<br>QEMU guest agent; no development tools installed |
| ubuntu-dev | VM 105 | grey-server | Ubuntu development workstation | GNOME Shell 50.1<br>Docker 29.7.2<br>VS Code 1.136.1<br>Node.js 24.19.0 via nvm<br>GitHub CLI 2.98.0<br>Wazuh agent 4.14.6<br>node_exporter 1.10.2<br>Samba (SMB2 to SMB3, TCP 445 on `lo` and `ens18`, shares `ai-agent` and `shared-folder`, Samba user `dkadi`), see [Samba](../../../Platforms/Samba/README.md) |
| ansible-01 | LXC 100 | blue-server | Automation and node provisioning | Ansible 14.2.0 / ansible-core 2.21.2<br>Semaphore 2.18.27<br>Galaxy PXE<br>tftpd-hpa 5.2+20240610-3<br>Wazuh agent 4.14.6 |
| docker-main | LXC 110 | grey-server | Docker apps | Immich 3.2.2<br>BookLore 2.4.0<br>Forgejo 16.0.5<br>Dockhand 1.0.48<br>CLI Proxy API 7.3.16<br>Ollama 0.33.3 / Qwen 3.5 2B<br>Open WebUI 0.11.4<br>App Portal 0.6.0<br>What's Up Docker 9.1.0<br>Internal documentation site and Homelab Dashboard, both stopped since 2026-09-22<br>Wazuh agent 4.14.6 |
| monitor-01 | LXC 104 | blue-server | Infrastructure monitoring (`192.168.73.2`, VLAN 73) | Prometheus 3.14.0<br>Grafana 13.2.2<br>Proxmox exporter 3.10.0<br>blackbox exporter 0.28.0<br>NUT exporter<br>Discord alert bot<br>PeaNUT 6.0.0<br>cAdvisor 0.60.6<br>What's Up Docker 9.1.0<br>Hawser Edge 0.2.48<br>Wazuh agent 4.14.6 |
| docker-network | LXC 107 | blue-server | Network access control plane | Nginx Proxy Manager 2.15.1<br>NetBird server 0.79.0 / dashboard 2.93.0<br>Hawser Edge 0.2.48<br>Wazuh agent 4.14.6 |
| docker-blue | LXC 108 | blue-server | Remote access and integrations | Docker MCP Gateway 0.43.3, two instances<br>SSH Manager MCP<br>UniFi Network MCP<br>Executor 1.6.10<br>RustDesk hbbs / hbbr 1.1.16<br>MeshCentral 1.2.6<br>Hawser Edge 0.2.48<br>Wazuh agent 4.14.6 |
| app-01 | VM 116 | purple-server | App platform | Coolify 4.3.23<br>Traefik 3.7.12<br>Postgres / Redis / Realtime / Sentinel<br>cAdvisor 0.60.5<br>Wazuh agent 4.14.6 |
| edge-01 | VM 121 | purple-server | Edge ingress | Caddy 2.6.2<br>cloudflared 2026.8.3<br>Wazuh agent 4.14.5 |
| security-01 | VM 200 | grey-server | Security monitoring (`192.168.72.2`, VLAN 72) | Wazuh 4.14.7<br>Wazuh MCP Server<br>node_exporter<br>cAdvisor<br>Hawser Edge 0.2.48 |
| alpha-prod-01 | VM 401 | purple-server | Voice services | Two TeamSpeak 3 Server 3.13.8 instances<br>TS3 Manager<br>TeamSpeak reachability collector<br>Playit agent<br>Hawser Edge 0.2.49<br>Wazuh agent 4.14.6 |
| splunk-siem | VM 109 | grey-server | SIEM (`192.168.72.3`, VLAN 72) | Splunk Enterprise 10.4.0<br>Enterprise Security 8.5.1<br>SC4S<br>No Wazuh agent |
| media-01 | LXC 842 | red-server | Media automation and playback | Jellyfin 12.1.0<br>Seerr 3.4.1<br>Sonarr / Radarr / Prowlarr<br>FlareSolverr 3.5.2<br>qBittorrent 5.2.3 through Gluetun and Proton VPN<br>Hawser Edge 0.2.48<br>Wazuh agent 4.14.6 |

## HQ-DC01, HQ-DC02 and HQ-MGT01

The forest build, LDAPS and the management tooling are recorded under [Active Directory](../../../Platforms/Active%20Directory/README.md). On 2026-09-25 `azcmagent show` on HQ-MGT01 reported agent 1.67.03504.3207, status Connected, and a heartbeat at 1:32 AM Eastern. The `WindowsAdminCenter`, `WindowsAdminCenterAccountManagement`, `AADConnectProvisioningAgent` and `himds` services were running. The Windows Admin Center executables read file version 2.7.21.5; the Active Directory extension 0.86.0 and DNS extension 2.76.0 are the 2026-09-12 readings. No Windows guest runs a Wazuh agent.

## ansible-01

| Workload | Details |
| --- | --- |
| Ansible | Control node; `ansible` resolves to `/usr/local/bin/ansible`, community 14.2.0 with ansible-core 2.21.2. The Debian packages `ansible` 12.0.0 and `ansible-core` 2.19.4 are also installed and shadowed on PATH |
| Semaphore | 2.18.27; systemd unit active, running as root from `/root/config.json` with SQLite at `/root/database.sqlite`; HTTP UI on TCP 3000; three projects (Server-SSH 13 templates, Fleet-Updates 6, Monitoring-Exporters 4), 23 templates, no schedules |
| Wazuh agent | 4.14.6-1, held; manager ID `009` as `ansible-01` |
| Galaxy PXE | `galaxy-pxe.service`; enabled and active since 2026-08-01; `/usr/bin/python3 /usr/local/lib/galaxy-pxe/galaxy_pxe.py` from `/etc/systemd/system/galaxy-pxe.service`; HTTP on `0.0.0.0:8080` with `--base-url http://192.168.40.36:8080`; machine registry `/etc/galaxy-pxe/machines.json`, state `/var/lib/galaxy-pxe/state.json`, assets `/srv/galaxy-pxe`; `ProtectSystem=strict` with `/var/lib/galaxy-pxe` the one writable path. Platform record at [Galaxy PXE](../../../Platforms/Galaxy%20PXE/README.md) |
| tftpd-hpa | 5.2+20240610-3 from APT; `tftpd-hpa.service` enabled and active; UDP 69; root `/srv/tftp`; serves the UEFI boot chain Galaxy PXE hands out |
| Containers | Docker is not installed |

## ubuntu-dev

This is the Ubuntu development workstation on VM 105, and it is where I now develop. I added it to this inventory on 2026-08-13; it had been running since 2026-08-12 with no record here.

It took CLI Proxy API from `debian-dev` on 2026-08-13 and hosted it until I moved the deployment to `docker-main` on 2026-08-19. After the new HTTPS and authenticated model paths passed, I removed the old container, Compose network, project files, credential state, logs, plugins, and migration cache from this VM.

The login account is `ai-agent`, under the single-account exception the Linux Host Baseline Standard gives this workstation role, as it did on `debian-dev`. I applied the Linux Host Baseline Standard on 2026-08-13: the sudo grant moved out of `/etc/sudoers` into a `0440` drop-in, SSH took the six hardening settings, root is locked, the clock and locale are `America/New_York` and `en_US.UTF-8`, and cloud-init is disabled. It joined fleet monitoring the same day as Wazuh agent `020` and node_exporter target.

Node.js is installed per-user through nvm rather than system-wide. It resolves in an interactive shell but not in a non-interactive one, so scripts, cron jobs, and remote commands do not find `node` on PATH.

| Workload | Details |
| --- | --- |
| GNOME desktop | Ubuntu GNOME; GNOME Shell 50.1, GDM 50.1 |
| Docker | Docker CE 29.7.2 with Compose v5.5.0 on 2026-09-06; installed 2026-08-13 |
| VS Code | 1.136.1 on 2026-09-06 |
| Node.js | 24.19.0 via nvm, user scope |
| GitHub CLI | 2.98.0 on 2026-09-06, authenticated as `Duresa7` |
| Wazuh agent | 4.14.6, manager ID `020`, manager `192.168.72.2`; version held in apt |
| node_exporter | `prometheus-node-exporter` 1.10.2, `192.168.40.179:9100` |
| SSH | key-based login; host signing key registered on GitHub for verified commits |

## Dockhand management

[Dockhand 1.0.48](../../../Platforms/Dockhand/README.md) runs on `docker-main` at `https://dockhand.alphasecunited.com` and replaced Dockge on 2026-09-15. It manages `docker-main` through the local Docker socket and six hosts through Hawser Edge agents: 0.2.48 on `docker-blue`, `docker-network`, `monitor-01`, `media-01` and `security-01`, and 0.2.49 on `alpha-prod-01`. `app-01` runs no Hawser agent, so Coolify's containers stay outside Dockhand. On 2026-09-16 the fleet held 64 running containers in 42 Compose projects, all imported for UI editing. Dockhand rewrote 11 of those 42 host files into its own JSON form when it imported them, so the tracked copies under each platform's `Configuration/` are the authored reference. [Replacement record](../../../Platforms/Dockhand/Documentation/Change%20Records/Dockge%20Replacement%20-%202026-09-15.md), [registry and agent cutover](../../../Platforms/Dockhand/Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md).

## docker-main

14 containers were running on 2026-09-24. No Hawser agent runs here, because Dockhand itself does.

| Workload | Details |
| --- | --- |
| Internal documentation site | `docusaurus` container from `forgejo.alphasecunited.com/homelab-images/docusaurus:stable`; exited with code 0 at 3:40 AM Eastern on 2026-09-22 and still stopped on 2026-09-24, with restart policy `unless-stopped`. NPM has no proxy host for it |
| Homelab Dashboard | `ghcr.io/duresa7/homelab-dashboard-aio:latest`; exited with code 137 at 3:39 AM Eastern on 2026-09-22 and still stopped on 2026-09-24. NPM host 12 and the UniFi `dashboard` record still point at `192.168.40.35:3001`, where nothing listens |
| Immich | Server and machine learning v3.2.2 (`release-cuda` for machine learning); PostgreSQL `14-vectorchord0.4.3-pgvector0.8.1-pgvectors0.2.0` and Valkey 9; NVENC transcoding and CUDA machine learning on the GTX 1080 Ti since 2026-09-05; TCP 2283 |
| BookLore | v2.4.0 with MariaDB 11.4.8; TCP 6060 |
| Forgejo | 16.0.5 from `codeberg.org/forgejo/forgejo:16`, labelled `wud.tag.include=^[0-9]+$` so What's Up Docker offers only plain numeric tags; HTTP 3000 and SSH 222; also the private registry for the `homelab-images` custom images |
| Dockhand | v1.0.48 (`fnsys/dockhand:v1.0.48`); TCP 3003; NPM host 31 |
| CLI Proxy API | v7.3.16 (commit c404af9, built 2026-09-24); Compose under `/opt/docker/cli-proxy-api`; TCP 8317 plus five auxiliary listeners; published internally as `https://aiproxy.alphasecunited.com` |
| Ollama | 0.33.3 (`/api/version`); `qwen3.5:2b` was the only installed model on 2026-09-06; API bound to `192.168.40.35:11434` without NPM or WAN publication |
| Open WebUI | 0.11.4 (`/api/version`) from the rolling `main` tag; TCP 3002; `openwebui.alphasecunited.com` through NPM host 28 |
| App Portal | 0.6.0 from `ghcr.io/duresa7/app-portal-server:0.6.0`; TCP 3004; `appportal.alphasecunited.com` through NPM host 32. [Platform record](../../../Platforms/App%20Portal/README.md) |
| What's Up Docker | 9.1.0; one of the six WUD exporters Prometheus scrapes |
| Wazuh agent | 4.14.6-1, held; manager ID `021`, enrolled 2026-09-06 after the old agent was found pointing at the manager's pre-migration address. [Re-enrollment record](../../../Platforms/Wazuh/Documentation/Change%20Records/docker-main%20Agent%20Re-enrollment%20-%202026-09-06.md) |
| Host services | node_exporter on 9100 (systemd), `wazuh-agent`, `php8.2-fpm` |
| Project directories | Compose projects live under `/opt/docker`. I removed five container-less leftover projects there on 2026-09-06; see [Documentation Staleness Audit - 2026-09-06](../../Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md) |

## monitor-01

| Workload | Details |
| --- | --- |
| Prometheus | 3.14.0 on TCP 9090; `restart: always`; 15-day retention; 57 of 57 targets up on 2026-09-24 across seven jobs: blackbox 23, cAdvisor 8, node 17, WUD 6, NUT 1, Proxmox 1, self-scrape 1. Prometheus holds no alert rules |
| Grafana | 13.2.2 on TCP 3000; 24 alert rules in `alphasec-united-alerts.yaml` and one contact point, `discord-bot`; 27 dashboards in the [Prometheus platform](../../../Platforms/Prometheus/README.md) configuration |
| Proxmox exporter | 3.10.0 on TCP 9221, using `pve-exporter@pve!monitor01` with `PVEAuditor` |
| blackbox exporter | 0.28.0 on TCP 9115; probes the internal NPM names plus the alert bot's health endpoint |
| NUT exporter | `hon95/prometheus-nut-exporter:latest` on TCP 9995; scrapes UPS-02 on grey-server; UPS-01 has had no data path since 2026-08-28 |
| Discord alert bot | `forgejo.alphasecunited.com/homelab-images/alert-bot:stable`, container created 2026-09-16; receives Grafana webhooks on TCP 8080 over the Compose network and posts to one Discord channel. Source in [Discord Alert Bot](../../../Platforms/Discord%20Alert%20Bot/README.md) |
| node_exporter | Debian `prometheus-node-exporter` 1.9.0-1+b4 on TCP 9100, systemd |
| cAdvisor | 0.60.6 on TCP 9101 |
| PeaNUT | 6.0.0; UPS dashboard on `192.168.73.2:8090`; its configuration lists NUT servers red-server and grey-server on TCP 3493 |
| What's Up Docker | 9.1.0 on TCP 9102 |
| Hawser | 0.2.48 |
| Wazuh agent | 4.14.6-1, held; manager ID `010` as `monitor-01` |
| Network | Static 192.168.73.2/24 on `MONITOR-A`, VLAN 73; UniFi DHCP serves .6 through .254 |

The [Uptime dashboard](../../../Platforms/Prometheus/Documentation/Change%20Records/Uptime%20Dashboard%20-%202026-09-15.md) went live on 2026-09-15 with 29 service checks. `edge-uptime.timer` on edge-01 reports the Cloudflare connection count and the Caddy and Coolify origin responses through the node_exporter textfile collector.

## docker-blue

11 containers were running on 2026-09-24. cloudflared and the Discord alert bot do not run here.

| Workload | Details |
| --- | --- |
| Docker MCP Gateway | `docker/mcp-gateway:v0.43.3`, two instances: `docker-mcp-gateway` for UniFi Network on `192.168.40.39:8811` and `ssh-manager-mcp-gateway` for SSH Manager on `192.168.40.39:8812`, both bearer-authenticated Streamable HTTP |
| UniFi Network MCP | `mcp-unifi-network` from `forgejo.alphasecunited.com/homelab-images/unifi-network-mcp:stable`; one shared controller connection, no published host port |
| SSH Manager MCP | `mcp-ssh-manager` from `forgejo.alphasecunited.com/homelab-images/mcp-ssh-manager:stable`, SSH Manager behind mcp-proxy on the Compose network only; 24 server definitions on 2026-09-24; enrolled host keys on the `ssh-manager-state` volume |
| Executor | 1.6.10 from `ghcr.io/usefulsoftwareco/executor-selfhost:latest`, container created 2026-09-19; Compose under `/opt/docker/executor`; internal HTTPS at `mcp.alphasecunited.com`. [Platform record](../../../Platforms/Executor/README.md) |
| RustDesk | `hbbs` and `hbbr` 1.1.16 from `rustdesk/rustdesk-server:latest`; [platform record](../../../Platforms/RustDesk/README.md) |
| MeshCentral | 1.2.6 (image label `1.2.6-mongodb`) from `ghcr.io/ylianst/meshcentral:latest`; HTTPS on `192.168.40.39:443`, published as `mesh.alphasecunited.com` through NPM host 29. [Platform record](../../../Platforms/MeshCentral/README.md) |
| What's Up Docker, cAdvisor, Hawser | `getwud/wud:latest`, `ghcr.io/google/cadvisor:latest`, Hawser 0.2.48 |
| Docker runtime | Docker Engine 29.8.0, containerd 2.3.4 and runc 1.5.1 on 2026-09-06 |
| Wazuh agent | 4.14.6-1, held; manager ID `007` as `docker-blue` |

## docker-network

| Workload | Details |
| --- | --- |
| Nginx Proxy Manager | 2.15.1, pinned by tag and excluded from Dockhand updates since 2026-09-25; Compose under `/opt/docker/nginx-proxy-manager`; 24 live proxy hosts and nine soft-deleted on 2026-09-24; one Let's Encrypt certificate for `*.alphasecunited.com` and the apex, valid to 2026-12-08, used by every live host. [Platform record](../../../Platforms/Nginx%20Proxy%20Manager/README.md) |
| NetBird | One combined `netbirdio/netbird-server:latest` container reporting management server 0.79.0, started 3:00 AM Eastern on 2026-09-19, plus `netbirdio/dashboard:latest` labelled v2.93.0; no separate signal or relay container; also the Access-A routing peer advertising `192.168.85.0/24`. [Platform record](../../../Platforms/Netbird/README.md) |
| Shared proxy network | External Docker network `proxy`, subnet `172.31.85.0/24`; Nginx Proxy Manager uses `172.31.85.10` |
| What's Up Docker, cAdvisor, Hawser | Running; Hawser 0.2.48 |
| Wazuh agent | 4.14.6-1, held; manager ID `011` as `docker-network` |

## app-01

| Workload | Details |
| --- | --- |
| Coolify | 4.3.23 from `/var/www/html/config/constants.php` (the image label `v4.5.1-33486634677` is not the app version); Sentinel 1.0.1, Realtime 1.0.19, PostgreSQL 15, Redis 7. [Update record](../../../Platforms/Coolify/Documentation/Change%20Records/Update%20to%204.3.23%20-%202026-09-18.md) |
| Traefik | Coolify ingress proxy `traefik:v3.7`, label v3.7.12 |
| cAdvisor | 0.60.5 |
| Generated apps | Coolify-managed application containers |
| Hawser | Not installed; Coolify manages this host |
| Wazuh agent | 4.14.6-1; manager ID `004` as `app-01` |

## edge-01

| Workload | Details |
| --- | --- |
| Caddy | 2.6.2, unit active on 2026-09-25 |
| cloudflared | 2026.8.3, unit active on 2026-09-25; the Cloudflare Tunnel connector. [Tunnel record](../../../Infrastructure/Network/Cloudflare/Configuration/edge-01.md) |
| Wazuh agent | 4.14.5-1; manager ID `005` as `edge-01` |
| Containers | Docker is not installed |

## security-01

| Workload | Details |
| --- | --- |
| Wazuh | Manager, indexer and dashboard; `wazuh-control info` reports v4.14.7 on 2026-09-24 |
| Wazuh MCP Server | `forgejo.alphasecunited.com/homelab-images/wazuh-mcp-server:stable`, healthy on 2026-09-24; host-networked at `192.168.72.2:3000`; read-only Manager and Indexer identities; upstream 4.3.0 is the last version I recorded |
| node_exporter | 1.9.0 on 9100 |
| cAdvisor | `ghcr.io/google/cadvisor:latest` on 9101 from `/opt/docker/cadvisor` |
| Hawser | 0.2.48 |
| Network | Static `192.168.72.2/24` on Security-A, VLAN 72 |

## alpha-prod-01

Eight containers were running on 2026-09-25.

| Workload | Details |
| --- | --- |
| TeamSpeak | `ts-valorant-02` and `ts-valorant-03`, both TeamSpeak 3 Server 3.13.8, recreated 2026-09-18. [Teamspeak Hosting](../../../Platforms/Teamspeak%20Hosting/README.md) |
| TS3 Manager | `joni1802/ts3-manager` on TCP 9000, NPM host 22 |
| TeamSpeak reachability collector | `teamspeak-monitor` from `forgejo.alphasecunited.com/homelab-images/teamspeak-monitor:stable`; reads each server's public SRV record every cycle and feeds the reachability dashboard |
| Playit agent | `ghcr.io/playit-cloud/playit-agent:latest`, image label 1.0 |
| What's Up Docker, cAdvisor, Hawser | WUD 9.0.2, cAdvisor 0.60.5, Hawser 0.2.49 |
| Wazuh agent | 4.14.6-1, held; manager ID `006` as `alpha-prod-01` |

## splunk-siem

| Workload | Details |
| --- | --- |
| Splunk Enterprise | 10.4.0, build f798d4d49089; `Splunkd` active; 65 apps under `/opt/splunk/etc/apps`, including `unifi_insights`, `wazuh_insights`, `ocsf_cim_addon_for_splunk`, `Splunk_ML_Toolkit` and `cefutils`. [Platform record](../../../Platforms/Splunk/README.md) |
| Enterprise Security | 8.5.1 |
| SC4S | Podman container `SC4S` from `ghcr.io/splunk/splunk-connect-for-syslog/container3:latest`, healthy; `sc4s.service` active; receives CEF on TCP and UDP 1514 and forwards to Splunk HEC over HTTPS 8088 |
| Other | `/opt/unifi-flow-collector` exists; no record covers it yet |
| Wazuh agent | None |
| Network | Static `192.168.72.3/24` on Security-A, VLAN 72 |

## media-01

11 containers were running on 2026-09-24: eight in the `media-stack` Compose project at `/opt/media-stack/compose.yml`, plus `cadvisor`, `hawser` and `wud` under `/opt/docker/`.

| Workload | Details |
| --- | --- |
| Jellyfin | 12.1.0 (`/System/Info/Public`), server name `Jelly-Media`, TCP 8096; Movies, TV Shows and Anime libraries; Intel Quick Sync render device. [Media Stack](../../../Platforms/Media%20Stack/README.md) |
| Seerr | v3.4.1 from `ghcr.io/seerr-team/seerr:latest`; the container is still named `jellyseerr`; TCP 5055 |
| Arr services | Sonarr 4.0.20.3014 (TCP 8989), Radarr 6.4.4.10685 (TCP 7878), Prowlarr 2.6.5.5623 (TCP 9696), all LinuxServer images |
| FlareSolverr | v3.5.2 |
| Download path | qBittorrent 5.2.3 (libtorrent 2.0.14) in the `qmcgaw/gluetun:latest` network namespace, UI on TCP 8080; Gluetun carries no version label (image built 2026-09-23, revision 1267bae) |
| What's Up Docker, cAdvisor, Hawser | WUD 9.1.0 on 9102, cAdvisor 0.60.6 on 9101, Hawser 0.2.48 |
| Wazuh agent | 4.14.6-1, held; manager ID `008` as `media-01` |
| Storage | `/` is the 100G `local-lvm` root volume (98G usable, 15% used); `/data` is the red-server HDD bind mount, `/dev/sda1` ext4, 916G usable with 541G used (60%) on 2026-09-24 |
| Network | Static `192.168.40.42` on VLAN 40; no gateway inbound port forward |

## Galaxy Proxmox node monitoring

| Node | Exporter | Service | Endpoint | State |
|---|---|---|---|---|
| grey-server | Manual `node_exporter` 1.9.0 | `node_exporter.service` | `192.168.70.10:9100` | Enabled, active, Prometheus `UP` |
| purple-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.11:9100` | Enabled, active, Prometheus `UP` |
| blue-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.12:9100` | Enabled, active, Prometheus `UP` |
| red-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.13:9100` | Enabled, active, Prometheus `UP` |
| green-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.14:9100` | Enabled, active, Prometheus `UP` |

## Wazuh agent coverage

On 2026-09-24 `agent_control -l` on `security-01` listed the manager (`000`) and 15 remote agents, all Active. `splunk-siem` and the Windows guests run no agent. I removed `debian-dev`'s agent `019` on 2026-08-14 and `game-01`'s agent `018` on 2026-09-12. The version column is the 2026-09-06 package reading.

| Host | Manager ID | Version (2026-09-06) | Group | State (2026-09-24) |
|---|---:|---|---|---|
| app-01 | 004 | 4.14.6 | default | Active |
| edge-01 | 005 | 4.14.5 | default, edge | Active |
| alpha-prod-01 | 006 | 4.14.6 | default | Active |
| docker-blue | 007 | 4.14.6 | default | Active |
| media-01 | 008 | 4.14.6 | default | Active |
| ansible-01 | 009 | 4.14.6 | default | Active |
| monitor-01 | 010 | 4.14.6 | default | Active |
| docker-network | 011 | 4.14.6 | default | Active |
| grey-server | 013 | 4.14.6 | default, proxmox | Active |
| purple-server | 014 | 4.14.6 | default, proxmox | Active |
| blue-server | 015 | 4.14.6 | default, proxmox | Active |
| red-server | 016 | 4.14.6 | default, proxmox | Active |
| green-server | 017 | 4.14.6 | default, proxmox | Active |
| ubuntu-dev | 020 | 4.14.6 | workstation | Active |
| docker-main | 021 | 4.14.6 | default | Active |

## Guest exporter coverage

Added 2026-07-25, completed 2026-07-28. Every running Linux guest now exports on 9100, all at `node_exporter` 1.9.0 except `ubuntu-dev`, added 2026-08-13, where Ubuntu 26.04 ships 1.10.2. `docker-main` and `splunk-siem` run the upstream binary because their distributions can't supply that version: bookworm offers only 1.5.0-1+b6, and Rocky 10.2 offers none. Rollout is owned by [monitoring-exporters](../../../Platforms/Ansible/Source/monitoring-exporters/README.md). The cAdvisor container counts below are a Prometheus readback of `container_last_seen` on 2026-09-07, 70 containers across the nine cAdvisor hosts.

| Guest | Install method | Service | Endpoint | cAdvisor |
|---|---|---|---|---|
| docker-main | Upstream binary (Debian 12 bookworm) | `node_exporter.service` | `192.168.40.35:9100` | 9101, 15 containers, `overlay2` |
| docker-network | Debian package | `prometheus-node-exporter.service` | `192.168.85.2:9100` | 9101, 6 containers, `overlayfs` |
| docker-blue | Debian package | `prometheus-node-exporter.service` | `192.168.40.39:9100` | 9101, 9 containers, `overlayfs` |
| media-01 | Debian package | `prometheus-node-exporter.service` | `192.168.40.42:9100` | 9101, 11 containers, `overlayfs` |
| alpha-prod-01 | Debian package | `prometheus-node-exporter.service` | `192.168.80.118:9100` | 9101, 8 containers, `overlayfs` |
| ansible-01 | Debian package | `prometheus-node-exporter.service` | `192.168.40.36:9100` | No containers |
| splunk-siem | Upstream binary (Rocky Linux 10.2) | `node_exporter.service` | `192.168.72.3:9100` | Podman, not applicable |
| app-01 | Pre-existing manual binary, left alone | `node_exporter.service` | `192.168.80.10:9100` | 9101, 7 containers, `overlayfs` |
| monitor-01 | Debian package | `prometheus-node-exporter.service` | `192.168.73.2:9100` | 9101, 9 containers, `overlayfs` |
| edge-01 | Manual binary | `node_exporter.service` | `192.168.30.10:9100` | No containers |
| ubuntu-dev | Ubuntu package | `prometheus-node-exporter.service` | `192.168.40.179:9100` | Not installed |

`security-01` also carries cAdvisor on 9101 with two containers; its row is in the guest table above.

`app-01` had been serving on 9100 since before this change and simply wasn't scraped. cAdvisor covered `docker-main` alone from 2026-07-25 to 2026-07-26, because v0.52.1 registers no containers under Docker 29's `overlayfs` driver. v0.60.5 from `ghcr.io/google/cadvisor` handles the containerd snapshotter. A Prometheus query on 2026-07-28 returned 53 named containers across all eight Docker hosts; eight are the cAdvisor containers. See [the troubleshooting record](../../../Platforms/Prometheus/Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

## Galaxy UPS telemetry

| Node | NUT version | Device | Endpoint | State |
| --- | --- | --- | --- | --- |
| red-server | 2.8.1-5 | `ups01`, APC Back-UPS Pro BR1500MS2 (UPS-01) | None | Disabled 2026-08-31: the `[ups01]` stanza is commented out in `/etc/nut/ups.conf`, `nut-server` is inactive, and `upsc -l` lists nothing. UPS-01's data cable has been disconnected since 2026-08-28. Re-read 2026-09-06 |
| grey-server | 2.8.1-5 | `ups02`, APC Back-UPS RS 1500MS2 (UPS-02) | `192.168.70.10:3493` | Driver and server active; `nut-monitor` disabled; `upsc -l` returns `ups02`. Re-read 2026-09-06 |
