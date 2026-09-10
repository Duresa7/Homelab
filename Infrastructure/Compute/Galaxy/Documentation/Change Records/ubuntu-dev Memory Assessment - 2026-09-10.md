# ubuntu-dev Memory Assessment

**Created:** 2026-09-10  
**Last updated:** 2026-09-10

I checked VM 105 `ubuntu-dev` on `grey-server` at about 7:02 PM Eastern on 2026-09-10 to decide whether to reduce its RAM. My initial recommendation was to keep 16 GiB. I subsequently chose a pending reduction to 12 GiB without restarting anything, as recorded below.

## Live measurements

I verified `memory: 16384` and `balloon: 0` through SSH Manager on `grey_server`. Ubuntu reported 15.047 GiB usable RAM, 7.210 GiB used by the `MemTotal - MemAvailable` estimate, and 7.837 GiB available. Buffers and cache occupied 8.412 GiB; this overlaps the available estimate and must not be added to it. Proxmox reported 13.949 GiB for both `mem` and `memhost`, a host-side footprint that includes guest caching rather than a measurement of application demand.

Ubuntu had 320 KiB in its 4 GiB swap area, zero current memory-pressure averages, and no swap traffic during the four one-second `vmstat` intervals. The process snapshot included Chrome, ChatGPT, Claude Desktop, GNOME Shell, and several development processes. I did not sum their RSS values because shared pages would be counted repeatedly.

## Retained history

I queried Prometheus on `monitor_01` through SSH Manager, using its local API at `http://127.0.0.1:9090`. I joined original samples by timestamp for `node_memory_MemTotal_bytes` and `node_memory_MemAvailable_bytes`, filtered by `host="ubuntu-dev",job="node"`. The 15-day window contained 86,205 paired samples, roughly 99.8% of the expected 15-second samples, from 2026-08-26 at 7:02:47 PM through 2026-09-10 at 7:02:34 PM Eastern.

| Window | Average used | 95th percentile used | Highest sampled usage |
|---|---:|---:|---:|
| 24 hours | 5.82 GiB | 6.89 GiB | 7.42 GiB |
| 7 days | 5.28 GiB | 6.62 GiB | 10.37 GiB |
| 15 days | 5.44 GiB | 6.80 GiB | 10.37 GiB |

The 15-day 99th percentile was 7.32 GiB. The peak occurred on 2026-09-07 at 10:54:34 AM Eastern. At that same sample, swap held 4.00 GiB, giving a combined RAM-use estimate plus swap occupancy of 14.37 GiB. That sum is a conservative sizing indicator, not proof that all those pages needed to be resident at once: swap can retain cold pages, and some swapped pages can also remain cached in RAM.

Swap was near its 4 GiB capacity during several earlier days. The 15-day counters showed swap traffic and brief memory stalls, but zero increase in the kernel OOM-kill counter. The largest five-minute memory-pressure averages sampled at one-minute steps were 15.52% for some tasks waiting and 14.19% for all non-idle tasks stalled. I did not establish the workload or cause of those earlier stalls. The most recent two days had zero recorded swap-ins, about 157 pages swapped out, and about 2.68 seconds of some-task memory waiting.

The host also has a reason to conserve RAM: `grey-server` currently had 10.68 GiB available but almost all of its 8 GiB swap occupied. Its last-day peak RAM-use estimate was 60.54 GiB out of 62.72 GiB usable. Host swap occupancy alone does not establish current thrashing, and this assessment does not attribute it to Ubuntu.

I retained the measured results in this record; I did not retain raw terminal transcripts or the full time series in the repository. The live configuration and guest readings independently verified the allocation and current state against the historical metrics.

## Sizing decision

I would keep 16 GiB for the current development workload. A 12 GiB allocation would save 4 GiB of configured capacity and likely accommodate ordinary sessions, but the observed 10.37 GiB RAM peak leaves little room after guest reservations, with another 4 GiB already swapped at that time. I would treat 12 GiB as a monitored trial only if recovering host capacity takes priority. I would not reduce this workload to 8 GiB.

The samples cannot establish a guaranteed minimum: they can miss short peaks, future builds can differ, and the observed usable-memory reservation need not remain identical after a resize. Any future reduction should be checked across representative development sessions for available RAM, sustained swap traffic, memory pressure, and responsiveness. No resize or restart was performed during the initial assessment; the subsequent pending change is recorded below.

I used the Linux kernel's definition of [MemAvailable](https://www.kernel.org/doc/html/latest/filesystems/proc.html): an estimate of memory available for new applications without swapping, accounting for reclaimable memory and required reserves.

## Pending reduction applied

At 7:07 PM Eastern on 2026-09-10 I chose 12 GiB and applied `qm set 105 --memory 12288` through SSH Manager on `grey_server`. The command returned exit code 0, stdout `update VM 105: -memory 12288`, and empty stderr. I verified the target name, 16,384 MiB starting allocation, disabled ballooning, and absence of memory hotplug before applying the change.

The subsequent Proxmox pending-state API returned `memory` with `value: 16384` and `pending: 12288`; `balloon` remained 0. The VM remained running under PID 582461, uptime advanced from 209,104 to 209,106 seconds, and runtime `maxmem` remained 17,179,869,184 bytes. At 7:07:28 PM, SSH to Ubuntu succeeded and `free -b` still reported 16,156,520,448 bytes usable RAM, confirming the running guest retained its existing memory.

I did not restart the VM, the host, or any service. The 4 GiB reduction is pending a future full VM stop/start; it has not yet recovered host capacity. After that future activation, I need to verify guest memory and observe representative development sessions at 12 GiB. I recorded these results here without retaining a separate raw transcript.
