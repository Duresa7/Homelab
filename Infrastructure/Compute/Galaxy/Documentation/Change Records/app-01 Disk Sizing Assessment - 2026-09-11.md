# app-01 Disk Sizing Assessment

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

I checked VM 116 `app-01` at about 12:09 AM Eastern on 2026-09-11 after the [Purple migration assessment](app-01%20and%20edge-01%20Purple%20Migration%20Assessment%20-%202026-09-10.md). Its current workload does not need a 200 GiB disk. I recommend a 64 GiB system disk for the observed services, which would let both app-01 and edge-01 fit on Purple's existing NVMe pool. This is a sizing recommendation, not an approved resize or completed migration.

## Live usage

I read filesystem and Docker usage through SSH Manager on `app_01`, and directory totals and the partition table through Grey's QEMU guest agent for VM 116. The root filesystem is ext4 on `/dev/sda2`. `df -B1 /` reported 14,016,499,712 bytes used, or 13.05 GiB, with 185,261,834,240 bytes available. Inodes were 3% used. No separate data filesystem appeared in the mount inventory.

| Measurement | Observed size |
|---|---:|
| `/var/lib/containerd` | 8.76 GiB |
| `/var/lib/docker` | 147.21 MiB |
| `/usr` | 2.43 GiB |
| `/var/cache` | 517.11 MiB |
| `/data/coolify` | 341.83 MiB |
| `/var/log` | 210.37 MiB |
| Docker images, Docker's own accounting | 9.365 GB total, 6.175 GB reported reclaimable |
| Docker local volumes | 124.6 MB total, 49.35 MB reported reclaimable |
| Docker build cache | 0 bytes |

The Docker accounting overlaps the directory totals and uses decimal units; I do not add those rows together. Of 19 images, seven were active. The seven running containers were Coolify 4.3.18, its Postgres database, Redis, Realtime, Sentinel, Traefik, and cAdvisor. All reported healthy. There was no additional deployed application container in this inspection, although old application build images remained. The Coolify database volume was 74.28 MB, Redis 972.2 kB, and one unused PostgreSQL volume 49.35 MB. `/data/coolify/backups` held 79,429,632 bytes. I did not read its contents, delete it, or prune any image or volume.

Grey's `lvs` reported the 200 GiB system volume at 24.24% allocated, about 48.48 GiB. The configured 200 GiB is a virtual capacity ceiling, not 200 GiB of consumed physical storage. Host thin allocation also differs from the guest's current file usage; I did not establish how much of that difference a discard operation would recover. The smaller-disk recommendation does not depend on reclaiming old images.

## Retained history

I queried Prometheus locally on `monitor_01` for `node_filesystem_size_bytes - node_filesystem_free_bytes`, matched on `host="app-01",mountpoint="/"`. The first 15-day request at 60-second resolution returned HTTP 400. Retrying at 120-second resolution succeeded with 10,798 evaluations from August 27 at 12:10:05 AM to September 11 at 12:10:05 AM Eastern. The successful query had 10,801 possible evaluation points, so coverage was about 99.97%. These are range-query evaluations, not a count of original scrapes.

| Measurement | Used space |
|---|---:|
| First evaluation | 11.71 GiB |
| Last evaluation | 13.05 GiB |
| Minimum | 11.70 GiB |
| Maximum | 13.48 GiB |
| 95th percentile | 13.47 GiB |
| Net change across the window | +1.35 GiB |

The peak evaluation was September 9 at 12:02:05 AM Eastern. Usage rose in steps and also fell; I would not project a constant growth rate from the net change. Two-minute evaluations can miss short build peaks, and this history does not establish requirements for future locally hosted applications or large databases.

## Revised placement recommendation

I would allocate 64 GiB to app-01 for the current workload, leaving roughly 45 GiB beyond current use after allowing for EFI, swap, filesystem overhead, and reserved space. Larger local builds or new application data would justify revisiting that limit; expanding a disk later is supported.

Purple's `pvesm status` still showed an empty 140.87 GiB `local-lvm` pool. A 64 GiB app disk plus edge-01's existing 30 GiB disk and both 4 MiB EFI volumes would provision about 94.01 GiB, leaving about 46.86 GiB of uncommitted pool capacity. This gives a route to placing both guests on NVMe without making the worn SATA SSD part of this migration. The previous assessment's SATA recommendation applied to retaining app-01's existing 200 GiB disk.

## How a reduction would work

The current GPT layout has a 976 MiB EFI partition, about 197 GiB of ext4 root, and a 2 GiB swap partition at the end of the disk. Grey's installed `qm help resize` explicitly states that shrinking disk size is unsupported. The [resize2fs manual](https://www.man7.org/linux/man-pages/man8/resize2fs.8.html) supports shrinking an unmounted filesystem and requires filesystem reduction before partition reduction. The trailing swap and GPT metadata also need handling; editing the VM's size field cannot relocate them.

I prefer a planned transfer to a new 64 GiB boot disk, with application writes stopped for the final copy, filesystem metadata preserved, and EFI/GRUB, filesystem identifiers, swap, permissions, and Docker storage verified before cutover. An offline filesystem-and-partition shrink is another route but needs its own reviewed procedure. I have not prepared or executed either procedure in this assessment.

The AMD-to-Intel shutdown migration and live switch-port VLAN verification from the previous assessment still apply. I retained these measured results in this record without a raw terminal transcript or full Prometheus time series. No disk, filesystem, service, guest allocation, snapshot, or backup was changed or created.
