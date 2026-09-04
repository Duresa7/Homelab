# Root Filesystem Filled by Retained Docker Images

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

**Issue date:** 2026-09-04  
**Affected system:** CT 104 `monitor-01`  
**Status:** Resolved

## Symptom

Grafana delivered `Filesystem is almost full` for `monitor-01`, reporting the root filesystem at 94.8 percent for 15 minutes. My pre-correction readback found `/dev/mapper/pve-vm--104--disk--0` at 96 percent with 720 MiB available. The inode count was only 14 percent, so this was block consumption rather than inode exhaustion.

## What I checked

The first top-level `du` scan saw only 1.3 GiB because Docker 29 keeps image content in containerd and exposes running root filesystems through overlay mounts. A privileged scan and Docker's own accounting found 7.5 GiB under `/var/lib/containerd` and a 5.2 GiB Prometheus volume. Journald used 12.9 MiB, container writable layers totaled 114.7 KiB, and no deleted open file held meaningful space.

Prometheus retained data from August 20 through September 4 and followed its normal compaction cycle. Its historical filesystem series showed the abrupt event instead: at 2:02 AM EDT, root usage jumped from 82.5 to 93.9 percent. Grafana and the alert bot had been recreated at 2:00 AM during the [Compose Fleet Refresh](../../../../Operations/Maintenance/Compose%20Fleet%20Refresh%20-%202026-09-04.md).

`docker system df` reported 7.913 GB of images, 4.382 GB reclaimable. The four dangling generations were two Grafana images at 1.91 GB and 1.58 GB, one Prometheus image at 359 MB, and one Proxmox exporter image at 201 MB.

## Root cause

The 16 GiB root filesystem held both Prometheus's expected 15-day data set and Docker's containerd image store. Repeated Compose pulls and recreations retained superseded image generations. The September 4 refresh pulled Grafana 13.2.1 and rebuilt the alert bot without pruning the now-dangling images, which pushed the filesystem across the alert threshold. Prometheus data, journals, container logs, and deleted files did not cause the sudden increase.

## Correction

I ran `docker image prune -f`, the dangling-only cleanup established by the [fleet artifact sweep](../../../../Operations/Maintenance/Fleet%20Artifact%20Sweep%20-%202026-07-29.md). Docker removed all four untagged image generations and reported 4.021 GB reclaimed. I did not use `-a`, remove any volume, or alter Prometheus data.

## Verification

The same threshold check that failed at 96 percent passed at 70 percent. The root filesystem had 4.5 GiB available, and `docker image ls --filter dangling=true -q` returned no image ID.

All nine containers remained running with restart count zero. Prometheus returned ready with 56 targets up. Grafana 13.2.1 reported database status `ok`, and every container with a health check remained healthy. A follow-up host health check reported 12.5 percent CPU, 34.86 percent memory, and 70 percent root usage with no critical issue.

No standalone evidence folder was retained. The values above are direct before-and-after readbacks from `monitor-01` on 2026-09-04.

## What remains open

The remaining 361.1 MB reported as reclaimable belongs to an unused tagged image and requires broader `-a` pruning, so I left it in place. A future fleet refresh can recreate this condition if its completion sequence does not include the existing dangling-image cleanup.
