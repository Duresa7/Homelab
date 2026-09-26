# Manager Processes Terminated by Hash Refresh

**Created:** 2026-09-11  
**Last updated:** 2026-09-25

## Incident Metadata

| Field | Value |
|---|---|
| Occurred | 2026-09-06 about 4:58 AM EDT |
| Recovered | 2026-09-11 about 2:44 AM EDT |
| Status | Closed 2026-09-11. Manager recovered, refresh corrected, and all 16 remote agents active |
| Severity | Not assigned |
| Impact type | Loss of agent event collection |
| Affected system | `security-01`, `192.168.72.2`, and its enrolled agents |

## Summary

The weekly Wazuh hash-list refresh on `security-01` restarted the manager from inside its own oneshot service on September 6. Systemd killed the new manager processes when that service ended, while `wazuh-manager.service` still reported active. Agents could not reach TCP 1514 or 1515 until September 11, when I changed the refresh to restart the manager through systemd and verified the fleet.

## Impact

The manager could not collect agent events from September 6 at about 4:58 AM Eastern through September 11 at about 2:44 AM Eastern. I have not measured lost events or established whether buffered events cover any part of that interval.

## Affected Assets

- `security-01`, `192.168.72.2`: `wazuh-manager.service` and `wazuh-hash-list.service`.
- The 16 remote agents enrolled to it.

## Symptoms

I found app-01's Wazuh connection pending during its disk replacement checks, with matching errors before that work began. During the subsequent Purple migration I reproduced TCP 1514 and 1515 timeouts from edge-01. On security-01, `systemctl is-active wazuh-manager` returned active, but neither port listened and no Wazuh manager processes were running.

## Timeline

All times are Eastern, from systemd.

| Time | Event |
|---|---|
| September 6, 4:57:47 AM | `wazuh-hash-list.service` starts and rebuilds 730 entries |
| September 6, 4:58:04 AM | The Wazuh log reports a successful restart, followed at once by SIGTERM and shutdown messages |
| September 6, 4:58:09 AM | The refresh unit finishes; no manager process remains |
| September 11, 2:44:25 AM | The corrected refresh finishes with `Result=success`; the manager stays up |
| September 11, 2:45 AM | 14 remote agents active, blue-server pending, app-01 shut down for migration |
| September 11, about 3:29 AM | All 16 remote agents active |

## Findings

Those processes were launched as children of the oneshot refresh service. Systemd terminated them when that service ended. Meanwhile, `wazuh-manager.service` uses `Type=forking` and `RemainAfterExit=yes`; its active state and September 2 start timestamp remained, despite its processes being gone. Disk and memory exhaustion were not indicated: root had 68 GiB available, memory had about 5 GiB available, and the inspected kernel journal showed no OOM kill. Wazuh's own log mixes local and UTC timestamps; the incident timeline above uses systemd's Eastern timestamps.

I summarized the original diagnostic commands and logs here without retaining a full raw diagnostic transcript. An early `agent_control -l` attempt waited on the absent database socket and caused the SSH call to time out; later calls used `timeout 5`. Passwordless sudo was unavailable, so I used Grey's QEMU guest-agent path for root diagnostics.

## Root Cause

The weekly `wazuh-hash-list.service` ran at 4:57:47 AM Eastern on September 6. Its script rebuilt 730 entries and called `/var/ossec/bin/wazuh-control restart` directly. The log reported a successful restart at 4:58:04 AM, immediately followed by SIGTERM and shutdown messages from the new manager processes. The refresh unit finished at 4:58:09 AM.

## Corrective Action

I changed the [refresh script](../../../Platforms/Wazuh/Scripts/wazuh-refresh-hash-list) to call `systemctl restart wazuh-manager.service`, then require `systemctl is-active --quiet` before reporting success. I checked the shell syntax, deployed the exact change, and restarted the manager through systemd. The local and deployed SHA-256 hashes match: `ebdbb3f02798a329c247bf29bad152bfda396696f6ce0e8a1962094afb47c859`.

## Validation

I then ran the actual `wazuh-hash-list.service` as the regression check. It finished at 2:44:25 AM Eastern with `Result=success` and `ExecMainStatus=0`. After the refresh unit became inactive, the manager remained active, both agent ports listened, and `/proc/<remoted-pid>/cgroup` placed the process in `/system.slice/wazuh-manager.service`. Fresh TCP probes from edge-01 passed for both ports, replacing the earlier timeouts. I changed no firewall rule and re-enrolled no agent.

At 2:45 AM Eastern, 14 remote agents were active, blue-server was pending, and app-01 was disconnected while shut down for its planned migration. At about 3:29 AM Eastern, after both VMs booted on Purple, `agent_control -l` showed all 16 remote agents active, with no pending or disconnected agents. Both migrated guests independently reported `connected`. I summarized this final readback without a separate raw transcript. The repair and regression captures hold commands, output, and exit codes. I created no snapshot or backup.

## Closure

Closed on 2026-09-11 after the fleet readback. Fleet verification is complete. A process/listener or manager-API health check is needed to catch this class of outage; systemd's active state alone did not do so. Existing missing `malicious-ioc` list warnings appeared during startup and are outside this repair.
