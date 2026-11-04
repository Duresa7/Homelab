# security-01 Memory Reduction

**Created:** 2026-11-04  
**Last updated:** 2026-11-04

**Change date:** 2026-11-04  
**Target:** VM 200 `security-01` on `grey-server`

## Outcome

I reduced VM 200 `security-01` from 10 GiB of memory with an 8 GiB balloon floor to a fixed 8 GiB. Grey commits 2 GiB less to the guest. Wazuh 4.14.8, the Splunk Universal Forwarder and the three Docker containers came back after one clean power cycle, and 14 remote agents reconnected.

## Why

I first looked at moving `security-01` or `splunk-siem` to `red-server`, and decided against both:

| Check at 12:36 PM | Result |
|---|---|
| `red-server` memory | 9.3 of 15.5 GiB in use, 6.1 GiB available; neither guest's 8 GiB minimum fits |
| `red-server` `local-lvm` | 46.52% used, about 75 GiB free, already holding about 180 GiB of thin volumes; too small for a 100 or 150 GiB disk |
| `red-server` CPU | i5-8500T, 6 cores and 6 threads, against Grey's Ryzen 7 3700X at 8 cores and 16 threads |
| `grey-server` | 21.1% CPU, 39.4 of 62.7 GiB in use |

`splunk-siem` stays at 8 GiB. That is Splunk's recommended minimum, and the guest had 832 MiB in swap with a load average of 4.36. `security-01` used far less than it was given, so I cut that one instead.

## Checks before the change

| Check | Result |
|---|---|
| `qm config 200` | `memory: 10240`, `balloon: 8192`, `numa: 0`, no `hotplug` line, so memory is not hot-pluggable and the new size needs a cold start |
| Pending configuration | None |
| Guest memory, `free -m` | 3,262 MiB used, 4,652 MiB cache, 6,615 MiB available; 315 MiB of swap in use |
| Memory pressure, `/proc/pressure/memory` | `some` and `full` both 0.00 over 10, 60 and 300 seconds |
| Indexer heap, `/etc/wazuh-indexer/jvm.options` | `-Xms1024m` and `-Xmx1024m` |
| Largest processes by RSS | indexer `java` 1,562 MiB, `wazuh-modulesd` 371 MiB, dashboard `node` 163 MiB, `wazuh-analysisd` 128 MiB |
| Proxmox memory RRD, month, MAX | 9.44 GiB peak, guest page cache included |
| Wazuh services | `wazuh-manager`, `wazuh-indexer` and `wazuh-dashboard` active |

The 1 GiB heap and about 3.3 GiB of real use leave the indexer more than half of 8 GiB for its file cache.

## Change

On `grey-server`:

```text
qm set 200 --memory 8192 --delete balloon
update VM 200: -delete balloon -memory 8192
memory: 8192

qm shutdown 200 --timeout 180    -> stopped
qm start 200                     -> status: running
```

The guest journal logged a clean poweroff at 1:01:25 PM. Proxmox started the VM at 1:01:32 PM, and the new boot began at 1:01:39 PM. There was one boot. Wazuh was down for about a minute plus its service start time. Agents buffer events while the manager is unreachable.

Removing the `balloon` key leaves ballooning at its default, with the floor equal to the 8 GiB maximum, so the host can no longer reclaim memory from the guest.

## Verification

| Check | Time | Result |
|---|---|---|
| `qm config 200` | 1:53 PM | `memory: 8192`, no `balloon` line, `cores: 4` |
| Guest `free -m` | 1:02 PM | 7,873 MiB total, 2,723 MiB used, 5,150 MiB available, swap 0 |
| Guest `free -m` | 1:53 PM | 2,986 MiB used, 4,887 MiB available, swap 0 |
| Wazuh services and Docker | 1:02 PM | `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard` and `docker` active |
| Containers | 1:02 PM | `hawser`, `cadvisor` and `wazuh-mcp-server` up and healthy |
| Dashboard, `https://127.0.0.1/` | 1:02 PM, 1:53 PM | HTTP 503 while starting, then HTTP 302 to the login page |
| `agent_control -l` | 1:53 PM | Manager plus 14 remote agents active; `004` `app-01` disconnected, as expected because the VM has been stopped since 2026-10-09 |
| Splunk forwarder | 1:53 PM | `SplunkForwarder` active |
| `/var/ossec/logs/alerts/alerts.json` | 1:53 PM | Newest alert stamped 18:52:38 UTC, so the manager is writing alerts again |

Grey read 48.8 of 62.72 GiB in use at 1:53 PM. That figure is not comparable with the 39.4 GiB reading before the change, because an ephemeral CI runner, VM 834, started on Grey at 1:01:42 PM.

## Open items

None.
