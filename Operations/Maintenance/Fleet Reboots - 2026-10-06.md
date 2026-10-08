# Fleet Reboots

**Created:** 2026-10-06  
**Last updated:** 2026-10-07

**Implementation date:** 2026-10-06, 12:26 AM to 12:46 AM EDT  
**Status:** Complete for four nodes and their guests plus `security-01` and `splunk-siem`; `grey-server` and `ubuntu-dev` not rebooted

## Scope

This finishes the reboots the [2026-10-05 fleet update](Fleet%20Update%20-%202026-10-05.md#open-state) left pending. I rebooted every machine except `grey-server`, which I excluded on purpose. That covered `green-server`, `red-server`, `purple-server` and `blue-server` with the eight guests they carry, and the two VMs on Grey that were waiting for kernels, `security-01` and `splunk-siem`, which I rebooted as guests without touching their node.

Not rebooted:

- **`grey-server`**, so `docker-main` (CT 110) still runs the node's `7.0.14-8-pve` kernel, and `7.0.14-20-pve` stays installed but not running there.
- **`ubuntu-dev`**, the VM I work from. Rebooting it would end the session before I could verify it. Kernel 7.0.0-38 is still waiting.
- **The Windows guests** on Grey (`HQ-DC01`, `HQ-DC02`, `HQ-MGT01`, `win11-dev`). The fleet update left Windows untouched, so there was nothing to apply. `kali-pen` and `HQ-WS001` stayed stopped.

## Execution

I ran the reboots one at a time, in the order the fleet update record set out, and checked each machine before starting the next. Times are Eastern.

**Nodes.** I drove these over direct SSH from `ubuntu-dev`, because rebooting `blue-server` takes down Executor and the SSH Manager gateway with it. A [helper script](../Evidence/Fleet%20Reboots%20-%202026-10-06/Logs/reboot-node.sh) recorded the boot ID and running guests. It then scheduled `systemctl reboot` through a transient systemd timer three seconds out and waited for a new boot ID. Once the node was back it read the kernel, the six PVE services plus `wazuh-agent`, quorum and failed units, and waited until every guest with `onboot=1` was running again. No guest was migrated: each one shut down with its node and started again when the node came back.

| Node | Reboot scheduled | Back after | Kernel | Guests running again |
|---|---|---|---|---|
| green-server | 12:26:05 AM | 76 s | `7.0.14-20-pve` | No guests |
| red-server | 12:27:47 AM | 91 s | `7.0.14-20-pve` | `media-01` 14 s later |
| purple-server | 12:30:09 AM | 95 s | `7.0.14-20-pve` | `app-01`, `edge-01`, `alpha-prod-01` 14 s later |
| blue-server | 12:33:34 AM | 102 s | `7.0.14-20-pve` | `ansible-01`, `monitor-01`, `docker-network`, `docker-blue` 6 s later |

Every node came back quorate at five votes. The only exception was a read on `purple-server` taken the moment corosync started, which showed one vote; a re-read seconds later showed five. `pveproxy` was still `activating` on the first read on `red-server` and `purple-server` and `active` on the next.

**VMs on Grey.** `ansible-01` ran `os-update.yml` with `-e reboot=auto` for `security-01` and then `splunk-siem`, as a transient unit so the run did not depend on my session. That path proves the boot ID changed and then waits up to five minutes for `systemctl is-system-running` to report `running`.

| VM | Booted | Kernel | Play result |
|---|---|---|---|
| security-01 | 12:37:29 AM | `6.8.0-146-generic` | Exit 2 at 12:42:52 AM: new boot ID confirmed, but the system stayed `degraded`, see below |
| splunk-siem | 12:43:59 AM | `6.12.0-211.61.1.el10_2.x86_64` | Exit 0 at 12:46:26 AM; `running` after 13 of the 30 checks |

`security-01`'s exit 2 does not mean the reboot failed. Its boot ID changed and it booted the new kernel, but its `prometheus-node-exporter.service` has been failed since before the [2026-10-02 package run](Guest%20Package%20Updates%20-%202026-10-02.md), so systemd reports `degraded` and never `running`. The settle step therefore used all 30 checks and failed the play. I checked the host directly afterwards; the results are below.

## Verification

**Correction recorded 2026-10-07:** docker-main had an upstream exporter restart loop during these checks. The old packaged exporter kept its Prometheus target up, and the restarting unit did not appear in `systemctl --failed`. I confirmed the loop on October 7 and [repaired it with the other confirmed service failures](Service%20Failure%20Repairs%20-%202026-10-07.md). The historical target and container counts below do not establish that every service was healthy.

Each guest was checked once its node was back, then the whole fleet again at the end.

- **media-01:** Jellyfin, Seerr, Sonarr, Radarr, Prowlarr and qBittorrent answered 200; qBittorrent was still in Gluetun's network namespace, and Gluetun reached the internet through the VPN.
- **edge-01:** Caddy and cloudflared active. cloudflared registered four tunnel connections this boot, and the `edge-uptime` textfile reports four connections with the Caddy and Coolify origins up. The public `coolify-a1.alphsec.com` answers 403 with `cf-mitigated: challenge`, which is Cloudflare's managed challenge for a non-browser client. A down tunnel would return 530.
- **app-01:** every Coolify container came back healthy, Sentinel included.
- **alpha-prod-01:** no unhealthy containers, and the playit agent reconnected.
- **docker-blue:** seven containers healthy 16 seconds after the LXCs started, all ten running, including Executor, both Docker MCP Gateway instances, SSH Manager and the UniFi MCP. My first Executor call after the restart returned a session-expired error, and the retry worked.
- **ansible-01:** `semaphore`, `galaxy-pxe`, `tftpd-hpa` and `wazuh-agent` active; Semaphore's `/api/ping` returned 200.
- **monitor-01:** Prometheus had 46 of 50 targets up one minute after boot, before the blackbox probes had run, and 50 of 50 shortly after. Grafana's health check passed, PeaNUT answered on `192.168.73.2:8090`, and the alert bot was healthy.
- **docker-network:** NPM and NetBird answered.
- **security-01:** `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard`, `filebeat` and Docker active. The dashboard answered 302, and the API and indexer answered 401, which means they were up and asking for credentials. `wazuh-mcp-server`, cAdvisor and Hawser healthy.
- **splunk-siem:** `running` with no failed units; `Splunkd`, `sc4s` and `unifi-flow-collector` running; Splunk Web 303 on 8000, management 200 on 8089, and SC4S listening on UDP 514.

The final fleet readback, between 1:02 AM and 1:10 AM:

- All five nodes on `pve-manager/9.2.21`, quorate at five votes. Green, red, purple and blue run `7.0.14-20-pve`; grey still runs `7.0.14-8-pve`. [Node state](../Evidence/Fleet%20Reboots%20-%202026-10-06/Exports/node-final-state.txt).
- No guest carries a reboot flag. `alpha-prod-01`, `app-01` and `edge-01` run `6.12.111+deb13-amd64`, and the blue and red LXCs run `7.0.14-20-pve`. [Guest state](../Evidence/Fleet%20Reboots%20-%202026-10-06/Exports/guest-final-state.txt).
- 69 containers running across the eight Docker hosts, the same count as after the fleet update, with none unhealthy, starting or restarting. The only exited containers are `docusaurus` on `docker-main`, already stopped, and the six Hawser updater helpers.
- Prometheus: 50 of 50 targets up and no alerts firing.
- Wazuh: 15 remote agents Active on the manager.
- The only new failed unit is `nut-server` on `red-server`, described below.

## What the reboots surfaced

None of these came from the updates, and I changed none of them.

- **`red-server`: `nut-server` failed, and `nut-monitor` with it.** On 2026-08-31 I commented out the `[ups01]` stanza and disabled `nut-server` and `nut-driver@ups01` ([troubleshooting record](../../Platforms/PeaNUT/Documentation/Troubleshooting/ups01%20NUT%20Driver%20Restart%20Loop%20After%20the%20UPS%20Swap%20-%202026-08-31.md)); `nut-monitor` had been disabled since the dashboard deployment. `nut.target` and `nut-driver.target` stayed enabled. `nut.target` is wanted by `multi-user.target` and wants both units itself, so tonight's boot, the first since that change, started them with no UPS defined. Both hit the restart limit and stopped as failed. `nut-monitor` was already failed before the August change; `nut-server` had been stopped cleanly and is the new failure. Nothing about UPS-01 changed: it still has no data path. Disabling the two targets would make the next boot match the documented state; reconnecting the cable and restoring the stanza would bring UPS-01 back.
- **`security-01`: `prometheus-node-exporter.service` failed.** Two exporters are installed. The upstream binary at `/usr/local/bin/node_exporter` 1.9.0, run by `node_exporter.service`, binds TCP 9100 and is the one Prometheus scrapes. Ubuntu's `prometheus-node-exporter` 1.7.0 package, installed on 2026-09-02 with `prometheus-node-exporter-collectors`, starts its own unit and fails with `bind: address already in use`. Metrics are not affected. The failed unit is what keeps the host `degraded` and makes `reboot=auto` report a failure on a good reboot. Disabling or masking the package's unit would clear both.
- **`grey-server`, not rebooted: `zfs-import@hddpool.service` failed** since 2026-09-04. The pool is named `hddpool-1` and is `ONLINE`; both `zfs-import@hddpool` and `zfs-import@hddpool-1` are enabled, and the first names a pool that does not exist, so it will fail again at Grey's next boot. `nut-monitor` there has been failed since 2026-08-01 and is disabled.
- The six `openipmi.service` failures on `alpha-prod-01`, `ansible-01`, `docker-blue`, `docker-network`, `media-01` and `monitor-01` came back as before.

## Evidence

Under [Fleet Reboots - 2026-10-06](../Evidence/Fleet%20Reboots%20-%202026-10-06/): the node helper and its output for all four nodes, the `os-update.yml` log for the two VMs, and the final node and guest readbacks. I removed the run directory from `ansible-01`, and no `fleet-*` transient units are left there. No snapshots were taken.

## Open state

- Reboot `grey-server`. Its guests restart with it: `docker-main`, `ubuntu-dev`, `security-01`, `splunk-siem`, the three Windows servers and `win11-dev`. That reboot also applies `ubuntu-dev`'s 7.0.0-38 kernel, and it has to be started from somewhere other than `ubuntu-dev`.
- The `red-server` NUT activation, duplicate exporters on `security-01` and `docker-main`, obsolete Grey import and six OpenIPMI failures were [repaired on 2026-10-07](Service%20Failure%20Repairs%20-%202026-10-07.md). Automatic UPS shutdown remains unconfigured.
- The four held upgrades from the fleet update are unchanged.
