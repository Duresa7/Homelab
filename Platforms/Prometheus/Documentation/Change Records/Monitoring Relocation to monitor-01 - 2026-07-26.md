# Monitoring Relocation to monitor-01

**Created:** 2026-07-26  
**Last updated:** 2026-07-26

**Change date:** 2026-07-26  
**Status:** Complete  
**Primary owner:** Prometheus infrastructure monitoring  
**Plan:** [Move Monitoring off grey-server](../Change%20Plans/Move%20Monitoring%20off%20grey-server.md)

## Scope

I moved Prometheus, Grafana, the Proxmox exporter, `blackbox_exporter`, and the NUT exporter from `security-01` on `grey-server` to CT 104 `monitor-01` on `blue-server`. I kept `node_exporter`, cAdvisor, and Wazuh on `security-01`.

The change added VLAN 73 `MONITOR-A`, custom firewall zone `Org-Monitor`, a dedicated Proxmox API identity, and the firewall paths required by a collector at 192.168.73.2. I also repointed the existing Nginx Proxy Manager hosts for Grafana and Prometheus.

## Starting State

- Prometheus and Grafana ran in a five-container Compose project under `/home/<YOUR_ADMIN_USERNAME>/monitoring` on `security-01`, 192.168.72.2.
- `security-01` shared `grey-server` with several workloads it monitored.
- Prometheus reported 44 of 44 expected targets `up`.
- The live UniFi controller held 52 user-defined policies. The firewall inventory said 43 because it had not counted the nine Kasm policies retained on 2026-07-23.
- `/etc/pve/firewall/cluster.fw` allowed 192.168.72.2 to the Proxmox API, node exporters, and both NUT listeners.
- CTID 104 was free on `blue-server`; the Debian 13 template was cached, and `local-lvm` had about 140 GB free.

## Actions

### 1. Network and firewall foundation

I created `MONITOR-A` as VLAN 73 at 192.168.73.1/24 with DHCP from 192.168.73.6 through 192.168.73.254. CT 104 keeps 192.168.73.2 as a static address in its Proxmox network configuration, outside that pool. I created `Org-Monitor` with only `MONITOR-A`.

UniFi initially excluded the new network from the shared `Proxmox-Trunk` port profile. I added only `MONITOR-A` to that trunk. The guest could then reach its gateway.

The planned firewall scope contained 23 design-level changes: 12 new UniFi policies, seven changes to existing UniFi policies, and four Proxmox firewall member or rule swaps. DNS testing found one additional requirement, `Allow Monitor DNS to Gateway`, so the completed scope was 24:

| Scope | Completed change |
|---|---|
| 12 new UniFi policies | Seven monitoring and NUT paths, web and NTP egress, NPM ingress, Jedi PC break-glass access, and Ansible SSH |
| 1 execution finding | Added `Allow Monitor DNS to Gateway` for port 53 after split-horizon DNS failed without it |
| 6 existing UniFi policies | Deleted the superseded Security-A monitoring and NUT policies sourced from 192.168.72.2 |
| 1 existing UniFi policy | Reduced `Allow NPM to security-01 web UIs` from ports 443, 3000, and 9090 to port 443 for Wazuh |
| 4 Proxmox firewall swaps | Replaced the 192.168.72.2 member of `pve_svc_clients` and its node-exporter plus two NUT rules with matching 192.168.73.2 entries |

The `pve_svc_clients` member mattered as much as the three rules in `[group pve_mgmt]`. It is outside the `[RULES]` section and permits the Proxmox exporter to reach TCP 8006. I verified it during both the additive and removal passes.

I built each `cluster.fw` candidate outside `/etc/pve`, kept all five IPSets, both trailing drops, and both PeaNUT rules, then ran `pve-firewall compile`. The final file has no 192.168.72.2 monitoring entries and four 192.168.73.2 entries.

### 2. Dedicated exporter identity

I created `pve-exporter@pve!monitor01` with privilege separation enabled and `PVEAuditor` on `/`. I stored the one-time token in 1Password as `the Proxmox token entry`. I did not change the existing `local-dash@pve!readonly` token used by the dashboard on `docker-main`.

### 3. CT 104 and exporter rollout

I created unprivileged Debian 13 CT 104 `monitor-01` on `blue-server` with two cores, 2 GiB memory, 1 GiB swap, a 16 GiB `local-lvm` disk, and static address 192.168.73.2/24. I applied the Linux host baseline before deploying the workload: approved administrative keys, key-only SSH, locked root, recovery credentials, current packages, `America/New_York`, and `en_US.UTF-8`.

Docker 29.6.2 and Compose 5.3.1 run inside the LXC. The Ansible monitoring-exporters project now manages eight node-exporter targets and eight cAdvisor targets. It installed `node_exporter` 1.9.0 on port 9100 and cAdvisor 0.60.5 on port 9101.

### 4. Monitoring stack and credentials

I deployed the versioned Compose, Prometheus, blackbox, and Grafana files under `/home/<YOUR_ADMIN_USERNAME>/monitoring`. The untracked `pve.yml` is mode 0600 and owned by `<YOUR_ADMIN_USERNAME>`; `pve-exporter` runs as UID 1000 so it can read that file.

The six running containers are Prometheus 3.13.1, Grafana 13.1.1, `pve-exporter`, `blackbox-exporter` 0.27.0, NUT exporter 1, and cAdvisor 0.60.5. Grafana 13 uses `/usr/share/grafana/bin/grafana cli`, so I used that supported path instead of the removed `grafana-cli` executable. I rotated the saved administrator credential through stdin, renamed the 1Password item to `the Grafana administrator entry`, confirmed the saved login succeeds, and confirmed `admin:admin` fails.

### 5. Cutover and cleanup

The NPM proxy hosts for Grafana and Prometheus now forward to 192.168.73.2 on ports 3000 and 9090. A read-only database query confirmed both saved upstreams.

After the 46-target gate passed, I stopped only the old five-container monitoring Compose project on `security-01`. I then removed the six old UniFi policies, narrowed the retained NPM-to-Wazuh policy to port 443, and installed the final `cluster.fw`.

I deleted `/home/<YOUR_ADMIN_USERNAME>/monitoring`, the `monitoring_prometheus_data` and `monitoring_grafana_data` volumes, and only the five retired monitoring images from `security-01`. I did not prune images. The separate cAdvisor project under `/opt/docker/cadvisor`, `node_exporter`, and all three Wazuh services remained in place.

## Decisions

- I used an unprivileged Debian 13 LXC and Docker Compose because the repository already described the complete stack and Debian did not package the full current set.
- I kept the LXC address static while leaving UniFi DHCP enabled for the rest of `MONITOR-A`.
- I started with a fresh Prometheus TSDB and Grafana database. The old 15-day history and retired Grafana database are not recoverable after the wipe.
- I kept the Prometheus and Grafana image tags floating as the existing configuration specifies. The deployed versions at completion were Prometheus 3.13.1 and Grafana 13.1.1.
- I left Security-A web and NTP egress unchanged because Wazuh on `security-01` and Splunk on `splunk-siem` still need those paths.

## Resulting Configuration

| Item | Result |
|---|---|
| Host | CT 104 `monitor-01` on `blue-server` |
| Network | Static 192.168.73.2/24 on `MONITOR-A`, VLAN 73; gateway and DNS 192.168.73.1 |
| DHCP | Enabled at 192.168.73.6 through 192.168.73.254 |
| Firewall zone | `Org-Monitor`, containing only `MONITOR-A` |
| UniFi user-defined policies | 59: started at 52, added 13, deleted 6 |
| Proxmox API identity | `pve-exporter@pve!monitor01`, `PVEAuditor` on `/` |
| Stack path | `/home/<YOUR_ADMIN_USERNAME>/monitoring` on `monitor-01` |
| Prometheus | 3.13.1, 15-day retention, 46 expected targets |
| Grafana | 13.1.1, one provisioned Homelab Overview dashboard |
| NPM upstreams | Grafana 192.168.73.2:3000; Prometheus 192.168.73.2:9090 |
| Remaining workload on `security-01` | Wazuh, `node_exporter` 1.9.0, and cAdvisor 0.60.5 |

## Verification

| Check | Observed result |
|---|---|
| Starting target set | 44 of 44 `up` |
| Final target set | 46 of 46 `up`; no stale address |
| Prometheus configuration | `promtool check config` passed |
| Dashboard queries | 65 passed; 64 returned data and the allowed restart table was empty |
| Exporter paths | All 15 node-exporter and eight cAdvisor endpoints returned HTTP 200 from `monitor-01` |
| Proxmox and UPS paths | TCP 8006 answered; both TCP 3493 paths opened and returned live UPS metrics |
| NPM routes | Grafana, Prometheus, and Wazuh each returned HTTP 302 through their HTTPS names |
| Proxmox firewall | `pve-firewall compile` passed; all four nodes held SHA256 `d706b11d2ada85c461568033eadfe2e46df3fa80fbea9240dce15e04d2d4d9b3`; TCP 22 and 8006 remained present |
| UniFi final state | 59 user-defined policies, 16 zones, and five groups |
| `security-01` cleanup | Retired directory, volumes, containers, and five images absent; cAdvisor healthy; `node_exporter` active; Wazuh manager, indexer, and dashboard active |

The plan's Phase 8 command expected six `name="..."` matches from cAdvisor after deleting the old five-container project. That expectation was wrong. The endpoint remains HTTP 200, but the only non-empty container name on `security-01` is now `cadvisor`, because the five retired containers no longer exist.

I retained no separate command transcript in the repository. This record carries the observed results, exact final firewall hash, policy counts, and service checks.

## Rollback

After the Phase 8 wipe, rollback means rebuilding rather than restoring local data:

1. Re-create the six Security-A UniFi policies and restore ports 3000 and 9090 on the NPM-to-`security-01` policy.
2. Restore the four 192.168.72.2 entries in `cluster.fw`, build a candidate outside `/etc/pve`, run `pve-firewall compile`, and verify ports 22 and 8006.
3. Deploy [Configuration](../../Configuration/) to `/home/<YOUR_ADMIN_USERNAME>/monitoring` on `security-01`, create a new untracked `pve.yml`, and start the Compose project.
4. Repoint the Grafana and Prometheus NPM hosts to 192.168.72.2.
5. Run `promtool`, the exact target assertion, and the dashboard query assertion before removing `monitor-01`.

The old Prometheus TSDB and Grafana SQLite database were deleted by design and cannot be restored from this project. The pre-change Proxmox firewall backup remains at `/root/cluster.fw.bak.monitor-relocation-2026-07-26` on `blue-server`.

## Remaining Work

The relocation has no open implementation step. Alert routing, the `kasm-01` exporter, UniFi device metrics, and the 24-hour Grafana WAL check remain separate backlog items in the [Prometheus TODO](../TODO.md).
