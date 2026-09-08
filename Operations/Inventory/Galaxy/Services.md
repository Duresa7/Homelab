# Galaxy Services

**Created:** 2026-07-08  
**Last updated:** 2026-09-07

This inventory maps 13 workload guests. I added `ubuntu-dev` on 2026-08-13, removed `debian-dev` on 2026-08-14 when I decommissioned it, moved CLI Proxy API from `ubuntu-dev` to `docker-main` on 2026-08-19, and removed `kasm-01` with VM 122 later that day. I confirmed deleted VM 117 `supabase-01` absent on 2026-08-20; it was stopped and did not carry a workload in this inventory. I added separate anime routing to the media stack on 2026-08-23. Twelve guests were running during the 2026-08-03 staleness audit; `game-01` was added on 2026-08-07. Wazuh and Prometheus cover all five Proxmox nodes.

I repeated the monitoring check on 2026-09-03 after the floating-tag rollout. Prometheus reported 56 active targets with all 56 up: 18 node exporters, nine cAdvisor exporters, six What's Up Docker exporters, 20 blackbox probes, one NUT exporter target for UPS-02, the Proxmox exporter, and Prometheus itself. No target labels or scrape URLs referenced Kasm.

On 2026-09-06 I audited every row in this file against the running guests through the SSH Manager, reading versions from the services themselves, from OCI image labels, and from package managers rather than from earlier records. Prometheus reported 57 of 57 targets up across the same seven jobs, with the Open WebUI probe as the twenty-first blackbox target. The corrections from that pass are marked with their date below; the largest finding was that `docker-main`'s Wazuh agent had never reached the current manager, which I fixed the same day. The audit is recorded in [Documentation Staleness Audit - 2026-09-06](../../Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md).

## Cluster State

All five nodes report `pve-manager/9.2.11` and their lowercase `.galaxy` FQDN. Kernel `7.0.14-15-pve` is installed on every node, while the nodes continue to run `7.0.14-8-pve` until a later rolling reboot. I re-read both figures from every node on 2026-09-06 and nothing had moved; quorum held at five votes.

| Node | FQDN | PVE | Running kernel | Installed kernel |
| --- | --- | --- | --- | --- |
| grey-server | `grey-server.galaxy` | 9.2.11 | `7.0.14-8-pve` | `7.0.14-15-pve` |
| purple-server | `purple-server.galaxy` | 9.2.11 | `7.0.14-8-pve` | `7.0.14-15-pve` |
| blue-server | `blue-server.galaxy` | 9.2.11 | `7.0.14-8-pve` | `7.0.14-15-pve` |
| red-server | `red-server.galaxy` | 9.2.11 | `7.0.14-8-pve` | `7.0.14-15-pve` |
| green-server | `green-server.galaxy` | 9.2.11 | `7.0.14-8-pve` | `7.0.14-15-pve` |

## Guest Workloads
| Guest | Type | Node | Role | Key workloads |
| --- | --- | --- | --- | --- |
| ansible-01 | LXC 100 | grey-server | Automation and node provisioning | Ansible 14.2.0 / core 2.21.2<br>Semaphore 2.18.27<br>Galaxy PXE<br>tftpd-hpa 5.2+20240610-3<br>Wazuh agent 4.14.6<br>SSH<br>cron |
| ubuntu-dev | VM 105 | grey-server | Ubuntu development workstation; VM display name and guest hostname `ubuntu-dev` | GNOME Shell 50.1<br>GDM 50.1<br>Docker 29.7.2<br>VS Code 1.136.1<br>Node.js 24.19.0 via nvm<br>GitHub CLI 2.98.0<br>Wazuh agent 4.14.6<br>node_exporter 1.10.2<br>SSH |
| docker-main | LXC 110 | grey-server | Docker apps | Internal documentation site<br>Immich<br>BookLore<br>Forgejo<br>Homelab Dashboard<br>Portainer<br>CLI Proxy API<br>Ollama 0.33.3 / Qwen 3.5 2B<br>Open WebUI `main` / 0.11.3<br>What's Up Docker 8.4.0<br>Wazuh agent 4.14.6 |
| monitor-01 | LXC 104 | blue-server | Infrastructure monitoring (`192.168.73.2`, VLAN 73) | Prometheus<br>Grafana<br>Proxmox exporter<br>blackbox exporter<br>NUT exporter<br>Discord alert bot<br>cAdvisor<br>PeaNUT<br>Wazuh agent 4.14.6 |
| docker-network | LXC 107 | blue-server | Network access control plane | Nginx Proxy Manager 2.15.1<br>NetBird management 0.78.1 / dashboard 2.92.0<br>Portainer Edge Agent `latest` / 2.45.0<br>Wazuh agent 4.14.6 |
| docker-blue | LXC 108 | blue-server | Remote access and lightweight integrations | Docker MCP Gateway 0.43.3<br>SSH Manager MCP 3.8.5<br>Executor `latest` / 1.6.8<br>RustDesk hbbs / hbbr<br>Portainer Edge Agent `latest` / 2.45.0<br>Wazuh agent 4.14.6 |
| app-01 | VM 116 | grey-server | App platform | Coolify<br>Traefik 3.7.10<br>Postgres / Redis / Realtime<br>Wazuh agent 4.14.6 |
| edge-01 | VM 121 | grey-server | Edge ingress | Caddy<br>cloudflared<br>Wazuh agent 4.14.5 |
| security-01 | VM 200 | grey-server | Security monitoring (`192.168.72.2`, VLAN 72) | Wazuh 4.14.7<br>Wazuh MCP Server 4.3.0<br>node_exporter<br>cAdvisor |
| alpha-prod-01 | VM 401 | grey-server | Voice/game services | TeamSpeak<br>TS3 Manager<br>TeamSpeak reachability collector<br>Playit<br>Portainer Edge Agent `latest` / 2.45.0<br>Wazuh agent 4.14.6 |
| splunk-siem | VM 109 | grey-server | SIEM (`192.168.72.3`, VLAN 72) | Splunkd<br>SC4S |
| media-01 | LXC 842 | red-server | Media automation and playback; request-to-play acquisition verified | Jellyfin<br>Seerr<br>Sonarr / Radarr / Prowlarr<br>FlareSolverr<br>qBittorrent through Gluetun / Proton VPN<br>Portainer Edge Agent `latest` / 2.45.0<br>Wazuh agent 4.14.6 |
| game-01 | LXC 123 | green-server | Self-hosted game servers (`192.168.80.30`, VLAN 80) | Pelican Panel v1.0.0-beta38<br>Pelican Wings v1.0.0-beta27<br>Docker 29.7.2<br>Vanilla Minecraft 26.2 / Java 25, running and public<br>Better Realism 7.2.0 / Minecraft 1.21.1 / Fabric 0.19.3, stopped and retained<br>Playit agent 1.0.9<br>node_exporter 1.9.0<br>cAdvisor 0.60.5<br>Wazuh agent 4.14.6 |

## ansible-01

| Workload | Details |
| --- | --- |
| Ansible | Control node; community 14.2.0 with ansible-core 2.21.2 selected from `/opt/ansible-current` |
| Semaphore | 2.18.27; systemd enabled/active; HTTP UI on TCP 3000; three projects, 23 templates, & 11 views |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `009` as `ansible-01` |
| Galaxy PXE | `galaxy-pxe.service`; enabled/active since 2026-08-01; `/usr/bin/python3 /usr/local/lib/galaxy-pxe/galaxy_pxe.py` from the unit at `/etc/systemd/system/galaxy-pxe.service`; HTTP on `0.0.0.0:8080` with `--base-url http://192.168.40.36:8080`; machine registry `/etc/galaxy-pxe/machines.json`, state `/var/lib/galaxy-pxe/state.json`, assets `/srv/galaxy-pxe`; `ProtectSystem=strict` with `/var/lib/galaxy-pxe` the one writable path. Platform record at [Galaxy PXE](../../../Platforms/Galaxy%20PXE/README.md) |
| tftpd-hpa | 5.2+20240610-3 from APT; `tftpd-hpa.service` enabled/active; UDP 69; root `/srv/tftp`; serves the UEFI boot chain Galaxy PXE hands out |
| System services | Semaphore, Galaxy PXE, tftpd-hpa, SSH, cron |
| Containers | No Docker or Podman containers detected |

## ubuntu-dev

This is the Ubuntu development workstation on VM 105, and it is where I now develop. I added it to this inventory on 2026-08-13; it had been running since 2026-08-12 with no record here.

It took CLI Proxy API from `debian-dev` on 2026-08-13 and hosted it until I moved the deployment to `docker-main` on 2026-08-19. After the new HTTPS and authenticated model paths passed, I removed the old container, Compose network, project files, credential state, logs, plugins, and migration cache from this VM.

The login account is `ai-agent`, matching the single-account arrangement on `debian-dev`, and it carries the same approved single-account exception. I applied the Linux Host Baseline Standard on 2026-08-13: the sudo grant moved out of `/etc/sudoers` into a `0440` drop-in, SSH took the six hardening settings, root is locked, the clock and locale are `America/New_York` and `en_US.UTF-8`, and cloud-init is disabled. It joined fleet monitoring the same day as Wazuh agent `020` and node_exporter target.

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

## docker-main

| Workload | Details |
| --- | --- |
| Internal documentation site | Static HTML served by an unprivileged Nginx container as UID 101 with a read-only root filesystem, all Linux capabilities dropped, and no writable application volume |
| Immich | 3.1.0 photo/video stack; server and machine learning track `release`; Valkey 9 and PostgreSQL 14 with VectorChord use the exact images from the 3.1.0 release Compose file; video transcoding through NVENC and machine learning through CUDA on the GTX 1080 Ti since 2026-09-05 |
| BookLore | v2.3.1 from `ghcr.io/booklore-app/booklore:latest`; MariaDB 11.4.8 matches the v2.3.1 release example; both containers healthy after the 2026-09-03 dependency update |
| Forgejo | 16.0.3 from `codeberg.org/forgejo/forgejo:16`, labelled `wud.tag.include=^[0-9]+$` since 2026-09-03 so What's Up Docker offers only plain numeric tags |
| Homelab Dashboard | `ghcr.io/Duresa7/homelab-dashboard-aio:latest` |
| Portainer CE | Server 2.45.0 from `portainer/portainer-ce:latest`, verified 2026-09-01 from the unauthenticated `/api/status` response; local Docker environment plus four Edge Agent 2.45.0 hosts: `alpha-prod-01`, `docker-blue`, `media-01`, & `docker-network` |
| CLI Proxy API | Version 7.2.149 from `eceasy/cli-proxy-api:latest`; Compose under `/opt/docker/cli-proxy-api`; published internally as `https://aiproxy.alphasecunited.com` |
| Ollama | 0.33.3 pinned by tag and digest; `qwen3.5:2b` model ID `324d162be6ca` is the only installed model; GTX 1080 Ti at 100% GPU offload; Compose under `/opt/docker/ollama`; API bound to `192.168.40.35:11434` without NPM or WAN publication |
| Open WebUI | Tracks rolling `main` with `pull_policy: always`; currently reports 0.11.3; authenticated frontend in the Ollama Compose project; internal HTTPS active at `openwebui.alphasecunited.com` through NPM host 28; direct recovery path on `192.168.40.35:3002`; model discovery verified |
| What's Up Docker | 8.4.0 from `getwud/wud:latest`; Compose under `/opt/docker/wud`; one of the six WUD exporters Prometheus scrapes on 9102 |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `021` as `docker-main`, enrolled 2026-09-06. Until that day the host ran 4.14.0-1 with `ossec.conf` still naming `192.168.40.227`, the manager's pre-migration address, so it had never connected to the manager at `192.168.72.2`; see [docker-main Agent Re-enrollment](../../../Platforms/Wazuh/Documentation/Change%20Records/docker-main%20Agent%20Re-enrollment%20-%202026-09-06.md) |
| Project directories | `/opt/docker` holds the ten Compose projects above and nothing else since 2026-09-06, when I removed five container-less leftovers: `wyze-bridge` and `docker-proxy` (empty), `backups` (empty), `nginx-proxy-manager` (a 2026-04-14 tree from before the proxy moved to `docker-network`, including its old certificates), and `docusaurus.prev` (a 2026-08-03 copy of the documentation site project). All 15 containers stayed up and `docusaurus` stayed healthy |

## monitor-01

| Workload | Details |
| --- | --- |
| Prometheus | 3.14.0 on TCP 9090; `restart: always`; 15-day retention; 57 of 57 targets `up` across seven jobs: node 18, cAdvisor 9, WUD 6, Proxmox 1, blackbox 21 (20 NPM names plus the alert bot's health endpoint), NUT 1, & self-scrape 1 |
| Grafana | 13.2.1 on TCP 3000; 27 provisioned dashboards and 24 provisioned alert rules in the `AlphaSec United Alerts` folder; root notification policy routes to the webhook contact point `discord-bot`; `GF_DATABASE_WAL` absent since the 2026-09-02 recreate; administrator credential held outside this repository |
| Proxmox exporter | `prompve/prometheus-pve-exporter:latest` on TCP 9221, using `pve-exporter@pve!monitor01` with `PVEAuditor` |
| blackbox exporter | `prom/blackbox-exporter:latest`, currently v0.28.0, on TCP 9115; probes 20 internal NPM names plus the alert bot's Compose health endpoint |
| NUT exporter | `hon95/prometheus-nut-exporter:latest` on TCP 9995; Prometheus scrapes UPS-02 on grey-server; UPS-01 remains absent while its data cable is disconnected |
| Discord alert bot | `alphasecunited/alert-bot:1` built from `Platforms/Discord Alert Bot/Source/`; receives Grafana webhooks on TCP 8080 over the Compose network only and posts to Discord `#bots` as the Anubis AS bot user; running since 2026-09-02, healthy, delivery proven the same day |
| node_exporter | 1.9.0 on TCP 9100, installed through the monitoring-exporters Ansible project |
| cAdvisor | `ghcr.io/google/cadvisor:latest`, currently v0.60.5, on TCP 9101; one of nine scraped cAdvisor endpoints |
| PeaNUT | `brandawg93/peanut:latest`, currently 6.0.0; authenticated UPS dashboard bound to `192.168.73.2:8090`; Compose under `/opt/docker/peanut`; reads Red and Grey NUT endpoints without a command account |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `010` as `monitor-01` |
| Network | Static 192.168.73.2/24 on `MONITOR-A`, VLAN 73; UniFi DHCP serves .6 through .254 |

## docker-blue

| Workload | Details |
| --- | --- |
| Docker MCP Gateway | Version 0.43.3 from a digest-pinned official image; Compose under `/opt/docker/mcp-gateway`; separate bearer-authenticated Streamable HTTP endpoints at `192.168.40.39:8811` for UniFi Network and `192.168.40.39:8812` for SSH Manager; UniFi runs as one persistent service at `http://unifi-network:8080/mcp` since 2026-09-07, SSH Manager at `http://ssh-manager:8080/mcp` since 2026-09-03; both health endpoints and real client calls pass |
| UniFi Network MCP | `mcp-unifi-network` from `homelab/unifi-network-mcp:0.29.3-full-access-proxy`; mcp-proxy 0.12.0 and bridge SDK 1.29.1 in an isolated environment; one shared controller connection, no published host port; credentials in root-owned mode-0600 `unifi-network.env`; six concurrent Executor reads passed on 2026-09-07 |
| SSH Manager MCP | `mcp-ssh-manager` container from the local `homelab/mcp-ssh-manager:latest` image, SSH Manager 3.8.5 behind mcp-proxy 0.12.0 on port 8080 of the Compose network only; one persistent process shared by every client, so no per-session container is created; eighteen server definitions in `ssh-manager-servers.env` and credentials in the root-owned `ssh-manager.env`; enrolled host keys on the `ssh-manager-state` volume |
| Executor | Self-hosted 1.6.8 from `ghcr.io/usefulsoftwareco/executor-selfhost:latest`, OCI version label read 2026-09-06; Compose under `/opt/docker/executor`; persistent SQLite and key state under `/opt/docker/executor/data`; internal HTTPS at `mcp.alphasecunited.com`; administrator claimed; separate healthy connections for UniFi MCP Gateway with 5 tools, SSH Manager MCP Gateway with 37 tools, and local Wazuh MCP with 41 read-only tools |
| RustDesk | `hbbs` and `hbbr` using `rustdesk/rustdesk-server:latest` |
| Portainer Edge Agent | `portainer/agent:latest`, currently 2.45.0; environment 7; compose under `/opt/docker/portainer-edge-agent`; endpoint status 1 on 2026-09-03 |
| Docker runtime | Docker Engine 29.8.0, containerd 2.3.4, & runc 1.5.1 on 2026-09-06. The 2026-07-28 repair of a containerd 2.2.4 shim panic took the host to 29.6.2 / 2.2.6 / 1.3.6, and ordinary package updates have carried it forward since. Every Debian 13 Docker host reads 29.8.0; `security-01` is on 29.6.2 and `ubuntu-dev` on 29.7.2 |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `007` as `docker-blue` |

## docker-network

| Workload | Details |
| --- | --- |
| Nginx Proxy Manager | Version 2.15.1; Docker Compose project under `/opt/docker/nginx-proxy-manager`; administrator initialized; wildcard/apex Let's Encrypt certificate assigned with Force SSL and HTTP/2 |
| NetBird | Management server 0.78.1 and dashboard 2.92.0 under `/opt/docker/netbird`; the management server moved from 0.78.0 to 0.78.1 on 2026-09-04, and on 2026-09-06 the container's own `netbird version` returned 0.78.1 while the dashboard OCI label still read v2.92.0; HTTPS returned `200`; also runs as the Access-A routing peer (overlay `100.121.111.204`) advertising the `AlphaSec-Access` network `192.168.85.0/24` |
| Shared proxy network | External Docker network `proxy`, subnet `172.31.85.0/24`; Nginx Proxy Manager uses `172.31.85.10` |
| Portainer Edge Agent | `portainer/agent:latest`, currently 2.45.0; environment 9; compose under `/opt/docker/portainer-edge-agent`; UniFi policy `6a68eb3f052792cd2140c9ad` permits only `192.168.85.2` to `192.168.40.35` on TCP 8000 & 9443; endpoint status 1 on 2026-09-03 |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `011` as `docker-network` |
| Operational status | First peer/VPN path, non-interactive ACME renewal, and bounded logging verified; no further hardening tracked after the 2026-07-12 descope decision |

## app-01

| Workload | Details |
| --- | --- |
| Coolify | Coolify app, Sentinel, Realtime, Postgres, Redis |
| Traefik | Coolify ingress proxy: `traefik:v3.7`; runtime 3.7.10 verified 2026-08-09; [change record](../../../Platforms/Coolify/Documentation/Change%20Records/Coolify%20Traefik%203.7%20Minor%20Update%20-%202026-08-09.md) |
| Generated apps | Coolify-managed application containers |
| Wazuh agent | 4.14.6-1; enabled/active; fresh manager ID `004` as `app-01`; connected to `192.168.72.2:1514` |

## edge-01

| Workload | Details |
| --- | --- |
| Caddy | Web/reverse proxy |
| cloudflared | Cloudflare Tunnel |
| Wazuh agent | 4.14.5-1; enabled/active; fresh manager ID `005` as `edge-01`; connected to `192.168.72.2:1514` |
| Containers | No Docker or Podman runtime detected |

## security-01

| Workload | Details |
| --- | --- |
| Wazuh | Manager, indexer, & dashboard at package version 4.14.7-1, verified 2026-09-01 |
| Wazuh MCP Server | 4.3.0 from a digest-pinned upstream image plus local TLS and static-bearer compatibility patches; host-networked at `192.168.72.2:3000`; read-only Manager and Indexer identities; Executor connection healthy with 41 tools |
| node_exporter | 1.9.0 on 9100 |
| cAdvisor | `ghcr.io/google/cadvisor:latest`, currently v0.60.5, on 9101 from `/opt/docker/cadvisor`; registers itself and the Wazuh MCP container |
| Network | Static `192.168.72.2/24` on Security-A/VLAN 72 |

## alpha-prod-01

| Workload | Details |
| --- | --- |
| TeamSpeak | Two `teamspeak` containers |
| TS3 Manager | `joni1802/ts3-manager` |
| TeamSpeak reachability collector | `teamspeak-monitor` from the locally built `teamspeak-monitor:local` image, rebuilt 2026-09-04; runs `collector.py` under `unless-stopped`, reads each server's public SRV record every cycle, and feeds the reachability dashboard; source under [Teamspeak Hosting](../../../Platforms/Teamspeak%20Hosting/Source/teamspeak-monitor/) |
| Playit agent | `ghcr.io/playit-cloud/playit-agent:latest`, currently release 1.0.10 |
| Portainer Edge Agent | `portainer/agent:latest`, currently 2.45.0; one of four remote Edge Agent hosts managed by Portainer server 2.45.0; endpoint status 1 on 2026-09-03 |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `006` as `alpha-prod-01` |

## splunk-siem

| Workload | Details |
| --- | --- |
| Splunkd | `Splunkd.service` active |
| SC4S | `sc4s.service` active; Podman host-network container receives CEF on TCP/UDP 1514 and forwards to Splunk HEC over HTTPS 8088 |
| Network | Static `192.168.72.3/24` on Security-A/VLAN 72 |

## media-01

| Workload | Details |
| --- | --- |
| Jellyfin | `jellyfin/jellyfin:latest` 10.11.11; Movies, TV Shows, and Anime libraries; AniList 13.0.0.0 is first for Anime series metadata and images; Moonbase 2.1.0.0 serves the Moonfin clients, hosts the Moonfin web app at `/Moonfin/Web/`, and proxies Seerr through a server-side SSO session; Intel Quick Sync render device and GPU-active playback verified; LAN port 8096 |
| Seerr | `ghcr.io/seerr-team/seerr:latest` 3.4.1; migrated from Jellyseerr with its existing configuration retained; Anime, Movies, and TV Shows enabled in Jellyfin sync; standard series route to `/data/media/tv` and anime to `/data/media/anime` through Sonarr |
| Arr services | LinuxServer Sonarr, Radarr, and Prowlarr `latest`; Sonarr has separate television and anime roots, its synced indexer includes anime category 5070, and Sonarr and Radarr link to qBittorrent through separate categories; a 2026-07-21 episode and movie acquisition passed request, download, hard-link import, payload, library scan, and playback checks |
| FlareSolverr | `ghcr.io/flaresolverr/flaresolverr:latest`; a challenge-protected indexer was verified through the `flaresolverr` Prowlarr tag during the acquisition pass |
| Download path | LinuxServer qBittorrent `latest` shares `qmcgaw/gluetun:latest` network namespace; Proton WireGuard, kill switch, and provider-side port synchronization verified; qBittorrent rejects the documented 100-pattern executable/script payload baseline for new torrents |
| Portainer Edge Agent | `portainer/agent:latest`, currently 2.45.0; environment 8; compose under `/opt/docker/portainer-edge-agent`; endpoint status 1 on 2026-09-03 |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `008` as `media-01` |
| Storage | One 100 GiB local LVM root volume contains configuration, downloads, media, and transcodes |
| Network | Static `192.168.40.42` on VLAN 40; no gateway inbound port forward |

## game-01

| Workload | Details |
| --- | --- |
| Pelican Panel | `ghcr.io/pelican/panel:latest`, running v1.0.0-beta38 on Laravel 13.25.0; SQLite in the `pelican-panel_pelican-data` volume; Compose under `/opt/docker/pelican-panel`; published as `games.alphasecunited.com` |
| Pelican Wings | v1.0.0-beta27 as a native `wings.service` binary, not a container; API on `0.0.0.0:8080`, SFTP on `0.0.0.0:2022`; server volumes under `/var/lib/pelican/volumes` owned `pelican` uid 999 gid 988; published as `wings.alphasecunited.com` |
| Node limits | 10240 MiB memory, 51200 MiB disk, 600 percent CPU, no overallocation; current assignments total 9216 MiB memory, 51200 MiB disk, and 500 percent CPU; allocations `192.168.80.30:25565` through `25575` |
| Vanilla Minecraft 26.2 | Pelican server ID 3; official Vanilla egg; Java 25; `VANILLA_VERSION=26.2`; 8192 MiB memory, 400 percent CPU, and 20480 MiB disk on `192.168.80.30:25565`; running and public; `keep_inventory=true`, read back from the console and flushed to the world on 2026-08-11; reached `Done (0.257s)!` after a controlled restart; public status returned 26.2 and protocol 776 after the game-rule change |
| Better Realism MC 7.2.0 | Pelican server ID 2; CurseForge server file 8570131; Minecraft 1.21.1 on Fabric 0.19.3 with Fabric Installer 1.1.2 and Java 21; stopped on 2026-08-09 and retained with its 363 MiB volume and world intact; 1024 MiB memory, 100 percent CPU, and 30720 MiB disk on `192.168.80.30:25566`; not public; its `-Xms4G` startup requires a limit restore before reactivation |
| Playit agent | Native package 1.0.9; enabled/active; the one assigned Minecraft tunnel forwards to `127.0.0.1:25565`; persistent secret at `/etc/playit/playit.toml`, mode 0600 and not versioned |
| Minecraft Playit relay | `minecraft-playit-relay.service`; enabled/active; dynamic user; loopback-only `127.0.0.1:25565` to Pelican allocation `192.168.80.30:25565` |
| node_exporter | 1.9.0 from APT, held; `:9100` |
| cAdvisor | `ghcr.io/google/cadvisor:latest`, currently v0.60.5, on `:9101`; registered 3 of 3 running containers |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `018` as `game-01` |
| Storage | One 80 GiB `local-lvm` root volume holds the panel, Wings, and both server volumes; root used 6.0 GiB of 79 GiB at the final 2026-08-09 check; no world backup or snapshot exists |
| Network | Static `192.168.80.30/24` on SERVERS-A/VLAN 80; `minecraft.alphasecunited.com` reaches only Vanilla Minecraft 26.2 through DNS-only Cloudflare CNAME/SRV records and Playit; no gateway inbound port forward and no Pelican interface in the tunnel |

## Galaxy Proxmox node monitoring

| Node | Exporter | Service | Endpoint | State |
|---|---|---|---|---|
| grey-server | Manual `node_exporter` 1.9.0 | `node_exporter.service` | `192.168.70.10:9100` | Enabled, active, Prometheus `UP` |
| purple-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.11:9100` | Enabled, active, Prometheus `UP` |
| blue-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.12:9100` | Enabled, active, Prometheus `UP` |
| red-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.13:9100` | Enabled, active, Prometheus `UP` |
| green-server | Debian `prometheus-node-exporter` 1.9.0-1+b4 | `prometheus-node-exporter.service` | `192.168.70.14:9100` | Enabled, active, Prometheus `UP` |

## Wazuh agent coverage

The Wazuh manager and dashboard verified 14 active remote agents on 2026-08-03. All five Proxmox nodes share `default, proxmox`. I enrolled `ubuntu-dev` as `020` on 2026-08-13. `debian-dev` held `019` from 2026-08-08 and was never added to this table; I decommissioned that VM on 2026-08-14 and removed agent `019` from the manager the same day via `manage_agents`, so `agent_control -l` no longer lists it.

On 2026-09-06 `agent_control -l` on `security-01` first listed 15 active remote agents and none disconnected or pending: the 14 rows from 2026-08-03 plus `game-01` as `018`, which had its own row in the guest table but was missing here. `docker-main` was not enrolled at all; its installed agent pointed at the manager's pre-migration address. I re-enrolled it the same day as `021`, so the manager now lists 16 active remote agents. The table below is the 2026-09-06 end state.

| Host | Manager ID | Version | Group | State |
|---|---:|---|---|---|
| app-01 | 004 | 4.14.6 | default | Active |
| edge-01 | 005 | 4.14.5 | default, edge | Active |
| alpha-prod-01 | 006 | 4.14.6 | default | Active |
| docker-blue | 007 | 4.14.6 | default | Active |
| media-01 | 008 | 4.14.6 | default | Active |
| ansible-01 | 009 | 4.14.6 | default | Active |
| monitor-01 | 010 | 4.14.6 | default | Active |
| docker-network | 011 | 4.14.6 | default | Active |
| game-01 | 018 | 4.14.6 | default | Active |
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
| edge-01 | Debian package | `prometheus-node-exporter.service` | `192.168.30.10:9100` | No containers |
| ubuntu-dev | Ubuntu package | `prometheus-node-exporter.service` | `192.168.40.179:9100` | Not installed |

`security-01` also carries cAdvisor on 9101 with two containers; its row is in the guest table above.

`app-01` had been serving on 9100 since before this change and simply wasn't scraped. cAdvisor covered `docker-main` alone from 2026-07-25 to 2026-07-26, because v0.52.1 registers no containers under Docker 29's `overlayfs` driver. v0.60.5 from `ghcr.io/google/cadvisor` handles the containerd snapshotter. A Prometheus query on 2026-07-28 returned 53 named containers across all eight Docker hosts; eight are the cAdvisor containers. See [the troubleshooting record](../../../Platforms/Prometheus/Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

## Galaxy UPS telemetry

| Node | NUT version | Device | Endpoint | State |
| --- | --- | --- | --- | --- |
| red-server | 2.8.1-5 | `ups01`, APC Back-UPS Pro BR1500MS2 (UPS-01) | None | Disabled 2026-08-31: the `[ups01]` stanza is commented out in `/etc/nut/ups.conf`, `nut-server` is inactive, and `upsc -l` lists nothing. UPS-01's data cable has been disconnected since 2026-08-28. Re-read 2026-09-06 |
| grey-server | 2.8.1-5 | `ups02`, APC Back-UPS RS 1500MS2 (UPS-02) | `192.168.70.10:3493` | Driver and server active; `nut-monitor` disabled; `upsc -l` returns `ups02`. Re-read 2026-09-06 |
