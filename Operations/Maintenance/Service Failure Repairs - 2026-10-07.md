# Service Failure Repairs

**Created:** 2026-10-07  
**Last updated:** 2026-10-07

**Implementation:** 2026-10-07, 9:17 PM to 9:22 PM EDT  
**Final verification:** 2026-10-07, 9:25 PM EDT  
**Status:** Confirmed service conflicts repaired on ten hosts

I repaired the failures confirmed in the [read-only recheck](Service%20Failure%20Recheck%20-%202026-10-07.md). I used SSH Manager for the service changes and deployed the corrected collector playbook to `ansible-01`. I rebooted no host, changed no storage pool and created no snapshot or backup.

| Repair | Result | Owning record |
|---|---|---|
| Mask the packaged exporter on docker-main and security-01; restore the upstream exporter on docker-main | Both serve 1.9.0 with `node_textfile_scrape_error 0`; duplicate services are inactive and masked | [Duplicate exporters](../../Platforms/Prometheus/Documentation/Troubleshooting/Duplicate%20Exporters%20Contended%20for%20Port%209100%20-%202026-10-07.md) |
| Disable Red's unused NUT targets and enumerator; mask Red's server and monitor and Grey's unused monitor | All are inactive; Grey's working NUT server still returns `OL` for UPS-02 | [Unused NUT services](../../Platforms/PeaNUT/Documentation/Troubleshooting/Unused%20NUT%20Services%20Started%20at%20Boot%20-%202026-10-07.md) |
| Disable Grey's obsolete `zfs-import@hddpool.service` | Real `hddpool-1` remains ONLINE with its import unit active and enabled; CT 110 stays running | [Stale pool import](../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/Obsolete%20Pool%20Import%20on%20grey-server%20-%202026-10-07.md) |
| Disable and mask OpenIPMI on six guests without IPMI devices | All six report `running` with no failed units | [OpenIPMI on guests](../../Platforms/Ansible/Documentation/Troubleshooting/OpenIPMI%20Failed%20on%20Guests%20Without%20IPMI%20Devices%20-%202026-10-07.md) |

The collector playbook now suppresses package-install service startup, masks the distro exporter when installed, ensures the upstream service runs, and checks its restart counter over ten seconds. The deployed play completed on docker-main and security-01 with `ok=18 changed=0 unreachable=0 failed=0` each. Its deployed SHA-256 is `706ecebe77f3bd6ed6f8b53b9b8da933f5aa442575d8d32994aa2e08555e8c00`.

At 9:25 PM, all ten affected hosts returned `running` and an empty failed-unit list. Docker-main's counter remained 549642 from its first successful start through the final readback, and security-01's remained zero. The 9:22 PM journal check counted zero new bind or service-failure errors since 9:19 PM. Wazuh's retained alert check found zero docker-main node_exporter alerts from 9:19 PM through 9:22 PM, while 112 other alerts arrived. That is a short observation window, not a claim about long-term alert rates.

Prometheus reported 50 of 50 targets up and zero firing alerts at 9:25 PM. Grafana 13.2.3 returned database `ok`. I did not repeat the full application or package-currency audit during these service repairs.

## Evidence and failed attempts

I retained the exact commands and returned output in [execution.json](../Evidence/Service%20Failure%20Repairs%20-%202026-10-07/Logs/execution.json), including the initial docker-main command that stopped after `Failed to reset failed state of unit prometheus-node-exporter.service: Unit prometheus-node-exporter.service not loaded.` The mask had succeeded; I immediately started the intended exporter in a separate call. Its first curl attempt preceded socket readiness, then the configured retry succeeded. Security-01 needed a separate `reset-failed` after masking its duplicate.

The [final host readback](../Evidence/Service%20Failure%20Repairs%20-%202026-10-07/Logs/final-verification.json), [monitoring readback](../Evidence/Service%20Failure%20Repairs%20-%202026-10-07/Logs/monitoring-verification.json), [alert check](../Evidence/Service%20Failure%20Repairs%20-%202026-10-07/Logs/alert-verification.json) and [temporary-file cleanup](../Evidence/Service%20Failure%20Repairs%20-%202026-10-07/Logs/cleanup.json) record the remaining checks. Earlier captures retain host-returned UTC timestamps; the times in this record are Eastern. I removed the play log and exit-status file from `ansible-01` after retaining their contents.

Both local Ansible validators passed: 11 OS-update hosts and 23 Compose projects on six hosts for fleet-updates, and nine node_exporter hosts plus eight cAdvisor hosts for monitoring-exporters. The playbook hash above matches the repository copy. Red's live `ups.conf` and its repository reference both hash to `166e4b5e45c90646426d5046f046300d5cfe95ca7d9b6c963ab8afade9507c79`. New local documentation links and JSON captures passed validation.

## Remaining work

UPS-01 remains deliberately unmonitored. Automatic UPS shutdown is still unconfigured; masking the unused monitors did not provide it. The [held application upgrades](Fleet%20Update%20-%202026-10-05.md#decisions-i-made-and-what-i-held-back), Windows update verification and the [reboots pending after the separate October 7 package run](OS%20Package%20Updates%20-%202026-10-07.md#open-state) remain outside these repairs. Grey was not rebooted.

The October 5 update and October 6 reboot checks missed docker-main's restart loop because an `activating/auto-restart` unit need not appear in `systemctl --failed`. Their healthy target counts remain valid, but did not establish exporter health. I added corrections to both records.
