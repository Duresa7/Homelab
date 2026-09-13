# Game 01 Retirement

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

**Status:** Retired from active service; stopped container and data retained.

I retired Game 01 from the homelab on 2026-09-12. CT 123 was already stopped on `green-server` when I checked it. I disabled automatic startup and removed the service's monitoring, Wazuh enrollment, DNS publication, proxy routes, dedicated firewall policies, and automation targets. I moved its platform records, deployment record, dedicated sudo maintenance record, and node dashboard into `Archive/` and repaired their links.

I retained `local-lvm:vm-123-disk-0`, the 80 GiB root volume holding Pelican and the Minecraft worlds. The request to archive did not settle whether to destroy the game data, so I kept the offline container. Its 6 vCPUs, 12 GiB memory and 2 GiB swap remain configured but inactive. I created no snapshot or backup. The [archived guest record](../../../../Operations/Inventory/Galaxy/Game%2001%20Archived%20Guest%20-%202026-09-12.md) preserves its former inventory.

## Changes and verification

| Area | Change | Observed result |
|---|---|---|
| Proxmox | `pct set 123 --onboot 0` on Green | `pct status 123` returned `stopped`; configuration returned `onboot: 0`; `pvesm list local-lvm --vmid 123` retained the 85,899,345,920-byte root volume |
| Prometheus | Removed `192.168.80.30:9100`, `192.168.80.30:9101`, and the `https://games.alphasecunited.com/` blackbox probe; added a Proxmox metric drop for `id="lxc/123"` | `promtool check config` passed before each HUP reload. The repository target assertion passed against the live API: 54 expected targets UP, comprising 34 exporters and 20 probes. Instant queries for the retired host, panel and CT returned no series; no remaining probe failed |
| Grafana | Removed `node-game-01.json` from the live provider directory and the dashboard generator inventory | Authenticated `/api/search?type=dash-db` returned 26 dashboards and no `node-game-01`. All 24 shared rules reported health `ok`. No Game 01 alert was firing or pending |
| Wazuh | Removed disconnected agent `018` with `manage_agents -r 018` | `agent_control -l` subsequently returned the manager and 15 remote agents, all active, with no Game 01 enrollment |
| Public DNS | Deleted the Minecraft CNAME and `_minecraft._tcp.minecraft.alphasecunited.com` SRV in Cloudflare | Both deletes returned HTTP 200; exact-name readbacks returned zero records |
| Local DNS | Deleted the `games.alphasecunited.com` and `wings.alphasecunited.com` A records | UniFi returned 28 records with neither retired name |
| NPM | Marked proxy hosts 24 and 25 deleted and disabled in SQLite and removed their generated Nginx files | Both rows were first checked against `192.168.80.30`. `nginx -t` and reload passed; no active proxy targets that address. The retained set has 22 enabled proxy hosts |
| UniFi firewall | Deleted `Allow NPM to game-01 Panel`, `Allow NPM to game-01 Wings`, and `Allow game-01 to NPM HTTPS`; removed the host from the shared monitoring destination list | Readback found no Game 01 name or address in 80 user policies or 23 firewall groups. The shared monitoring rule retains only `192.168.80.10` and `192.168.80.118` |
| Ansible | Removed the host from fleet updates, access baseline, monitoring exporters, SSH-key automation, and Wazuh deployment inventories, locally and on `ansible-01`; removed it from the three human identity allowlists on the controller | All five live inventories parsed with `LC_ALL=C.UTF-8` and excluded `game-01`. Local validators passed: 11 OS-update hosts, 6 Compose hosts and 25 projects; 9 node-exporter hosts and 8 cAdvisor hosts; 10 account targets and zero key-only targets; 16 SSH-key hosts |
| SSH Manager | Removed the host's server definition and sudo entry, then recreated only the SSH Manager service | The reloaded catalog returned 21 configured servers and no `game_01` |
| Repository | Archived dedicated records and dashboard; updated living inventories, service references and generated dashboard allowances | All 26 dashboard layouts passed; moved-file links and `git diff --check` passed |

These steps were verified from tool responses and live API readbacks. I did not retain separate terminal transcripts or API response exports.

## Verification corrections

An initial unprivileged Wazuh command failed with permission denied; the privileged call succeeded. An attempted sudo call on the Proxmox node failed because it already connects as root and has no `sudo` binary; the ordinary root call succeeded. The first Ansible inventory check failed because the inherited locale was unsupported; rerunning with `LC_ALL=C.UTF-8 LANG=C.UTF-8` parsed all five inventories.

Grafana 13 keeps dashboards in unified storage and alert state outside the old `alert_instance` table. Empty results from the legacy tables did not prove deletion. I verified the dashboard count, alert states and rule health through authenticated APIs instead. Two cached Game 01 entries remained: `Metrics source stopped reporting` in `Normal (NoData)` and `CPU is pinned` in `Normal`. They are resolved state, not firing or pending alerts. The deleted scrape targets and dropped Proxmox series prevent new evaluations for this guest.

## Retained state

The offline container, its installed services, and its game data remain intact. The external Playit account's relay allocation was not deleted; its local agent cannot forward traffic while the container is stopped, and the Minecraft public DNS names no longer publish it. Historical monitoring samples and past notifications remain subject to their normal retention. Shared fleet alert rules and cross-system dated maintenance records retain their history.

Restarting CT 123 alone does not restore publication, monitoring or management. A future restoration would require restoring those registrations from the archived configuration and re-enrolling Wazuh. Permanent deletion of the retained container and game data remains a separate decision.
