# Galaxy Services

**Created:** 2026-07-08  
**Last updated:** 2026-08-10

This inventory maps 14 workload guests. Twelve guests were running during the 2026-08-03 staleness audit; `game-01` was added on 2026-08-07. Wazuh and Prometheus cover all five Proxmox nodes.

I repeated the workload check after the 2026-08-10 guest resource changes. Every expected production guest and primary workload was running. Prometheus reported 52 active targets with none unhealthy, and all 20 blackbox probes passed after its restart policy was repaired.

## Cluster State

All five nodes report `pve-manager/9.2.6`, kernel `7.0.14-8-pve`, and their lowercase `.galaxy` FQDN.

| Node | FQDN | PVE | Kernel |
| --- | --- | --- | --- |
| grey-server | `grey-server.galaxy` | 9.2.6 | `7.0.14-8-pve` |
| purple-server | `purple-server.galaxy` | 9.2.6 | `7.0.14-8-pve` |
| blue-server | `blue-server.galaxy` | 9.2.6 | `7.0.14-8-pve` |
| red-server | `red-server.galaxy` | 9.2.6 | `7.0.14-8-pve` |
| green-server | `green-server.galaxy` | 9.2.6 | `7.0.14-8-pve` |

## Guest Workloads
| Guest | Type | Node | Role | Key workloads |
| --- | --- | --- | --- | --- |
| ansible-01 | LXC 100 | grey-server | Automation | Ansible 14.2.0 / core 2.21.2<br>Semaphore 2.18.27<br>Wazuh agent 4.14.6<br>SSH<br>cron |
| debian-dev | VM 102 | grey-server | Primary development workstation; VM display name and guest hostname `debian-dev` | GNOME Shell 48.7<br>GDM 48.0<br>Claude Desktop 1.26832.0<br>Docker 29.7.2<br>VS Code 1.132.0<br>Neovim 0.12.4 with LazyVim<br>Wazuh agent 4.14.6<br>node_exporter 1.9.0<br>SSH |
| docker-main | LXC 110 | grey-server | Docker apps | Internal documentation site<br>Immich<br>Forgejo<br>Homelab Dashboard<br>Portainer |
| monitor-01 | LXC 104 | blue-server | Infrastructure monitoring (`192.168.73.2`, VLAN 73) | Prometheus<br>Grafana<br>Proxmox exporter<br>blackbox exporter<br>NUT exporter<br>cAdvisor<br>PeaNUT<br>Wazuh agent 4.14.6 |
| docker-network | LXC 107 | blue-server | Network access control plane | Nginx Proxy Manager 2.15.1<br>NetBird management 0.75.1 / dashboard 2.90.8<br>Portainer Edge Agent 2.39.1<br>Wazuh agent 4.14.6 |
| docker-blue | LXC 108 | blue-server | Remote access | RustDesk hbbs / hbbr<br>Portainer Edge Agent 2.39.1<br>Wazuh agent 4.14.6 |
| app-01 | VM 116 | grey-server | App platform | Coolify<br>Traefik 3.7.10<br>Postgres / Redis / Realtime<br>Wazuh agent 4.14.6 |
| edge-01 | VM 121 | grey-server | Edge ingress | Caddy<br>cloudflared<br>Wazuh agent 4.14.5 |
| kasm-01 | VM 122 | purple-server | Isolated disposable desktops (`192.168.78.10`, VLAN 78 control plane) | Kasm Workspaces 1.19.0 CE<br>Docker 29.6.2<br>macvlan session lanes 74, 75, 77, 79<br>Wazuh agent 4.14.6 |
| security-01 / wazuh-01 | VM 200 | grey-server | Security monitoring (`192.168.72.2`, VLAN 72) | Wazuh 4.14.6<br>node_exporter<br>cAdvisor |
| alpha-prod-01 | VM 401 | grey-server | Voice/game services | TeamSpeak<br>TS3 Manager<br>Playit<br>Portainer Edge Agent<br>Wazuh agent 4.14.6 |
| splunk-siem | VM 109 | grey-server | SIEM (`192.168.72.3`, VLAN 72) | Splunkd<br>SC4S |
| media-01 | LXC 842 | red-server | Media automation and playback; request-to-play acquisition verified | Jellyfin<br>Seerr<br>Sonarr / Radarr / Prowlarr<br>FlareSolverr<br>qBittorrent through Gluetun / Proton VPN<br>Portainer Edge Agent 2.39.1<br>Wazuh agent 4.14.6 |
| game-01 | LXC 123 | green-server | Self-hosted game servers (`192.168.80.30`, VLAN 80) | Pelican Panel v1.0.0-beta36<br>Pelican Wings v1.0.0-beta27<br>Docker 29.7.2<br>Vanilla Minecraft 26.2 / Java 25, running and public<br>Better Realism 7.2.0 / Minecraft 1.21.1 / Fabric 0.19.3, stopped and retained<br>Playit agent 1.0.9<br>node_exporter 1.9.0<br>cAdvisor 0.60.5<br>Wazuh agent 4.14.6 |

## ansible-01

| Workload | Details |
| --- | --- |
| Ansible | Control node; community 14.2.0 with ansible-core 2.21.2 selected from `/opt/ansible-current` |
| Semaphore | 2.18.27; systemd enabled/active; HTTP UI on TCP 3000; three projects, 23 templates, & 11 views |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `009` as `ansible-01` |
| System services | Semaphore, SSH, cron |
| Containers | No Docker or Podman containers detected |

## debian-dev

This is the machine I develop on. It holds that role by itself since I deleted VM 111 `fedora-dev`.

The login account is `ai-agent`, and it is the only login account. I made that change on 2026-08-08. `/home/dkadi` survived the morning as a symlink to `/home/ai-agent` so existing paths kept resolving, and I removed the symlink the same afternoon. One account carries both my own work and the work agents do for me, which is a deliberate departure from the baseline standard's three-account model and the reason it is written down here.

`dkadi` is not a user on this host. Nothing on the host referenced the old path outside Chrome and Codex log files, which only recorded it as history.

| Workload | Details |
| --- | --- |
| GNOME desktop | Debian GNOME metapackages `gnome` and `gnome-core` 48; GNOME Shell 48.7-0+deb13u2 |
| Container runtime | Docker 29.7.2 with Compose v5.4.0 and buildx 0.36.1; `ai-agent` is a member of group `docker` |
| Display manager | GDM 48.0-2; Wayland greeter active; graphical target is the default boot target |
| Network | NetworkManager profile `Wired connection 1` owns `ens18`; autoconnect; static `192.168.40.135/24`; gateway/DNS `192.168.40.1` |
| Desktop privilege policy | `/etc/polkit-1/rules.d/49-ai-agent-gnome-nopasswd.rules` grants all actions without authentication to user `ai-agent` only from an active local session; remote Polkit requests remain subject to normal policy |
| Claude Desktop | 1.26832.0 from Anthropic's APT repository; sign-in persists through the GNOME Keyring login collection since the 2026-07-22 fresh session |
| Cowork virtualization | `/dev/kvm` available through AMD KVM; `ai-agent` is the sole member of group `kvm` |
| Remote administration | SSH Manager target `db_13_dev` (`ai-agent@192.168.40.135`) using the Jedi-PC Ed25519 identity. This independent profile name did not change with the Proxmox display name. It replaced the target `debian_dev`, which pointed at the removed `dkadi` account and had stopped working |
| SSH hardening | `/etc/ssh/sshd_config.d/99-hardening.conf` sets `PermitRootLogin no`, `PubkeyAuthentication yes`, `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `X11Forwarding no`, and `AllowUsers ai-agent`. `sshd -T` reads all six back, and root is password-locked, so `passwd -S root` returns `L` |
| Authorized keys | Three identities in `/home/ai-agent/.ssh/authorized_keys`: `jedi-pc`, `mac-air3-dkadi`, and `ansible-control`. I set no `from=` restriction on purpose, because over the Management VPN a device answers from `10.6.0.0/24` rather than its LAN address, and a source lock would close the path I use from outside the house |
| Privilege | `/etc/sudoers.d/90-ai-agent` at mode 0440 grants `ai-agent ALL=(ALL:ALL) NOPASSWD: ALL`. It replaced an inline grant that sat in `/etc/sudoers` itself, below `@includedir`, where one syntax error would have taken sudo out entirely |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `019` remains enrolled as `db-13-dev`; groups `default,workstation` |
| node_exporter | 1.9.0 on TCP 9100, installed through the monitoring-exporters Ansible project; Prometheus scrapes it with label `role=workstation` |
| Unattended upgrades | `unattended-upgrades` with `/etc/apt/apt.conf.d/20auto-upgrades` enabling daily list refresh and unattended install; `apt-daily-upgrade.timer` is armed |
| Language toolchains | GCC 14.2.0 and Clang 19.1.7 with clang-format, clang-tidy, cppcheck, bear, gdb, lldb and valgrind; Go 1.26.5 from upstream at `/usr/local/go` with gopls, dlv, staticcheck and golangci-lint; Rust 1.97.1 with clippy, rustfmt and rust-analyzer; Python 3.13.5 with ruff, mypy, pytest through poetry, pre-commit, ansible-lint, yamllint and IPython; Node 24.19.0 with npm 11.17.0; OpenJDK 21.0.11 with Maven 3.9.9 |
| Toolchain environment | `/etc/profile.d/dev-toolchains.sh` sets `GOPATH`, `GOBIN`, `JAVA_HOME`, `EDITOR` and `VISUAL`. Every shared binary lives in `/usr/local/bin`, which the default non-login `PATH` already carries, so a command run over SSH resolves the same tool the desktop session resolves |
| Editors | VS Code 1.132.0 from Microsoft's APT repository; Neovim 0.12.4 from the upstream release with LazyVim, 57 plugins and 20 extras covering C, Go, Rust, Python, TypeScript, Java, SQL, YAML, JSON, TOML, Docker, Markdown and Git; JetBrainsMono Nerd Font 48 faces installed for its glyphs |
| Rollback | None. I deleted the `pre-gnome-20260715` snapshot on 2026-08-08 under the standing rule, because the 2026-07-15 GNOME work was long finished and verified |

## docker-main

| Workload | Details |
| --- | --- |
| Internal documentation site | Static HTML served by an unprivileged Nginx container as UID 101 with a read-only root filesystem, all Linux capabilities dropped, and no writable application volume |
| Immich | 3.0.3 photo/video stack: server, Postgres, machine learning, Valkey |
| Forgejo | Git service: `codeberg.org/forgejo/forgejo:15` |
| Homelab Dashboard | `ghcr.io/Duresa7/homelab-dashboard-aio:latest` |
| Portainer CE | Server 2.39.5 from `portainer/portainer-ce:latest`, verified 2026-08-04 from the unauthenticated `/api/status` response; local Docker environment plus four Edge Agent 2.39.1 hosts: `alpha-prod-01`, `docker-blue`, `media-01`, & `docker-network` |

## monitor-01

| Workload | Details |
| --- | --- |
| Prometheus | 3.13.1 on TCP 9090; `restart: always`; 15-day retention; 52 of 52 targets `up` across six jobs: node 19, cAdvisor 9, Proxmox 1, blackbox 20, NUT 2, & self-scrape 1 |
| Grafana | 13.1.1 on TCP 3000; provisioned Homelab Overview dashboard; administrator credential held outside this repository |
| Proxmox exporter | `prompve/prometheus-pve-exporter:latest` on TCP 9221, using `pve-exporter@pve!monitor01` with `PVEAuditor` |
| blackbox exporter | `prom/blackbox-exporter:v0.28.0` on TCP 9115; probes 20 internal NPM names |
| NUT exporter | `hon95/prometheus-nut-exporter:1` on TCP 9995; reads `ups01` on red-server and `ups02` on grey-server |
| node_exporter | 1.9.0 on TCP 9100, installed through the monitoring-exporters Ansible project |
| cAdvisor | `ghcr.io/google/cadvisor:v0.60.5` on TCP 9101; one of eight scraped cAdvisor endpoints |
| PeaNUT | 6.0.0 pinned by digest; authenticated UPS dashboard bound to `192.168.73.2:8090`; Compose under `/opt/docker/peanut`; reads Red and Grey NUT endpoints without a command account |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `010` as `monitor-01` |
| Network | Static 192.168.73.2/24 on `MONITOR-A`, VLAN 73; UniFi DHCP serves .6 through .254 |

## docker-blue

| Workload | Details |
| --- | --- |
| RustDesk | `hbbs` and `hbbr` using `rustdesk/rustdesk-server:latest` |
| Portainer Edge Agent | `portainer/agent:2.39.1`; environment 7; compose under `/opt/docker/portainer-edge-agent`; Portainer listed all 4 host containers on 2026-07-28 |
| Docker runtime | Docker Engine 29.6.2, containerd 2.2.6, & runc 1.3.6 after the 2026-07-28 repair of a containerd 2.2.4 shim panic |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `007` as `docker-blue` |

## docker-network

| Workload | Details |
| --- | --- |
| Nginx Proxy Manager | Version 2.15.1; Docker Compose project under `/opt/docker/nginx-proxy-manager`; administrator initialized; wildcard/apex Let's Encrypt certificate assigned with Force SSL and HTTP/2 |
| NetBird | Management server 0.75.1 and dashboard 2.90.8 under `/opt/docker/netbird`; dashboard version verified 2026-08-04 from the OCI version and revision labels; authenticated dashboard live at `https://netbird.alphasecunited.com`; also runs as the Access-A routing peer (overlay `100.121.111.204`) advertising the `AlphaSec-Access` network `192.168.85.0/24` |
| Shared proxy network | External Docker network `proxy`, subnet `172.31.85.0/24`; Nginx Proxy Manager uses `172.31.85.10` |
| Portainer Edge Agent | `portainer/agent:2.39.1`; environment 9; compose under `/opt/docker/portainer-edge-agent`; UniFi policy `6a68eb3f052792cd2140c9ad` permits only `192.168.85.2` to `192.168.40.35` on TCP 8000 & 9443; Portainer listed all 5 host containers on 2026-07-28 |
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

## kasm-01

| Workload | Details |
| --- | --- |
| Kasm Workspaces | 1.19.0 Community Edition, `--role all` single-server install under `/opt/kasm/1.19.0`; eight containers running, seven Docker health checks healthy, and `kasm_proxy` running without a Docker health check; HTTPS on TCP 443 with the installer's self-signed certificate; RDP gateway on TCP 3389 |
| Docker | 29.6.2 with containerd 2.2.6, installed by the Kasm dependency script from `download.docker.com` |
| Workspace images | 19 lane workspaces and 14 Full workspaces across 15 local Docker image names; Parrot has Full, Normal, and VPN variants; Debian Malware uses lane 77; Docker Registry is null on all rows, so updates are manual instead of hourly rolling-tag pulls |
| Session isolation | `lab74`, `lab75`, `lab77`, and `lab79` macvlan networks on addressless VLAN parents; host shims persist before Docker; the `Lab Sessions` group limits sessions to one hour and three concurrent sessions with upload and selective persistent profiles enabled while download, clipboard, printing, sharing, and user storage mappings remain disabled |
| Storage | VM disk is 200 GiB on `ssd-lvm2` with discard enabled; guest ext4 reports 193 GB total, 154 GB used, and 39 GB available; the thin pool reports 68.25 percent data use; `baseline-parrot-2026-07-30` is the only VM snapshot |
| Swap | 4 GiB file at `/mnt/Kasm.swap`, required by Kasm's own guidance |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `012` as `kasm-01` |
| Network | Static `192.168.78.10/24` on LAB-MGMT/VLAN 78; sessions use `192.168.74.208/28`, `192.168.75.208/28`, `192.168.77.208/28`, or `192.168.79.208/28`; VLAN 74 exits through Proton, VLAN 75 uses ordinary WAN, and VLANs 77 and 79 have no Internet |

## security-01 / wazuh-01

| Workload | Details |
| --- | --- |
| Wazuh | Manager, indexer, & dashboard at package version 4.14.6-1 |
| node_exporter | 1.9.0 on 9100 |
| cAdvisor | `ghcr.io/google/cadvisor:v0.60.5` on 9101 from `/opt/docker/cadvisor`; one named container after the monitoring stack moved |
| Network | Static `192.168.72.2/24` on Security-A/VLAN 72 |

## alpha-prod-01

| Workload | Details |
| --- | --- |
| TeamSpeak | Two `teamspeak` containers |
| TS3 Manager | `joni1802/ts3-manager` |
| Playit agent | `ghcr.io/playit-cloud/playit-agent:0.17` |
| Portainer Edge Agent | `portainer/agent:2.39.1`; one of four remote Edge Agent hosts managed by Portainer server 2.39.5 |
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
| Jellyfin | `jellyfin/jellyfin:latest`; Intel Quick Sync render device and GPU-active playback verified; LAN port 8096 |
| Seerr | `ghcr.io/seerr-team/seerr:latest` 3.3.0; migrated from Jellyseerr with its existing configuration retained; setup wizard completed 2026-07-17 with confirmed Jellyfin, Sonarr, and Radarr connections |
| Arr services | LinuxServer Sonarr, Radarr, and Prowlarr `latest`; Sonarr and Radarr link to qBittorrent through separate categories; a 2026-07-21 episode and movie acquisition passed request, download, hard-link import, payload, library scan, and playback checks |
| FlareSolverr | `ghcr.io/flaresolverr/flaresolverr:latest`; a challenge-protected indexer was verified through the `flaresolverr` Prowlarr tag during the acquisition pass |
| Download path | LinuxServer qBittorrent `latest` shares `qmcgaw/gluetun:latest` network namespace; Proton WireGuard, kill switch, and provider-side port synchronization verified; qBittorrent rejects the documented 100-pattern executable/script payload baseline for new torrents |
| Portainer Edge Agent | `portainer/agent:2.39.1`; environment 8; compose under `/opt/docker/portainer-edge-agent`; Portainer listed all 10 host containers on 2026-07-28 |
| Wazuh agent | 4.14.6-1, held; enabled/active; manager ID `008` as `media-01` |
| Storage | One 100 GiB local LVM root volume contains configuration, downloads, media, and transcodes |
| Network | Static `192.168.40.42` on VLAN 40; no gateway inbound port forward |

## game-01

| Workload | Details |
| --- | --- |
| Pelican Panel | `ghcr.io/pelican-dev/panel:latest`, running v1.0.0-beta36 on Laravel 13.23.0; SQLite in the `pelican-panel_pelican-data` volume; compose under `/opt/docker/pelican-panel`; published as `games.alphasecunited.com` |
| Pelican Wings | v1.0.0-beta27 as a native `wings.service` binary, not a container; API on `0.0.0.0:8080`, SFTP on `0.0.0.0:2022`; server volumes under `/var/lib/pelican/volumes` owned `pelican` uid 999 gid 988; published as `wings.alphasecunited.com` |
| Node limits | 10240 MiB memory, 51200 MiB disk, 600 percent CPU, no overallocation; current assignments total 9216 MiB memory, 51200 MiB disk, and 500 percent CPU; allocations `192.168.80.30:25565` through `25575` |
| Vanilla Minecraft 26.2 | Pelican server ID 3; official Vanilla egg; Java 25; `VANILLA_VERSION=26.2`; 8192 MiB memory, 400 percent CPU, and 20480 MiB disk on `192.168.80.30:25565`; running and public; reached `Done (0.257s)!` after a controlled restart; public status returned 26.2, protocol 776, 0 of 20 players |
| Better Realism MC 7.2.0 | Pelican server ID 2; CurseForge server file 8570131; Minecraft 1.21.1 on Fabric 0.19.3 with Fabric Installer 1.1.2 and Java 21; stopped on 2026-08-09 and retained with its 363 MiB volume and world intact; 1024 MiB memory, 100 percent CPU, and 30720 MiB disk on `192.168.80.30:25566`; not public; its `-Xms4G` startup requires a limit restore before reactivation |
| Playit agent | Native package 1.0.9; enabled/active; the one assigned Minecraft tunnel forwards to `127.0.0.1:25565`; persistent secret at `/etc/playit/playit.toml`, mode 0600 and not versioned |
| Minecraft Playit relay | `minecraft-playit-relay.service`; enabled/active; dynamic user; loopback-only `127.0.0.1:25565` to Pelican allocation `192.168.80.30:25565` |
| node_exporter | 1.9.0 from APT, held; `:9100` |
| cAdvisor | `ghcr.io/google/cadvisor:v0.60.5` on `:9101`; registered 3 of 3 running containers |
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

The Wazuh manager and dashboard verified 14 active remote agents on 2026-08-03. All five Proxmox nodes share `default, proxmox`.

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
| kasm-01 | 012 | 4.14.6 | default | Active |
| grey-server | 013 | 4.14.6 | default, proxmox | Active |
| purple-server | 014 | 4.14.6 | default, proxmox | Active |
| blue-server | 015 | 4.14.6 | default, proxmox | Active |
| red-server | 016 | 4.14.6 | default, proxmox | Active |
| green-server | 017 | 4.14.6 | default, proxmox | Active |

## Guest exporter coverage

Added 2026-07-25, completed 2026-07-28. Every running Linux guest now exports on 9100, all at `node_exporter` 1.9.0. `docker-main` and `splunk-siem` run the upstream binary because their distributions can't supply that version: bookworm offers only 1.5.0-1+b6, and Rocky 10.2 offers none. Rollout is owned by [monitoring-exporters](../../../Platforms/Ansible/Source/monitoring-exporters/README.md).

| Guest | Install method | Service | Endpoint | cAdvisor |
|---|---|---|---|---|
| docker-main | Upstream binary (Debian 12 bookworm) | `node_exporter.service` | `192.168.40.35:9100` | 9101, 12 containers, `overlay2` |
| docker-network | Debian package | `prometheus-node-exporter.service` | `192.168.85.2:9100` | 9101, 5 containers, `overlayfs` |
| docker-blue | Debian package | `prometheus-node-exporter.service` | `192.168.40.39:9100` | 9101, 4 containers, `overlayfs` |
| media-01 | Debian package | `prometheus-node-exporter.service` | `192.168.40.42:9100` | 9101, 10 containers, `overlayfs` |
| alpha-prod-01 | Debian package | `prometheus-node-exporter.service` | `192.168.80.118:9100` | 9101, 8 containers, `overlayfs` |
| ansible-01 | Debian package | `prometheus-node-exporter.service` | `192.168.40.36:9100` | No containers |
| splunk-siem | Upstream binary (Rocky Linux 10.2) | `node_exporter.service` | `192.168.72.3:9100` | Podman, not applicable |
| app-01 | Pre-existing manual binary, left alone | `node_exporter.service` | `192.168.80.10:9100` | 9101, 7 containers, `overlayfs` |
| monitor-01 | Debian package | `prometheus-node-exporter.service` | `192.168.73.2:9100` | 9101, 7 containers, `overlayfs` |
| kasm-01 | Upstream binary (Ubuntu 24.04) | `node_exporter.service` | `192.168.78.10:9100`, bound to that address only | Not installed, deliberately |
| edge-01 | Debian package | `prometheus-node-exporter.service` | `192.168.30.10:9100` | No containers |

`security-01` also carries cAdvisor on 9101 with one container; its row is in the guest table above.

`kasm-01` is the one host whose exporter binds a single address instead of every interface. It holds macvlan shim addresses in VLANs 74, 75, 77, and 79, so an exporter on 0.0.0.0 would answer a lab session container on the same subnet with no gateway in the path. cAdvisor stays off that host for the same reason: a second listener is a second way into the lane holding the sessions.

`app-01` had been serving on 9100 since before this change and simply wasn't scraped. cAdvisor covered `docker-main` alone from 2026-07-25 to 2026-07-26, because v0.52.1 registers no containers under Docker 29's `overlayfs` driver. v0.60.5 from `ghcr.io/google/cadvisor` handles the containerd snapshotter. A Prometheus query on 2026-07-28 returned 53 named containers across all eight Docker hosts; eight are the cAdvisor containers. See [the troubleshooting record](../../../Platforms/Prometheus/Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

## Galaxy UPS telemetry

| Node | NUT version | Device | Endpoint | State |
| --- | --- | --- | --- | --- |
| red-server | 2.8.1-5 | `ups01`, APC Back-UPS RS 1500MS2 | `192.168.70.13:3493` | Driver and server active; `nut-monitor` disabled |
| grey-server | 2.8.1-5 | `ups02`, APC Back-UPS RS 1500MS2 | `192.168.70.10:3493` | Driver and server active; `nut-monitor` disabled |
