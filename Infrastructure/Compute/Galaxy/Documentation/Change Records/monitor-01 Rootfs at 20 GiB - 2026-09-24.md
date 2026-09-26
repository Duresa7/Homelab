# monitor-01 Rootfs at 20 GiB

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Observed on:** 2026-09-24  
**Status:** Recorded after the fact; the resize has no earlier record  
**Affected systems:** CT 104 `monitor-01` on `blue-server`

## What changed

CT 104's root volume is 20G. Every record before this one gave it 16G, the size I built it with on 2026-07-26. [Monitoring Relocation to monitor-01](../../../../../Platforms/Prometheus/Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).

On 2026-09-24 `pvesh get /nodes/blue-server/lxc/104/config` returned `rootfs: local-lvm:vm-104-disk-0,size=20G`, with memory 2048 MiB, swap 1024 MiB and 2 cores. The cluster resource list reported `maxdisk` 20,957,491,200 bytes, which is 19.52 GiB of filesystem. The [2026-09-06 staleness audit](../../../../../Operations/Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md) read every LXC configuration and corrected only `docker-blue`, so the resize happened after 2026-09-06. I have no record of the exact day.

The relocation plan sized the disk at 16G and named `pct resize` as the growth path if it ever needed more. [Move Monitoring off grey-server](../../../../../Platforms/Prometheus/Documentation/Change%20Plans/Move%20Monitoring%20off%20grey-server.md). The 4G of growth fits that path, but I have no capture of the command.

## Current state

- Rootfs `local-lvm:vm-104-disk-0`, 20G, on Blue's NVMe-backed thin pool.
- Blue's `local-lvm` held 55.0 of 141.2 GiB (39.0%) on 2026-09-24.
- `monitor-01` ran 10 containers, and Prometheus reported 57 of 57 targets up.

## Verification

The [LXC inventory](../../../../../Operations/Inventory/Galaxy/LXCs.md) now reads 20G. Blue's task log (`/var/log/pve/tasks/`) would show the `resize` task and date it; I did not read it.
