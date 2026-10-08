# Fleet Update

**Created:** 2026-10-05  
**Last updated:** 2026-10-07

**Implementation date:** 2026-10-05, 11:35 PM to 2026-10-06, 12:05 AM EDT  
**Status:** Updates complete; reboots done on 2026-10-06 except `grey-server` and `ubuntu-dev`; four held upgrades deferred

## Scope

I updated everything that was reachable and package- or image-managed: the five Proxmox nodes, the twelve running Linux guests, the 23 Compose projects the fleet inventory now lists on six hosts, the six Hawser agents, cAdvisor on eight Docker hosts, Semaphore on `ansible-01`, the Wazuh agents on fifteen hosts, and cloudflared on `edge-01`. The VMs `kali-pen` and `HQ-WS001` were stopped and stayed stopped. `parrot_os_mac`, `surface_pro` and `obipc` were powered off and unreachable. Coolify on `app-01` manages its own two projects and was already on its current release, 4.3.23.

Three days earlier the [2026-10-02 package run](Guest%20Package%20Updates%20-%202026-10-02.md) had patched the same guests, so the guest package step was small. The nodes had not been patched: each offered 97 to 99 packages, including `pve-manager` 9.2.21 and kernel 7.0.14-20-pve.

## Execution

Every long step ran as a transient systemd unit on the host doing the work, so the 60-second Executor tool limit never cut one off, and I read each log back afterwards. Times are Eastern.

| Time | Step | Result |
|---|---|---|
| 11:35:47 PM | `os-update.yml` on `ansible-01` for nine guests, `docker-blue` and `docker-network` excluded, `reboot=report`, no autoremove or autoclean | Ended 11:36:46 PM, exit 0; eight guests changed, `ansible-01` had nothing to install |
| 11:35:52 PM | `apt-get dist-upgrade` on `green-server`, the node with no guests | Ended 11:37:24 PM, exit 0; `pve-manager` 9.2.21 |
| 11:37:08 PM | `apt-get upgrade` on `ubuntu-dev`, run locally | Ended 11:37:35 PM, exit 0; 12 packages, including `docker-compose-plugin` 5.6.0 |
| 11:39:16 PM | `os-update.yml` for `docker-network`, then `docker-blue` | Both exit 0 by 11:39:31 PM |
| 11:39:24 PM | `dist-upgrade` on `red-server` | Ended 11:41:00 PM, exit 0 |
| 11:41:05 PM | `docker-compose-update.yml` for `docker-main`, `media-01`, `alpha-prod-01` and `monitor-01` after the inventory and pin changes below | Ended 11:44:44 PM, exit 0; 16 of 19 projects recreated at least one container, every container running and healthy |
| 11:42:54 PM | `dist-upgrade` on `purple-server` | Ended 11:44:48 PM, exit 0 |
| 11:42:57 PM | Semaphore 2.18.27 to 2.19.12 on `ansible-01` from the upstream `.deb`, checksum matched | Migrations through v2.19.14 finished; `/api/ping` 200 |
| 11:43:04 PM | `wazuh-agent` 4.14.8-1 on `ubuntu-dev` | Failed on a conffile prompt; repaired at 11:47 PM, see below |
| 11:46:53 PM | `dist-upgrade` on `blue-server` | Ended 11:48:56 PM, exit 0 |
| 11:46:57 PM | Compose run for `docker-network`, then `cadvisor.yml` from `monitoring-exporters` on eight hosts | Both exit 0 by 11:47:30 PM; NetBird recreated, NPM unchanged, cAdvisor 0.60.6 everywhere with every running container registered |
| 11:49:06 PM | `dist-upgrade` on `grey-server` | Ended 11:50:25 PM, exit 0 |
| 11:49:18 PM | Compose run for `docker-blue`, then the six Hawser updater helpers | Compose exit 2 because Executor failed its health gate; the helpers all exited 0 with Hawser 0.2.50 healthy on six hosts by 11:50:41 PM |
| 11:56:02 PM | `deploy.yml` from `wazuh-agent-deployment` with `wazuh_agent_version=4.14.8-1` on twelve hosts, then `edge-01` and `app-01` by ad-hoc apt | Exit 0 at 11:58:45 PM and 11:59:04 PM; every host active, held at 4.14.8-1 |
| 11:56 PM | `cloudflared` restarted on `edge-01` | 2026.10.0 running, four tunnel connections registered |
| 11:56 PM | Executor data directory handed to UID 65532 and the container restarted | Healthy in 20 seconds |

Node upgrades ran one at a time, each followed by a check that the six PVE services were active and the cluster still quorate at five votes before the next began. I used `--force-confdef --force-confold` with `DEBIAN_FRONTEND=noninteractive`, and no node reported a kept-back package afterwards.

## What changed

### Pins I moved

| Service | Host | From | To | How |
|---|---|---|---|---|
| Dockhand | docker-main | v1.0.48 | v1.0.51, digest `ffba7083…` | Compose file edit, [notes](https://github.com/Finsys/dockhand/releases) read for 1.0.49 to 1.0.51 |
| Ollama | docker-main | 0.33.3 | 0.35.1, digest `292ee794…` | Compose file edit; Open WebUI still lists `qwen3.5:2b`, Open WebUI itself unchanged at 0.11.4 |
| BookOrbit | docker-main | v3.1.0 | v3.2.0, digest `1020eef9…` | `APP_IMAGE` in the host `.env`; the `3.2.0` and `latest` tags share that digest |

The tracked copies under `Platforms/Ollama/Configuration/`, `Platforms/Dockhand/Configuration/docker-main-compose.yaml` and the BookOrbit README carry the same references.

### Floating tags that moved

Immich 3.2.2 to 3.2.4, CLI Proxy API 7.3.16 to 8.0.16, Jellyfin 12.1.0 to 12.2.0, Seerr 3.4.1 to 3.5.0, Sonarr 4.0.20.3014, Radarr 6.4.4.10685, Prowlarr 2.6.5.5623, qBittorrent 5.2.4, Prometheus 3.14.0 to 3.15.0, Grafana 13.2.2 to 13.2.3, Proxmox exporter 3.10.0 to 3.10.1, NetBird server 0.79.0 to 0.80.0 and dashboard 2.93.0 to 2.94.0, Hawser 0.2.48 and 0.2.49 to 0.2.50, cAdvisor 0.60.5 to 0.60.6 on `app-01` and `alpha-prod-01`. Homarr, Forgejo 16.0.5, MeshCentral 1.2.6, RustDesk 1.1.16, the TeamSpeak servers 3.13.8, Gluetun, FlareSolverr 3.5.2, PeaNUT, blackbox exporter 0.28.0 and the NUT exporter pulled no newer image; several were recreated anyway because the module reconciles labels and configuration, and each came back healthy with the same image.

### Packages

All five nodes report `pve-manager/9.2.21` with `7.0.14-20-pve` installed. The eight changed guests took the few packages that had appeared since 2026-10-02; `splunk-siem` took its DNF updates. On `ubuntu-dev` the kernel 7.0.0-38 that was already installed on 2026-10-02 is still waiting for a reboot. Docker Engine stayed at 29.8.2 everywhere.

### Wazuh agents

The manager had been on 4.14.8 since 2026-10-02 while every agent sat on a 4.14.6-1 hold, with `edge-01` on 4.14.5-1. The deploy play's version variable released each hold, installed 4.14.8-1 and re-applied the hold; `edge-01` and `app-01`, which are outside that inventory but carry the Wazuh repository, took the same package by ad-hoc apt. At 12:05 AM the manager listed all 15 remote agents Active, none pending or disconnected.

### Fleet inventory

The `docker_compose_targets` list in [fleet-updates](../../Platforms/Ansible/Source/fleet-updates/inventory/hosts.yml) was three weeks behind `docker compose ls`. I replaced `booklore` with `bookorbit`, added `homarr`, `sure`, `dockhand`, `deploy` (App Portal, two Compose files) and `meshcentral`, and dropped `docusaurus`, whose container has been stopped since 2026-09-22 and must not be started by a fleet run. The validator, README and the deployed copy on `ansible-01` match: 11 OS-update hosts, 6 Compose hosts, 23 projects.

## Failed attempts and repairs

**Baseline capture.** The pre-run ad-hoc `shell` call carried a Docker `--format` string, and Ansible's templating rejected the double braces on every host. The playbook that followed did not depend on it. I kept the [failed attempt](../Evidence/Fleet%20Update%20-%202026-10-05/Exports/guest-baseline-attempt.txt); the pre-change container inventory I had read through SSH Manager minutes earlier served as the baseline, and the [post-state capture](../Evidence/Fleet%20Update%20-%202026-10-05/Exports/guest-post-state.txt) used `{% raw %}` and succeeded. Every guest kept its boot ID.

**Wazuh agent on `ubuntu-dev`.** My manual `apt-get install wazuh-agent=4.14.8-1` lacked the `--force-confold` option. The package's post-install script prompted about `/etc/systemd/system/wazuh-agent.service`, a conffile that had been removed since the earlier install, read end-of-file on stdin, and aborted before it restored the saved `ossec.conf` and `client.keys` from its staging directory. The agent came up with the template's `MANAGER_IP` placeholder and an empty key file and refused to start. `dpkg --configure --force-confold wazuh-agent` completed the script, restored both files unchanged, and the agent was active and connected to TCP 1514 at 11:47 PM. The fleet play uses Ansible's apt module, whose defaults include that option, which is why none of the other hosts prompted. [Log](../Evidence/Fleet%20Update%20-%202026-10-05/Logs/ubuntu-dev-wazuh-agent.log).

**Executor.** The rolling `latest` tag moved Executor from a build that ran as root to one that runs as UID 65532, and the root-owned data directory stopped it with `EACCES` on `/data/secret.key`. Every tool call through Executor timed out for about eight minutes. I worked through direct SSH from `ubuntu-dev`, which already reaches `ansible-01` and `docker-blue`, changed the directory owner, and restarted the container. [Change record](../../Platforms/Executor/Documentation/Change%20Records/Rolling%20Image%20Recreation%20-%202026-10-05.md).

**Windows Update.** I started a Windows Update search through the agent API on `HQ-DC01`, `HQ-DC02`, `HQ-MGT01` and `win11-dev`, first as a detached process from the SSH session and then as a SYSTEM scheduled task. Neither wrote a result within twenty minutes, so I removed the task and the files under `C:\Temp` and left Windows alone. The last installed updates are from 2026-09-08 on the two domain controllers, 2026-09-11 on `HQ-MGT01` and 2026-09-24 on `win11-dev`.

## Verification

**Correction recorded 2026-10-07:** The failed-unit and target checks below missed docker-main's upstream exporter restart loop. Its packaged exporter supplied metrics while `node_exporter.service` kept restarting. These checks establish the container and target results stated below, not a clean exporter service state. I repaired the conflict and corrected the collector playbook in the [service repair](Service%20Failure%20Repairs%20-%202026-10-07.md).

- All five nodes: six PVE services active, cluster quorate with five votes, `apt-get -s dist-upgrade` reporting nothing left, every guest still running on its node.
- Guests: every boot ID unchanged; no new failed units beyond the seven pre-existing `openipmi.service` failures and `security-01`'s `prometheus-node-exporter.service`; `dpkg --audit`-level checks are implicit in the play's exit 0.
- Containers: 69 running across the eight Docker hosts, none restarting or unhealthy; the only exited containers are `docusaurus` on `docker-main`, which was already stopped, and the six Hawser updater helpers, which exit after they run.
- Prometheus: 50 of 50 targets up after Prometheus, Grafana and cAdvisor were recreated; Grafana reports database `ok` at 13.2.3.
- Endpoints answered on their bind addresses: Dockhand 307, Homarr 200, Sure 302, Open WebUI 200 and `/api/version` 0.11.4, BookOrbit 200, Forgejo 200, Immich `/api/server/version` 3.2.4, Ollama `/api/version` 0.35.1, CLI Proxy API root 200 with the unauthenticated model list still 401 and `https://aiproxy.alphasecunited.com` 200, Jellyfin 200 at 12.2.0, Seerr, Sonarr, Radarr, Prowlarr and qBittorrent 200, qBittorrent still inside Gluetun's network namespace with Gluetun healthy, NetBird dashboard 200 and management log at 0.80.0, NPM admin 200, `https://mcp.alphasecunited.com` 200, MeshCentral 200, RustDesk `hbbs` listening on 21115 and 21116, both TeamSpeak servers listening and the playit agent connected with two tunnels loaded.
- Semaphore: unit active, `semaphore version` 2.19.12, `/api/ping` and the login page 200. I removed the SQLite rollback copy I had taken once that passed.
- Wazuh: manager `v4.14.8`, 15 remote agents Active; every agent host holds `wazuh-agent` at 4.14.8-1.
- cloudflared on `edge-01`: 2026.10.0, four tunnel connections registered after the restart; Caddy 2.6.2 active.

The retained evidence is under [Fleet Update - 2026-10-05](../Evidence/Fleet%20Update%20-%202026-10-05/): the four guest play logs, the Compose, cAdvisor, Hawser and Wazuh logs, the five node upgrade logs, the two `ubuntu-dev` logs, and the two capture files. I removed the run directory from `ansible-01` and the scripts and logs from the five nodes afterwards, with no transient units left behind. I created no snapshots; the one rollback copy, Semaphore's database, is gone.

## Decisions I made, and what I held back

- **Nginx Proxy Manager stays at 2.15.1.** 2.16.0 exists, but the 2026-09-25 incident pinned NPM for a reason, and its release notes warn that the bundled certbot update can break DNS plugins. This proxy renews the wildcard through Cloudflare DNS-01, so that upgrade gets its own planned window.
- **Homarr stays at 1.77.2.** Upstream published 2.2.0 the same day; a major version of the dashboard is not something a fleet pull should land unread.
- **Sure stays at 0.7.5-hotfix.1.** The hotfix.2 release exists on GitHub, but neither `0.7.5-hotfix.2` nor `v0.7.5-hotfix.2` resolves on GHCR yet, and `latest` points at a 0.7.6 alpha.
- **App Portal stays at 0.6.0.** It is my own release train; 0.10.0 is out, and that upgrade follows its own change-record path with a database copy and the smoke test.
- **Docker MCP Gateway stays at v0.43.3.** 0.44.1 has no release notes, and this is the one component whose failure removes my remote access.
- **No reboots.** Node reboots mean migrating or stopping every guest, and `ubuntu-dev` is where I work from.

## Open state

Update 2026-10-06: I rebooted `green-server`, `red-server`, `purple-server` and `blue-server` with their guests, and `security-01` and `splunk-siem` on their own, in this order. `grey-server` and `ubuntu-dev` were not rebooted. [Fleet reboots](Fleet%20Reboots%20-%202026-10-06.md).

Reboots pending as of 2026-10-05, in the order I would take them: `green-server` (no guests), `red-server` (`media-01`), `purple-server` (`app-01`, `edge-01`, `alpha-prod-01`), `blue-server` (`ansible-01`, `monitor-01`, `docker-network`, `docker-blue`, which also carries Executor and the SSH Manager gateway), then `grey-server` with the rest. The VM kernels waiting from 2026-10-02 are unchanged: `alpha-prod-01`, `app-01` and `edge-01` on 6.12.111, `security-01` on 6.8.0-146, `splunk-siem` on 6.12.0-211.61.1, and `ubuntu-dev` on 7.0.0-38. The LXCs take their node's kernel at the node reboot. Each reboot needs the service and monitoring checks run again as the guest returns.

The four held upgrades above are listed in the root [TODO](../../TODO.md). The three physical machines were off and have had no update since whenever they were last on.
