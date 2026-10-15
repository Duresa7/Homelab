# Galaxy Services

**Created:** 2026-07-08  
**Last updated:** 2026-10-15

This inventory maps the workloads on Galaxy's 18 guests: 12 VMs and six LXCs. I read the versions below from the running services on 2026-09-24 and 2026-09-25, through SSH Manager, from each service's version endpoint, its OCI image label, or its package manager. On 2026-09-24 Prometheus scraped 57 targets across seven jobs with all 57 up, the Wazuh manager listed 15 remote agents with all 15 active, and six Docker hosts ran a Hawser Edge agent for Dockhand. A version marked with an earlier date is the last reading I have.

I verified the October 7 [service repairs](../../Maintenance/Service%20Failure%20Repairs%20-%202026-10-07.md): docker-main and security-01 serve upstream node_exporter 1.9.0 with their distro units masked; the unused NUT monitors on Red and Grey are masked, and Grey still serves UPS-02 telemetry.

## Recent changes

- 2026-10-15: I turned TSO, GSO and GRO off on `nic0` on Purple, Green and Red, then rebooted Green and Red to confirm the setting survives a boot. Red now runs `7.0.14-22-pve`; `media-01` was down for about a minute and a half and came back with all ten running containers and working DNS. [Change record and reboot checks](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md#after-reboot-verification).

- 2026-10-14: Purple's NIC transmit hang took `edge-01` and `alpha-prod-01` offline for about 54 minutes. After my October 15 power cycle, monitoring and workloads recovered and Playit loaded all three tunnels. LAN/public Minecraft, TeamSpeak and TS3 Manager checks passed. Minecraft logins were most likely impaired after it started at 12:37 AM until a separate container restart restored external DNS at 12:58:32 AM; authenticated joins remain untested. [Minecraft DNS persistence](../../../Platforms/Minecraft/README.md#open-items) remains open. [Outage and validation](../../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md).

- 2026-10-11: I increased `alpha-prod-01` to 8 GiB maximum and minimum RAM and Minecraft to a 4 GiB maximum heap with a 5 GiB container limit. I verified the retained world, Minecraft LAN/public responses and both TeamSpeak paths after the VM restart. [Memory increase and verification](../../../Platforms/Minecraft/Documentation/Change%20Records/Memory%20and%20Operator%20Update%20-%202026-10-11.md).

- 2026-10-09: I deployed Vanilla Minecraft Java Edition 26.3 on `alpha-prod-01` through Dockhand, verified LAN, loopback and public Playit status, and increased the host VM to 6 GiB maximum and minimum RAM. The retained Minecraft tunnel now uses the shared Playit agent; both TeamSpeak public paths remained up after the transfer. I restored `minecraft.alphasecunited.com` in Cloudflare and verified its SRV login transport; the custom name's server-list ping remains rejected by Playit. `app-01` is temporarily stopped with automatic startup disabled; Coolify is offline. [Deployment](../../../Platforms/Minecraft/Documentation/Change%20Records/Deployment%20-%202026-10-09.md), [DNS publication](../../../Platforms/Minecraft/Documentation/Change%20Records/DNS%20Publication%20-%202026-10-09.md).

- 2026-10-06: I rebooted `green-server`, `red-server`, `purple-server` and `blue-server` onto kernel 7.0.14-20-pve with their guests, plus `security-01` and `splunk-siem` onto their waiting kernels, and verified every service afterwards. `grey-server` and `ubuntu-dev` were not rebooted. [Fleet reboots](../../Maintenance/Fleet%20Reboots%20-%202026-10-06.md).

- 2026-10-05: I updated the whole Linux fleet: packages on all five Proxmox nodes (PVE 9.2.21, kernel 7.0.14-20-pve installed) and all twelve running Linux guests, 23 Compose projects on six hosts, the six Hawser agents, cAdvisor on eight hosts, Semaphore and the Wazuh agents. Node and VM reboots remain pending. [Fleet update](../../Maintenance/Fleet%20Update%20-%202026-10-05.md).

- 2026-10-05: I deployed Sure 0.7.5-hotfix.1 on `docker-main` at `https://sure.alphasecunited.com` through NPM host 36, as four containers on TCP 3005. [Deployment](../../../Platforms/Sure/Documentation/Change%20Records/Deployment%20-%202026-10-05.md).

- 2026-10-02: I updated host packages on all twelve running Linux guests. Docker Engine is 29.8.2 on all nine Docker hosts; Wazuh central packages are 4.14.8-1. Six VM reboots remain pending. [Maintenance and verification](../../Maintenance/Guest%20Package%20Updates%20-%202026-10-02.md).

- 2026-09-28: I replaced BookLore with BookOrbit v3.1.0 and PostgreSQL 18.6 on `docker-main`, preserving TCP 6060 and the BookLore HTTPS address. All 42 books imported, and the old application and MariaDB containers were removed. [Migration](../../../Platforms/BookOrbit/Documentation/Change%20Records/Migration%20from%20BookLore%20-%202026-09-28.md).

- 2026-09-27: I removed WUD from all six hosts and retired its monitoring, deployment and HTTPS configuration. [Retirement](../../../Platforms/Prometheus/Documentation/Change%20Records/WUD%20Retirement%20-%202026-09-27.md).

- 2026-09-27: I deployed Homarr 1.77.2 on `docker-main` at `https://dashboard.alphasecunited.com` through NPM host 34. [Deployment](../../../Platforms/Homarr/Documentation/Change%20Records/Deployment%20-%202026-09-27.md).

- 2026-09-24: Weebarr, deployed on `media-01` on 2026-09-21, was absent: no container, image or Compose entry, and its proxy host and DNS record deleted. [Weebarr Retirement](../../../Archive/Platforms/Weebarr/Documentation/Change%20Records/Retirement%20-%202026-09-25.md).
- 2026-09-23: I moved VM 103 `win11-dev` from Green to Grey. [Migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md).
- 2026-09-22: The internal documentation site and Homelab Dashboard containers on `docker-main` stopped at 3:39 and 3:40 AM Eastern and were still stopped on 2026-09-24. I retired Homelab Dashboard on 2026-09-26; the internal documentation site remains stopped.

## Cluster State

All five nodes report `pve-manager/9.2.21` after the 2026-10-05 node package upgrade, keep their lowercase `.galaxy` FQDN, and quorum holds at five votes. The [2026-10-07 package updates](../../Maintenance/OS%20Package%20Updates%20-%202026-10-07.md) installed kernel `7.0.14-22-pve` on every node except Green. Purple booted it during the 2026-10-15 [NIC outage recovery](../../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md), and Red during the [offload reboot check](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md#after-reboot-verification) the same morning. Blue still runs `7.0.14-20-pve` from the [2026-10-06 reboots](../../Maintenance/Fleet%20Reboots%20-%202026-10-06.md), and `grey-server` still runs `7.0.14-8-pve`. [Fleet update](../../Maintenance/Fleet%20Update%20-%202026-10-05.md).

| Node | FQDN | PVE | Running kernel (2026-10-15) | Newest installed kernel (2026-10-15) |
| --- | --- | --- | --- | --- |
| grey-server | `grey-server.galaxy` | 9.2.21 | `7.0.14-8-pve` | `7.0.14-22-pve` |
| purple-server | `purple-server.galaxy` | 9.2.21 | `7.0.14-22-pve` | `7.0.14-22-pve` |
| blue-server | `blue-server.galaxy` | 9.2.21 | `7.0.14-20-pve` | `7.0.14-22-pve` |
| red-server | `red-server.galaxy` | 9.2.21 | `7.0.14-22-pve` | `7.0.14-22-pve` |
| green-server | `green-server.galaxy` | 9.2.21 | `7.0.14-20-pve` | `7.0.14-20-pve` |

## Guest Workloads

| Guest | Type | Node | Role | Key workloads |
| --- | --- | --- | --- | --- |
| HQ-DC01 | VM 301 | grey-server | First domain controller for `ad.alphasecunited.com` (`192.168.65.10`, VLAN 65) | AD DS, AD-integrated DNS, global catalog, all five operations master roles<br>LDAPS on TCP 636 since 2026-09-20<br>OpenSSH |
| HQ-DC02 | VM 302 | grey-server | Second domain controller (`192.168.65.11`, VLAN 65) | AD DS, AD-integrated DNS, global catalog<br>LDAPS on TCP 636 since 2026-09-20<br>OpenSSH |
| HQ-MGT01 | VM 303 | grey-server | Windows management and hybrid identity (`192.168.65.12`, VLAN 65) | [Windows Admin Center](../../../Platforms/Windows%20Admin%20Center/README.md) 2.7.21.5, HTTPS 443<br>Azure Connected Machine agent 1.67.03504.3207, Connected<br>Entra provisioning agent service running<br>OpenSSH |
| HQ-WS001 | VM 310 | grey-server | Windows 11 test workstation (`192.168.65.20`, VLAN 65); stopped on 2026-09-24 | Windows 11 Pro 25H2<br>Windows LAPS and the Tier 2 local-administrator policy<br>OpenSSH since 2026-09-19 |
| kali-pen | VM 102 | grey-server | Penetration-testing VM on VLAN 40; stopped on 2026-09-24 | Kali Linux 2026.2 installer build |
| win11-dev | VM 103 | grey-server | Standalone Windows development workstation (`192.168.40.117`, VLAN 40) | Windows 11 Pro 25H2<br>OpenSSH Server<br>QEMU guest agent; no development tools installed |
| ubuntu-dev | VM 105 | grey-server | Ubuntu development workstation | GNOME Shell 50.1<br>Docker 29.7.2<br>VS Code 1.136.1<br>Node.js 24.19.0 via nvm<br>GitHub CLI 2.98.0<br>Wazuh agent 4.14.8<br>node_exporter 1.10.2<br>Samba (SMB2 to SMB3, TCP 445 on `lo` and `ens18`, shares `ai-agent` and `shared-folder`, Samba user `dkadi`), see [Samba](../../../Platforms/Samba/README.md) |
| ansible-01 | LXC 100 | blue-server | Automation and node provisioning | Ansible 14.2.0 / ansible-core 2.21.2<br>Semaphore 2.19.12<br>Galaxy PXE<br>tftpd-hpa 5.2+20240610-3<br>Wazuh agent 4.14.8 |
| docker-main | LXC 110 | grey-server | Docker apps | Homarr 1.77.2<br>Sure 0.7.5-hotfix.1<br>Immich 3.2.4<br>BookOrbit 3.2.0<br>Forgejo 16.0.5<br>Dockhand 1.0.51<br>CLI Proxy API 8.0.16<br>Ollama 0.35.1 / Qwen 3.5 2B<br>Open WebUI 0.11.4<br>App Portal 0.6.0<br>Internal documentation site, stopped since 2026-09-22<br>Wazuh agent 4.14.8 |
| monitor-01 | LXC 104 | blue-server | Infrastructure monitoring (`192.168.73.2`, VLAN 73) | Prometheus 3.15.0<br>Grafana 13.2.3<br>Proxmox exporter 3.10.1<br>blackbox exporter 0.28.0<br>NUT exporter<br>Discord alert bot<br>PeaNUT 6.0.0<br>cAdvisor 0.60.6<br>Hawser Edge 0.2.50<br>Wazuh agent 4.14.8 |
| docker-network | LXC 107 | blue-server | Network access control plane | Nginx Proxy Manager 2.15.1<br>NetBird server 0.80.0 / dashboard 2.94.0<br>Hawser Edge 0.2.50<br>Wazuh agent 4.14.8 |
| docker-blue | LXC 108 | blue-server | Remote access and integrations | Docker MCP Gateway 0.43.3, two instances<br>SSH Manager MCP<br>UniFi Network MCP<br>Executor 1.6.10<br>RustDesk hbbs / hbbr 1.1.16<br>MeshCentral 1.2.6<br>Hawser Edge 0.2.50<br>Wazuh agent 4.14.8 |
| app-01 | VM 116 | purple-server | App platform, temporarily stopped since 2026-10-09; automatic startup disabled | Installed: Coolify 4.4.3<br>Traefik 3.7.12<br>PostgreSQL 15.19 / Redis 7.4.11 / Sentinel 1.0.2<br>cAdvisor 0.60.6<br>node_exporter / Wazuh agent 4.14.8 |
| edge-01 | VM 121 | purple-server | Edge ingress | Caddy 2.6.2<br>cloudflared 2026.10.0<br>Wazuh agent 4.14.8 |
| security-01 | VM 200 | grey-server | Security monitoring (`192.168.72.2`, VLAN 72) | Wazuh 4.14.8<br>Wazuh MCP Server<br>node_exporter<br>cAdvisor<br>Hawser Edge 0.2.50 |
| alpha-prod-01 | VM 401 | purple-server | Voice and game services | [Vanilla Minecraft Java Edition 26.3](../../../Platforms/Minecraft/README.md), LAN and public Playit verified<br>Two TeamSpeak 3 Server 3.13.8 instances<br>TS3 Manager<br>TeamSpeak reachability collector<br>Playit agent<br>Hawser Edge 0.2.50<br>Wazuh agent 4.14.8 |
| splunk-siem | VM 109 | grey-server | SIEM (`192.168.72.3`, VLAN 72) | Splunk Enterprise 10.4.0<br>Enterprise Security 8.5.1<br>SC4S<br>No Wazuh agent |
| media-01 | LXC 842 | red-server | Media automation and playback | Jellyfin 12.2.0<br>Seerr 3.5.0<br>Sonarr 4.0.20 / Radarr 6.4.4 / Prowlarr 2.6.5<br>FlareSolverr 3.5.2<br>qBittorrent 5.2.4 through Gluetun and Proton VPN<br>Hawser Edge 0.2.50<br>Wazuh agent 4.14.8 |

## HQ-DC01, HQ-DC02 and HQ-MGT01

The forest build, LDAPS and the management tooling are recorded under [Active Directory](../../../Platforms/Active%20Directory/README.md). On 2026-09-25 `azcmagent show` on HQ-MGT01 reported agent 1.67.03504.3207, status Connected, and a heartbeat at 1:32 AM Eastern. The `WindowsAdminCenter`, `WindowsAdminCenterAccountManagement`, `AADConnectProvisioningAgent` and `himds` services were running. The Windows Admin Center executables read file version 2.7.21.5; the Active Directory extension 0.86.0 and DNS extension 2.76.0 are the 2026-09-12 readings. No Windows guest runs a Wazuh agent.

## ansible-01

| Workload | Details |
| --- | --- |
| Ansible | Control node; `ansible` resolves to `/usr/local/bin/ansible`, community 14.2.0 with ansible-core 2.21.2. The Debian packages `ansible` 12.0.0 and `ansible-core` 2.19.4 are also installed and shadowed on PATH |
| Semaphore | 2.19.12 since 2026-10-05, installed from the upstream `.deb` after a checksum match; systemd unit active, running as root from `/root/config.json` with SQLite at `/root/database.sqlite`; HTTP UI on TCP 3000; three projects (Server-SSH 13 templates, Fleet-Updates 6, Monitoring-Exporters 4), 23 templates, no schedules |
| Wazuh agent | 4.14.8-1 since 2026-10-05, held; manager ID `009` as `ansible-01` |
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
| Wazuh agent | 4.14.8 since 2026-10-05, manager ID `020`, manager `192.168.72.2`; version held in apt |
| node_exporter | `prometheus-node-exporter` 1.10.2, `192.168.40.179:9100` |
| SSH | key-based login; host signing key registered on GitHub for verified commits |

## Dockhand management

[Dockhand 1.0.51](../../../Platforms/Dockhand/README.md) runs on `docker-main` at `https://dockhand.alphasecunited.com` and replaced Dockge on 2026-09-15. It manages `docker-main` through the local Docker socket and six hosts through Hawser Edge agents, all 0.2.50 since the 2026-10-05 updater run. `app-01` runs no Hawser agent, so Coolify's containers stay outside Dockhand. On 2026-09-16 the fleet held 64 running containers in 42 Compose projects, all imported for UI editing. Dockhand rewrote 11 of those 42 host files into its own JSON form when it imported them, so the tracked copies under each platform's `Configuration/` are the authored reference. [Replacement record](../../../Platforms/Dockhand/Documentation/Change%20Records/Dockge%20Replacement%20-%202026-09-15.md), [registry and agent cutover](../../../Platforms/Dockhand/Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md).

## docker-main

19 containers were running on 2026-10-05 after adding Sure's four. No Hawser agent runs here, because Dockhand itself does.

| Workload | Details |
| --- | --- |
| Homarr | 1.77.2 from `ghcr.io/homarr-labs/homarr:v1.77.2`; `/opt/docker/homarr`; TCP 7575; `dashboard.alphasecunited.com` through NPM host 34; persistent `/appdata` and initial administrator verified after restart; nine integrations on one private dashboard, consolidated on 2026-09-27. [Platform record](../../../Platforms/Homarr/README.md) |
| Sure | 0.7.5-hotfix.1 from `ghcr.io/we-promise/sure:0.7.5-hotfix.1`, with PostgreSQL 16 and Redis 8; `/opt/docker/sure`; TCP 3005; `sure.alphasecunited.com` through NPM host 36; administrator login and data verified after a full stack restart; sign-up closed. [Platform record](../../../Platforms/Sure/README.md) |
| Internal documentation site | `docusaurus` container from `forgejo.alphasecunited.com/homelab-images/docusaurus:stable`; exited with code 0 at 3:40 AM Eastern on 2026-09-22 and still stopped on 2026-09-24, with restart policy `unless-stopped`. NPM has no proxy host for it |
| Immich | Server and machine learning v3.2.4 since 2026-10-05 (`release-cuda` for machine learning); PostgreSQL `14-vectorchord0.4.3-pgvector0.8.1-pgvectors0.2.0` and Valkey 9; NVENC transcoding and CUDA machine learning on the GTX 1080 Ti since 2026-09-05; TCP 2283 |
| BookOrbit | v3.2.0 since 2026-10-05 (digest-pinned), with PostgreSQL 18.6; TCP 6060; replaced BookLore on 2026-09-28 |
| Forgejo | 16.0.5 from `codeberg.org/forgejo/forgejo:16`, HTTP 3000 and SSH 222; also the private registry for the `homelab-images` custom images |
| Dockhand | v1.0.51 (`fnsys/dockhand:v1.0.51`, digest-pinned) since 2026-10-05; TCP 3003; NPM host 31 |
| CLI Proxy API | v8.0.16 (commit a2976eb, built 2026-10-05) since the 2026-10-05 pull of `latest`; the unauthenticated model list still returns 401 and the management page 200; Compose under `/opt/docker/cli-proxy-api`; TCP 8317 plus five auxiliary listeners; published internally as `https://aiproxy.alphasecunited.com` |
| Ollama | 0.35.1 (`/api/version`, digest-pinned) since 2026-10-05; `qwen3.5:2b` was the only installed model on 2026-09-06; API bound to `192.168.40.35:11434` without NPM or WAN publication |
| Open WebUI | 0.11.4 (`/api/version`) from the rolling `main` tag; TCP 3002; `openwebui.alphasecunited.com` through NPM host 28 |
| App Portal | 0.6.0 from `ghcr.io/duresa7/app-portal-server:0.6.0`; TCP 3004; `appportal.alphasecunited.com` through NPM host 32. [Platform record](../../../Platforms/App%20Portal/README.md) |
| Wazuh agent | 4.14.8-1 since 2026-10-05, held; manager ID `021`, enrolled 2026-09-06 after the old agent was found pointing at the manager's pre-migration address. [Re-enrollment record](../../../Platforms/Wazuh/Documentation/Change%20Records/docker-main%20Agent%20Re-enrollment%20-%202026-09-06.md) |
| Host services | node_exporter on 9100 (systemd), `wazuh-agent`, `php8.2-fpm` |
| Project directories | Compose projects live under `/opt/docker`. I removed five container-less leftover projects there on 2026-09-06; see [Documentation Staleness Audit - 2026-09-06](../../Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md) |

## monitor-01

| Workload | Details |
| --- | --- |
| Prometheus | 3.15.0 on TCP 9090; `restart: always`; 15-day retention; 50 of 50 targets up on 2026-10-05 across six jobs: blackbox 22, cAdvisor 8, node 17, NUT 1, Proxmox 1, self-scrape 1. Prometheus holds no alert rules |
| Grafana | 13.2.3 on TCP 3000; 23 alert rules in `alphasec-united-alerts.yaml` and one contact point, `discord-bot`; 27 dashboards in the [Prometheus platform](../../../Platforms/Prometheus/README.md) configuration |
| Proxmox exporter | 3.10.1 on TCP 9221, using `pve-exporter@pve!monitor01` with `PVEAuditor` |
| blackbox exporter | 0.28.0 on TCP 9115; probes the internal NPM names plus the alert bot's health endpoint |
| NUT exporter | `hon95/prometheus-nut-exporter:latest` on TCP 9995; scrapes UPS-02 on grey-server; UPS-01 has had no data path since 2026-08-28 |
| Discord alert bot | `forgejo.alphasecunited.com/homelab-images/alert-bot:stable`, container created 2026-09-16; receives Grafana webhooks on TCP 8080 over the Compose network and posts to one Discord channel. Source in [Discord Alert Bot](../../../Platforms/Discord%20Alert%20Bot/README.md) |
| node_exporter | Debian `prometheus-node-exporter` 1.9.0-1+b4 on TCP 9100, systemd |
| cAdvisor | 0.60.6 on TCP 9101 |
| PeaNUT | 6.0.0; UPS dashboard on `192.168.73.2:8090`; its configuration lists NUT servers red-server and grey-server on TCP 3493 |
| Hawser | 0.2.50 |
| Wazuh agent | 4.14.8-1 since 2026-10-05, held; manager ID `010` as `monitor-01` |
| Network | Static 192.168.73.2/24 on `MONITOR-A`, VLAN 73; UniFi DHCP serves .6 through .254 |

The [Uptime dashboard](../../../Platforms/Prometheus/Documentation/Change%20Records/Uptime%20Dashboard%20-%202026-09-15.md) went live on 2026-09-15 with 29 service checks. `edge-uptime.timer` on edge-01 reports the Cloudflare connection count and the Caddy and Coolify origin responses through the node_exporter textfile collector.

## docker-blue

11 containers were running on 2026-09-24. cloudflared and the Discord alert bot do not run here.

| Workload | Details |
| --- | --- |
| Docker MCP Gateway | `docker/mcp-gateway:v0.43.3`, two instances: `docker-mcp-gateway` for UniFi Network on `192.168.40.39:8811` and `ssh-manager-mcp-gateway` for SSH Manager on `192.168.40.39:8812`, both bearer-authenticated Streamable HTTP |
| UniFi Network MCP | `mcp-unifi-network` from `forgejo.alphasecunited.com/homelab-images/unifi-network-mcp:stable`; one shared controller connection, no published host port |
| SSH Manager MCP | `mcp-ssh-manager` from `forgejo.alphasecunited.com/homelab-images/mcp-ssh-manager:stable`, SSH Manager behind mcp-proxy on the Compose network only; 24 server definitions on 2026-09-24; enrolled host keys on the `ssh-manager-state` volume |
| Executor | 1.6.10 from `ghcr.io/usefulsoftwareco/executor-selfhost:latest`, container recreated 2026-10-05 on the image that runs as UID 65532; Compose under `/opt/docker/executor`; internal HTTPS at `mcp.alphasecunited.com`. [Platform record](../../../Platforms/Executor/README.md) |
| RustDesk | `hbbs` and `hbbr` 1.1.16 from `rustdesk/rustdesk-server:latest`; [platform record](../../../Platforms/RustDesk/README.md) |
| MeshCentral | 1.2.6 (image label `1.2.6-mongodb`) from `ghcr.io/ylianst/meshcentral:latest`; HTTPS on `192.168.40.39:443`, published as `mesh.alphasecunited.com` through NPM host 29. [Platform record](../../../Platforms/MeshCentral/README.md) |
| cAdvisor, Hawser | `ghcr.io/google/cadvisor:latest` 0.60.6, Hawser 0.2.50 |
| Docker runtime | Docker Engine 29.8.2 and containerd 2.3.6 after the 2026-10-02 package updates; runc 1.5.1 was last recorded on 2026-09-06 |
| Wazuh agent | 4.14.8-1 since 2026-10-05, held; manager ID `007` as `docker-blue` |

## docker-network

| Workload | Details |
| --- | --- |
| Nginx Proxy Manager | 2.15.1, pinned by tag and excluded from Dockhand updates since 2026-09-25; Compose under `/opt/docker/nginx-proxy-manager`; 24 live proxy hosts and eleven soft-deleted on 2026-09-27; one Let's Encrypt certificate for `*.alphasecunited.com` and the apex, valid to 2026-12-08, used by every live host. [Platform record](../../../Platforms/Nginx%20Proxy%20Manager/README.md) |
| NetBird | One combined `netbirdio/netbird-server:latest` container reporting management server 0.80.0, recreated on 2026-10-05, plus `netbirdio/dashboard:latest` labelled v2.94.0; no separate signal or relay container; also the Access-A routing peer advertising `192.168.85.0/24`. [Platform record](../../../Platforms/Netbird/README.md) |
| Shared proxy network | External Docker network `proxy`, subnet `172.31.85.0/24`; Nginx Proxy Manager uses `172.31.85.10` |
| cAdvisor, Hawser | Running; cAdvisor 0.60.6, Hawser 0.2.50 |
| Wazuh agent | 4.14.8-1 since 2026-10-05, held; manager ID `011` as `docker-network` |

## app-01

I stopped VM 116 on 2026-10-09 and disabled automatic startup. The installed workloads below are offline; the same-day running-state checks describe the period before shutdown. [Deployment and verification](../../../Platforms/Minecraft/Documentation/Change%20Records/Deployment%20-%202026-10-09.md).

| Workload | Details |
| --- | --- |
| Coolify | 4.4.3, verified 2026-10-09 from the running image tag, `COOLIFY_VERSION`, and `/var/www/html/config/constants.php` (the image label `v4.5.1-33486634677` is not the app version); Sentinel 1.0.2, PostgreSQL 15.19, Redis 7.4.11. No separate realtime container; Coolify itself publishes ports 6001-6002. [Live verification](../../../Platforms/Coolify/README.md#containers-verified-2026-10-09) |
| Traefik | Coolify ingress proxy `traefik:v3.7`, label v3.7.12 |
| cAdvisor | 0.60.6 since 2026-10-05 |
| Generated apps | None on 2026-10-09; the complete Docker inventory held six running, healthy platform and monitoring containers and no stopped containers |
| node_exporter | `node_exporter.service` active on 2026-10-09 |
| Hawser | Not installed; Coolify manages this host |
| Wazuh agent | 4.14.8-1 since 2026-10-05, held; manager ID `004` as `app-01` |

## edge-01

| Workload | Details |
| --- | --- |
| Caddy | 2.6.2, unit active on 2026-09-25 |
| cloudflared | 2026.10.0, installed by the 2026-10-05 package run and running since I restarted the unit the same night; four tunnel connections registered. [Tunnel record](../../../Infrastructure/Network/Cloudflare/Configuration/edge-01.md) |
| Wazuh agent | 4.14.8-1 since 2026-10-05, held; manager ID `005` as `edge-01` |
| Containers | Docker is not installed |

## security-01

| Workload | Details |
| --- | --- |
| Wazuh | Manager, indexer and dashboard; `wazuh-control info` reports v4.14.8 on 2026-10-02; all three services active |
| Wazuh MCP Server | `forgejo.alphasecunited.com/homelab-images/wazuh-mcp-server:stable`, healthy on 2026-09-24; host-networked at `192.168.72.2:3000`; read-only Manager and Indexer identities; upstream 4.3.0 is the last version I recorded |
| node_exporter | 1.9.0 on 9100 |
| cAdvisor | `ghcr.io/google/cadvisor:latest` on 9101 from `/opt/docker/cadvisor` |
| Hawser | 0.2.50 |
| Network | Static `192.168.72.2/24` on Security-A, VLAN 72 |

## alpha-prod-01

Eight containers were running on 2026-09-25. On 2026-10-09 I verified eight running containers, now including Minecraft and excluding the retired WUD stack, plus the stopped Hawser updater. Since 2026-10-11 the VM has 8 GiB maximum and minimum RAM, six vCPUs and a 60 GiB disk.

| Workload | Details |
| --- | --- |
| Minecraft | Vanilla Java Edition 26.3, protocol 777, `itzg/minecraft-server:stable-java25`; TCP 25565; 4 GiB maximum heap, 5 GiB container limit since 2026-10-11; world under `/opt/docker/minecraft/data`; managed as `minecraft` in Dockhand environment 6. LAN, loopback and the retained public Playit tunnel verified on 2026-10-09. `minecraft.alphasecunited.com` resolves through Cloudflare; SRV login transport verified, custom hostname server-list ping rejected. [Platform record](../../../Platforms/Minecraft/README.md) |
| TeamSpeak | `ts-valorant-02` and `ts-valorant-03`, both TeamSpeak 3 Server 3.13.8, recreated 2026-09-18. [Teamspeak Hosting](../../../Platforms/Teamspeak%20Hosting/README.md) |
| TS3 Manager | `joni1802/ts3-manager` on TCP 9000, NPM host 22 |
| TeamSpeak reachability collector | `teamspeak-monitor` from `forgejo.alphasecunited.com/homelab-images/teamspeak-monitor:stable`; reads each server's public SRV record every cycle and feeds the reachability dashboard |
| Playit agent | `ghcr.io/playit-cloud/playit-agent:latest`, image label 1.0; three tunnels since 2026-10-09, serving both TeamSpeak instances and Minecraft |
| cAdvisor, Hawser | cAdvisor 0.60.6, Hawser 0.2.50 |
| Wazuh agent | 4.14.8-1 since 2026-10-05, held; manager ID `006` as `alpha-prod-01` |

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

Ten containers were running after WUD retirement on 2026-09-27: eight in the `media-stack` Compose project at `/opt/media-stack/compose.yml`, plus `cadvisor` and `hawser` under `/opt/docker/`. The earlier 2026-09-24 count was 11, including WUD.

| Workload | Details |
| --- | --- |
| Jellyfin | 12.2.0 (`/System/Info/Public`, 2026-10-05), server name `Jelly-Media`, TCP 8096; Movies, TV Shows and Anime libraries; Intel Quick Sync render device. [Media Stack](../../../Platforms/Media%20Stack/README.md) |
| Seerr | v3.5.0 from `ghcr.io/seerr-team/seerr:latest`; the container is still named `jellyseerr`; TCP 5055 |
| Arr services | Sonarr 4.0.20.3014 (TCP 8989), Radarr 6.4.4.10685 (TCP 7878), Prowlarr 2.6.5.5623 (TCP 9696), all LinuxServer images |
| FlareSolverr | v3.5.2 |
| Download path | qBittorrent 5.2.3 (libtorrent 2.0.14) in the `qmcgaw/gluetun:latest` network namespace, UI on TCP 8080; Gluetun carries no version label (image built 2026-09-23, revision 1267bae) |
| cAdvisor, Hawser | cAdvisor 0.60.6 on 9101, Hawser 0.2.50 |
| Wazuh agent | 4.14.8-1 since 2026-10-05, held; manager ID `008` as `media-01` |
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

On 2026-10-06 at 12:05 AM Eastern, after the agent upgrade, `agent_control -l` on `security-01` listed the manager (`000`) and 15 remote agents. `splunk-siem` and the Windows guests run no agent. I removed `debian-dev`'s agent `019` on 2026-08-14 and `game-01`'s agent `018` on 2026-09-12. The version column is the 2026-10-05 package reading after the [fleet update](../../Maintenance/Fleet%20Update%20-%202026-10-05.md); every host holds the package at 4.14.8-1, the manager's own version.

| Host | Manager ID | Version (2026-10-05) | Group | State (2026-10-06) |
|---|---:|---|---|---|
| app-01 | 004 | 4.14.8 | default | Active |
| edge-01 | 005 | 4.14.8 | default, edge | Active |
| alpha-prod-01 | 006 | 4.14.8 | default | Active |
| docker-blue | 007 | 4.14.8 | default | Active |
| media-01 | 008 | 4.14.8 | default | Active |
| ansible-01 | 009 | 4.14.8 | default | Active |
| monitor-01 | 010 | 4.14.8 | default | Active |
| docker-network | 011 | 4.14.8 | default | Active |
| grey-server | 013 | 4.14.8 | default, proxmox | Active |
| purple-server | 014 | 4.14.8 | default, proxmox | Active |
| blue-server | 015 | 4.14.8 | default, proxmox | Active |
| red-server | 016 | 4.14.8 | default, proxmox | Active |
| green-server | 017 | 4.14.8 | default, proxmox | Active |
| ubuntu-dev | 020 | 4.14.8 | workstation | Active |
| docker-main | 021 | 4.14.8 | default | Active |

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
