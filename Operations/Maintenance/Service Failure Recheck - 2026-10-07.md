# Service Failure Recheck

**Created:** 2026-10-07  
**Last updated:** 2026-10-07

**Verification:** 2026-10-07, approximately 9:13 PM to 9:15 PM EDT  
**Status:** Reported failures still present at this read-only check; no fixes applied

**Follow-up:** I [repaired and verified these failures](Service%20Failure%20Repairs%20-%202026-10-07.md) later the same evening.

I rechecked the failures reported after the [fleet reboots](Fleet%20Reboots%20-%202026-10-06.md) through SSH Manager. I read service states, restart counters, targeted journals, port ownership, exporter metrics, the Prometheus API, USB presence and ZFS pool state. I made no remote configuration changes, package updates, restarts or reboots.

| Host | Observed state | Impact |
|---|---|---|
| docker-main | `node_exporter.service` remained `activating/auto-restart`, with `NRestarts` rising from 549589 at 9:13:19 PM to 549595 at 9:13:53 PM. Fresh logs report `listen tcp :9100: bind: address already in use`. Both exporter units are enabled. | The packaged exporter 1.5.0 owns port 9100 and supplies metrics; the intended exporter keeps failing every approximately five seconds. `systemctl --failed` was empty despite the loop. |
| security-01 | `node_exporter.service` is running with zero restarts and serves version 1.9.0. Packaged `prometheus-node-exporter.service` is failed after five restarts. Both units remain enabled. | Metrics work, but the duplicate service installation and boot-order risk remain. Wazuh manager, indexer, dashboard and Filebeat are active. |
| red-server | `nut-server` and `nut-monitor` are failed with five restarts each. Both are disabled, but enabled `nut.target` still wants them. `nut-driver@ups01` is inactive and disabled. No APC USB device appeared in `lsusb -d 051d:`. | UPS-01 monitoring remains unavailable. Neither failed service was continuously restarting at inspection. |
| grey-server | `zfs-import@hddpool.service` is enabled and failed with `cannot import 'hddpool': no such pool available`. `nut-monitor` is failed after five restarts and disabled. | The stale import task remains. The real `hddpool-1` pool is ONLINE and mounted, CT 110 is running, and the UPS-02 server returns `OL`. Automatic shutdown monitoring is not running on Grey. |
| alpha-prod-01, ansible-01, docker-blue, docker-network, media-01, monitor-01 | Each has failed `openipmi.service`; none has `/dev/ipmi0`, `/dev/ipmi/0` or `/dev/ipmidev/0`. | The six hardware-driver failures remain and leave failed units in systemd. |

Prometheus reported 50 of 50 targets up. Its stored build metrics independently confirmed version 1.5.0 for docker-main and 1.9.0 for security-01. Target availability therefore does not detect the duplicate exporter problem.

The real pool's enabled, successful unit is `zfs-import@hddpool\x2d1.service`, with the hyphen escaped in the instance name. My first probe used the unescaped `zfs-import@hddpool-1.service`, which reported inactive/disabled; I resolved the actual name from `zfs-import.target` and verified it as active/exited with `Result=success`. Any future cleanup must distinguish that working unit from the obsolete `zfs-import@hddpool.service`.

I did not recalculate the earlier Wazuh alert-volume or journal-retention estimates in this recheck. The restart loop is directly confirmed by two counter samples and fresh errors. I did not re-audit package currency or application functionality across the whole fleet.

My first security-01 call tried passwordless sudo for service reads and received `sudo: a password is required`. I repeated those reads without sudo successfully. The first Prometheus version query matched hostnames against the `instance` label and returned no series; the corrected query used the actual labels and returned both versions. Neither initial result was treated as a clean bill of health.

I retained the exact commands, returned stdout/stderr and exit codes, including those probe corrections, in the [verification capture](../Evidence/Service%20Failure%20Recheck%20-%202026-10-07/Logs/checks.json). The capture records UTC timestamps as returned by the hosts; the verification times above are Eastern. All reported failures remain open. No corrective action was authorized or performed.

