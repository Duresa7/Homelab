# docker-main Memory at 8 GiB

**Created:** 2026-11-04  
**Last updated:** 2026-11-04

**Change date:** 2026-11-04  
**Target:** CT 110 `docker-main` on `grey-server`

## Outcome

I cut CT 110 `docker-main` from 16 GiB of memory to 8 GiB. Swap stays at 4 GiB and the container keeps 4 vCPUs. The new limit applied live, with no restart, and all 17 containers stayed up.

In an LXC the memory setting is a ceiling, not a reservation, so Grey only ever spent what the container used. The cut stops `docker-main` from growing past 8 GiB and crowding the other guests on Grey.

## Why

Prometheus held 15 days of data for the container's node_exporter and cAdvisor targets when I checked at 3:48 PM.

| Measure over 15 days | Value |
|---|---|
| Memory in use, average | 2.48 GiB |
| Memory in use, 99th percentile | 2.87 GiB |
| Memory in use, peak | 5.31 GiB |
| Swap in use, peak | 2.58 GiB |
| CPU, average | 0.63 cores |
| CPU, 99th percentile | 1.82 cores |
| Memory pressure, `/proc/pressure/memory` | `some` and `full` 0.02 or lower over 10, 60 and 300 seconds |

The largest containers by working set:

| Container | Average | Peak |
|---|---|---|
| `immich_server` | about 550 to 660 MiB | 1,478 MiB |
| `immich_machine_learning` | about 100 to 230 MiB | 2,487 MiB |
| `open-webui` | about 460 to 590 MiB | 701 MiB |
| `immich_postgres` | 189 MiB | 570 MiB |
| `sure-worker` | 291 MiB | 446 MiB |
| `bookorbit-app` | 144 MiB | 387 MiB |
| `ollama` | 75 MiB | 384 MiB |

Every other container averaged under 120 MiB. The 5.31 GiB peak fits inside 8 GiB with room for Immich's machine-learning models and an Ollama load at the same time. Ollama runs its models on the GTX 1080 Ti's 11 GiB of VRAM, and no model was loaded at the time.

Swap held 2.4 GiB while 13 GiB of memory sat free, with no memory pressure. Those are idle pages swapped out earlier, not a sign the container is short of memory, so I left swap at 4 GiB.

I kept 4 vCPUs. `immich_server` reached 2.81 cores during its jobs, and spare cores in an LXC cost Grey almost nothing while idle.

## Change

On `grey-server`:

```text
pct config 110    -> cores: 4, memory: 16384, swap: 4096
pct set 110 --memory 8192
pct config 110    -> cores: 4, memory: 8192, swap: 4096
```

## Verification

| Check | Time | Result |
|---|---|---|
| `pct status 110` | 3:49 PM | `running` |
| `/sys/fs/cgroup/lxc/110/memory.max` on Grey | 3:50 PM | `8589934592`, 8 GiB |
| `/sys/fs/cgroup/lxc/110/memory.swap.max` on Grey | 3:50 PM | `4294967296`, 4 GiB |
| `/sys/fs/cgroup/lxc/110/memory.current` on Grey | 3:50 PM | 2.87 GiB, page cache included |
| `memory.events` on Grey | 3:50 PM | `oom 0`, `oom_kill 0` |
| Guest `free -m` | 3:50 PM | 8,192 MiB total, 1,744 MiB used, 6,447 MiB available |
| Guest `/proc/pressure/memory` | 3:50 PM | 0.00 across every window |
| `docker ps` | 3:50 PM | All 17 containers up; every one with a health check reports healthy |

## Open items

None.
