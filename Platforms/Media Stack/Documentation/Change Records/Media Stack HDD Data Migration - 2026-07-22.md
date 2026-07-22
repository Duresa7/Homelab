# Media Stack HDD Data Migration

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Implementation date:** 2026-07-22  
**System:** Galaxy `red-server`, CT 842 `media-01`  
**Status:** Complete

## Scope

I moved `/data` from CT 842's 100 GiB NVMe root volume to the 1 TB Seagate ST1000LM035 HDD. Movies, television, downloads, & Jellyfin transcodes moved together; `/opt/media-stack`, Docker, application configuration, databases, & Jellyfin cache stayed on NVMe.

## Starting State

CT 842 had no mount point besides its `local-lvm:vm-842-disk-0` root volume. `/data` used 9.9 GiB across 19 files, while the root filesystem used 19 GiB of 98 GiB. All eight Compose services were running before the maintenance outage.

The target `/dev/disk/by-id/ata-ST1000LM035-1RK172_WCB0SRHK` resolved to `/dev/sda`. It had a GPT label with no partition or filesystem. SMART reported `PASSED`, three completed short tests, 23,951 power-on hours, 1,432,702 load cycles, & zero reallocated, reported-uncorrectable, pending, offline-uncorrectable, or CRC-error sectors.

## Decisions

1. I chose ext4 on one full-disk partition because this drive uses drive-managed SMR & holds replaceable media on one disk.
2. I kept every guest path unchanged. A host bind mount supplies `/data`, so Compose needed no edit.
3. I didn't create a new backup or run the 168-minute extended SMART test. I accepted the used disk's measured history & treat the media as replaceable.
4. I retained the NVMe source through validation, then deleted it in the same project to recover 9.9 GiB.

## Step 1: Confirm the source and target

**Action:** I inspected the persistent disk path, GPT, SMART attributes, CT configuration, filesystem use, source file count, & Compose state through the SSH Manager target `red_server`.

**Observed result:** The by-id path matched the approved ST1000LM035 disk. The GPT was empty, every stop-condition SMART counter stayed at zero, CT 842 had no `mp0`, `/data` held 19 files in 9.9 GiB, & eight services were running.

**Verification:** The preflight command exited `0`. The [S01 transcript](../../Evidence/Media%20Stack%20HDD%20Data%20Migration%20-%202026-07-22/Logs/S01-Preflight-2026-07-22.md) records the command & result; the [raw SMART baseline](../../../../Operations/Diagnostics/SMART/red-server-seagate-1tb-st1000lm035-srhk.txt) preserves the full `smartctl -a` output beside the existing NVMe reports.

## Step 2: Build the ext4 mount

**Action:** I created one Linux-filesystem partition from sector 2,048 through the end of the approved HDD, formatted it as ext4 with 4 KiB blocks, labeled it `media-01-data`, & set the reserved-block count to zero. I mounted its UUID at `/mnt/bindmounts/media-01-hdd` through `/etc/fstab` with `noatime`, `nofail`, `x-systemd.automount`, & a 10-second device timeout.

**Observed result:** Partition 1 has 931.5 GiB, filesystem UUID `289788f9-52a4-4e49-885b-000e8d565c8b`, a clean ext4 state, & zero reserved blocks. The mounted `data` directory has host ownership `101000:101000`, which maps to guest `1000:1000`.

**Verification:** `lsblk`, `findmnt`, `tune2fs`, `stat`, & the `/etc/fstab` readback matched the planned values. The [S02 transcript](../../Evidence/Media%20Stack%20HDD%20Data%20Migration%20-%202026-07-22/Logs/S02-Ext4-Provisioning-2026-07-22.md) records the write & verification.

## Step 3: Copy and attach `/data`

**Action:** I stopped the eight existing containers without removing them, shut down CT 842, mounted its root volume, & copied `/data` to the HDD with `rsync -aHAXS --numeric-ids`. I computed content & metadata manifests on both filesystems, then ran a checksum-based rsync dry run before changing the guest configuration.

**Observed result:** Rsync transferred 19 files in 12 directories, totaling 10,615,586,954 logical bytes, at 130,284,429 bytes per second. The source & destination content-manifest hash was `14a63738f3871ccb6dffad205c7189d75077eb245a1991f94d3792a850d1d886`; the metadata-manifest hash was `63fb8ecbf67f1949ee43aeafda9c316f7764422478f6a78f528a94607466fda2`. The checksum dry run reported zero changes.

I renamed the NVMe source to `/data.nvme-source`, created an empty `/data` mountpoint, & attached `/mnt/bindmounts/media-01-hdd/data` as CT 842 `mp0` with `backup=0`. The same stopped containers restarted without pulling or recreating an image.

**Verification:** Inside CT 842, `/data` reports 916 GiB on `/dev/sda1` with guest ownership `1000:1000`; `/`, `/opt/media-stack`, & `/data.nvme-source` remain on device `64518`, the NVMe root volume. All eight containers started, & Jellyfin and Gluetun reported healthy. The [S03 transcript](../../Evidence/Media%20Stack%20HDD%20Data%20Migration%20-%202026-07-22/Logs/S03-Copy-and-Cutover-2026-07-22.md) holds the copy, comparison, & attachment results.

## Step 4: Verify application data paths

**Action:** I tested all eight running services, Jellyfin & Gluetun health, qBittorrent's exact Gluetun namespace, forwarded-port synchronization, six HTTP listeners, a qBittorrent-created download file, & a hard link between the download and media trees. I then read an existing movie through Jellyfin's bundled ffmpeg and encoded 10 seconds with `h264_qsv` into `/transcodes`.

**Observed result:** The qBittorrent file landed on HDD device `2049` as UID/GID `1000:1000`. The hard-link source & target shared device `2049`, inode `37224480`, & link count `2`. Jellyfin's Intel iHD driver initialized, the H.264 Quick Sync output reached 3,187,149 bytes on device `2049`, & cleanup removed every `.migration*` test file.

**Verification:** The provider-forwarded port matched qBittorrent, the VPN organization differed from the guest's ordinary egress, Jellyfin returned `Healthy`, & all six exposed HTTP listeners answered. The [S04 transcript](../../Evidence/Media%20Stack%20HDD%20Data%20Migration%20-%202026-07-22/Logs/S04-Functional-Validation-2026-07-22.md) records the assertions & outputs.

## Step 5: Test missing-disk startup and reclaim NVMe

**Action:** I stopped the containers & CT 842, stopped the HDD mount unit, & confirmed the bind-source child disappeared. The first verification wrapper exited after `findmnt` returned its expected no-match status under `set -e`; the [troubleshooting record](../Troubleshooting/Fail-Closed%20Verification%20findmnt%20Exit%20Handling%20-%202026-07-22.md) records that command-control error.

I resumed from the inspected stopped state. `pct start 842` failed with exit `255` while `/mnt/bindmounts/media-01-hdd/data` was absent. After I started the systemd automount, the same path resolved to `/dev/sda1`, CT 842 started, & all eight services plus both health checks passed again.

**Observed result:** The missing-disk state blocked CT initialization before an application could write to an empty NVMe directory. After the second validation, I checked the exact `/data.nvme-source` path, its root-volume device `64518`, its 19 files, & its 10,615,586,954 logical bytes before deleting it with `rm -rf --one-file-system`.

**Verification:** Root-volume use fell from 19 GiB to 9.1 GiB; `/data` stayed at 9.9 GiB with 906 GiB free. The final audit found 19 media-tree files, no rollback source, no temporary test files, eight services, healthy Jellyfin & Gluetun, matched VPN ports, active mount and automount units, & unchanged zero-valued SMART stop counters. The [S05 transcript](../../Evidence/Media%20Stack%20HDD%20Data%20Migration%20-%202026-07-22/Logs/S05-Fail-Closed-Cleanup-and-Final-Audit-2026-07-22.md) records the test, deletion guard, & final state.

## Resulting Configuration

| Layer | Result |
| --- | --- |
| Physical disk | Seagate ST1000LM035-1RK172, 1 TB nominal, 931.5 GiB raw |
| Partition | GPT partition 1, sectors 2,048 through 1,953,523,711 |
| Filesystem | ext4, label `media-01-data`, UUID `289788f9-52a4-4e49-885b-000e8d565c8b`, 4 KiB blocks, zero reserved blocks |
| Host mount | `/mnt/bindmounts/media-01-hdd`, `noatime`, `nofail`, systemd automount, 10-second device timeout |
| CT mount | `mp0: /mnt/bindmounts/media-01-hdd/data,mp=/data,backup=0` |
| HDD contents | `/data/media`, `/data/downloads`, `/data/transcodes`; 19 files, 10,615,586,954 logical bytes at completion |
| NVMe contents | Debian, Docker, `/opt/media-stack`, application configuration, databases, & Jellyfin cache |
| Capacity | `/data`: 916 GiB usable, 9.9 GiB used, 906 GiB free; `/`: 98 GiB usable, 9.1 GiB used, 84 GiB free |
| Failure behavior | CT 842 pre-start fails when the HDD-backed bind source is absent |
| Backup policy | `vzdump` excludes `/data`; the media is replaceable |

## Rollback

The copy-verification checkpoint provided local rollback until I deleted `/data.nvme-source`. That source is gone. A disk-loss recovery now requires a replacement filesystem at the recorded bind path plus reacquisition of movies & television; Compose and application state remain on the NVMe root.

## Remaining Work

The migration has no remaining step. Configuration backup and restore testing, HDD capacity alerts, the `latest` image maintenance cadence, & the HTTPS ingress decision remain in the [Media Stack TODO](../TODO.md).
