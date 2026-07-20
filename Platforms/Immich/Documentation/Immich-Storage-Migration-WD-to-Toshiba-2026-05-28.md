# Immich Storage Migration: WD Red Plus to Toshiba (Proxmox Grey Server)

**Created:** 2026-05-28  
**Last updated:** 2026-07-20

**Author:** Duresa7
**Date:** 2026-05-28
**System:** Proxmox node grey-server, Docker-Main LXC (ID 110), Immich v2.7.5
**Status:** Completed successfully

---

## 1. Summary

I migrated my Immich photo and video library off the aging WD Red Plus drive and onto a separate Toshiba drive, with zero data loss and no loss of albums, faces, tags, or any other organizational metadata. The migration was done entirely at the ZFS and Proxmox layer using a stop, copy, verify, retire workflow. Throughout the process I kept a full second copy of the data and an off-machine database backup so that I always had a rollback path. After verifying that Immich was fully functional on the new drive, I destroyed the old pool and physically removed the WD.

This document records what I did, why I did it in this order, and the precautions I took at each step.

---

## 2. Background and Goal

My Immich instance runs inside the Docker-Main LXC (container 110) on the Proxmox grey-server node. The library and database lived on a ZFS pool named `hddpool`, which was backed by a single WD Red Plus 4 TB drive (model WDC WD40EFPX-68C6CN0).

I wanted to:

1. Move the entire Immich dataset (photos, videos, database, albums, faces, all metadata) to a different physical drive.
2. Free up the WD drive so I could remove it and repurpose it on a separate machine.
3. Do all of this without losing any of my organized content.

The key risk I needed to manage: the Immich database holds all of the organization (albums, face recognition, tags, favorites, shared links, smart search data), while the actual photo and video files live on disk. Both have to move together and stay consistent, or I would end up with a library that opens but has lost all its structure.

---

## 3. Pre-Migration Assessment

Before touching anything, I mapped out exactly what was on the drive and what depended on it.

### 3.1 What was using the HDD

I checked every LXC and VM config on grey-server for references to `hddpool`, and I checked which Docker containers bind-mounted paths on the drive. The findings:

- **LXC 110 (Docker-Main):** mounted the pool at `/data` (this was the main consumer).
- **Docker containers actively using `/data`:** `immich_server`, `immich_postgres`, and `forgejo`.
- **Stale leftovers:** an empty `calibre` directory, Nextcloud marker files (`.htaccess`, `.ncdata`), and three empty placeholder ZFS datasets (`general`, `nextcloud-data`, `omv`).

### 3.2 Immich storage layout

Immich was configured with:

- `UPLOAD_LOCATION=/data/immich/library`
- `DB_DATA_LOCATION=/data/immich/postgres`

Both lived on the same pool, which simplified the migration since I could move everything as a single unit.

### 3.3 Drive health check on the target Toshiba

The replacement Toshiba (model DT01ACA200, 2 TB) had been used previously, so I ran a SMART check before trusting it. SMART reported PASSED, with zero reallocated sectors, zero pending sectors, and zero CRC errors. I noted that the drive had high power-on hours and a high load cycle count, so I treated it as serviceable but not as a long-term single point of failure. This is part of why I kept the WD copy intact until I had fully verified the new setup.

---

## 4. Cleanup Before Migration

To reduce risk and shrink the amount of data I had to move, I cleaned house first.

### 4.1 Migrated Forgejo to local NVMe storage

Forgejo was small (about 2.6 MB, holding two repositories). Rather than carry it along to the new drive, I moved it onto the LXC's local LVM (NVMe-backed) storage so it no longer depended on the HDD at all. The steps:

1. Stopped the Forgejo container with `docker compose down`.
2. Backed up the compose file.
3. Moved the data directory from `/data/forgejo` to `/opt/docker/forgejo/data`.
4. Updated the bind mount in the compose file to a relative `./data:/data` path.
5. Brought it back up and confirmed both repositories were visible and the web UI returned HTTP 200.

### 4.2 Removed stale Nextcloud and Calibre leftovers

I deleted the empty `calibre` directory and the orphaned Nextcloud marker files on Docker-Main. I also destroyed the three empty placeholder ZFS datasets (`general`, `nextcloud-data`, `omv`) on grey-server, since none of them held data and no service used them.

After this cleanup, the HDD was effectively serving Immich only.

---

## 5. Database Backup (Primary Precaution)

Before any data movement, I captured a database backup as my safety net. The reasoning: even with a full file copy, the database is the single most valuable and least replaceable piece, because it holds all the albums, named faces, and metadata that took real effort to build.

Steps I took:

1. Confirmed Immich's automatic nightly backups were already running. There were 14 days of `.sql.gz` dumps in `/data/immich/library/backups/`.
2. Triggered a fresh manual backup through the Immich web UI (Administration, Job Queues, Create Job, Create Database Backup).
3. Verified the new dump on disk: I confirmed the gzip integrity, checked that the file started with the PostgreSQL dump header and ended with the "dump complete" footer (so it was not truncated), and confirmed the uncompressed size was reasonable (about 103 MB from a 40 MB compressed file).
4. Downloaded the verified backup to my personal PC, so a copy existed completely off the grey-server.

At this point I had the database protected in a location independent of either drive.

I also reviewed the official Immich backup and restore documentation to confirm my understanding of what the database backup does and does not contain. The key confirmations:

- Database backups contain metadata only, not photos or videos. They must be paired with a copy of the files.
- The `thumbs` and `encoded-video` folders hold generated content and do not need to be backed up. They can be regenerated by rerunning the transcoding and thumbnail jobs after a restore.
- The essential folders to preserve are `library`, `upload`, and `profile`, plus the PostgreSQL data directory.

---

## 6. Building the New Pool

I installed the Toshiba into grey-server, wiped it, and initialized it with a GPT label. I then created a new single-disk ZFS pool through the Proxmox web UI (Datacenter, grey-server, Disks, ZFS, Create), naming it `hddpool-1`. I left "Add Storage" checked so Proxmox would register the pool as a usable storage backend automatically.

I deliberately created the pool using the drive's persistent device path rather than a transient `/dev/sdX` name, so the pool would survive reboots and any change in drive ordering.

I verified the result on the command line: the pool came up ONLINE, mapped to the correct Toshiba device, showed the expected usable capacity, and appeared in the Proxmox storage config.

---

## 7. Shrinking the Dataset

The Toshiba is smaller than the WD, so I needed the Immich dataset to fit comfortably. The largest consumer by far was the `encoded-video` cache, which held transcoded copies of every video for web playback. Since these are generated files that Immich can rebuild from the originals, they were safe to delete.

Steps:

1. Stopped Immich cleanly with `docker compose down`.
2. Deleted the contents of `/data/immich/library/encoded-video/`. I intentionally kept the `thumbs` cache.
3. Re-measured the dataset.

This dropped the Immich footprint from roughly 1.9 TB down to about 825 GB, which left plenty of headroom on the Toshiba. The original photos and videos in `library/library`, the in-flight uploads in `library/upload`, the profile images, and the PostgreSQL data were all left fully intact.

---

## 8. The Migration (Stop, Copy, Verify)

I used Proxmox's built-in volume move so the LXC config would be updated automatically and the copy would happen at the storage layer.

### 8.1 Decision: keep the source copy

When I ran the move, I deliberately chose not to delete the source. This meant that after the copy completed, I would have two complete copies of the data: the original on the WD and the new one on the Toshiba. The WD copy stayed as a rollback option until I had personally verified the new setup. I did not want a single move operation to be the only thing standing between me and my entire library.

### 8.2 Running the move

1. Stopped LXC 110.
2. Ran `pct move-volume 110 mp0 hddpool-1` (without the delete flag, so the source was preserved).
3. Let it run in the background and monitored progress by watching the destination subvolume grow relative to the known source size, plus the live task log in the Proxmox UI.

The move transferred roughly 886 GB across about 32,000 files at an average of about 132 MB/s, completing in well under two hours. On completion, Proxmox automatically updated the LXC config so that `mp0` pointed at the new `hddpool-1` subvolume, while the old subvolume on `hddpool` remained in place as planned.

---

## 9. Verification

With the data on the Toshiba, I brought everything back online and tested it thoroughly before retiring the old drive.

1. Started LXC 110 and confirmed `/data` was now mounted from the Toshiba pool.
2. Confirmed the Immich data directories were present.
3. Started Immich with `docker compose up -d`.
4. Watched all four containers (server, postgres, machine learning, redis) come up healthy, and confirmed the server reported it was listening on port 2283.
5. Confirmed the web UI returned HTTP 200.

I then logged into the Immich web interface myself and verified the things that actually mattered: the timeline loaded, albums were present with their covers, named people and faces were intact, individual photos opened at full resolution, and videos played. Everything was in place. Nothing had been lost.

---

## 10. Retiring the WD

Once I was confident the Toshiba copy was complete and Immich was fully functional, I retired the old WD pool.

1. Destroyed the old subvolume: `zfs destroy hddpool/subvol-110-disk-0`.
2. Destroyed the pool: `zpool destroy hddpool`.
3. Removed the Proxmox storage entry: `pvesm remove hddpool`.

I verified that only `hddpool-1` remained, that the Proxmox storage config no longer referenced the old pool, and that Immich continued to run normally on the Toshiba.

After that, I rebuilt the video transcode cache so web playback was fully restored, and I physically pulled the WD drive from grey-server so I could repurpose it elsewhere.

---

## 11. Outcome

The migration was a complete success:

- All photos, videos, albums, faces, tags, and metadata moved intact to the Toshiba.
- Immich runs normally from the new drive.
- The WD has been freed and removed for reuse on another machine.
- An off-machine database backup remains on my personal PC as an extra layer of protection.

The order of operations (assess, clean up, back up, build the new target, shrink, copy while keeping the source, verify, then retire) meant that at no point during the migration was there only a single copy of my data. That was the core principle behind the whole process.

---

## 12. Reference: Final State

| Item | Before | After |
| --- | --- | --- |
| Immich storage pool | hddpool (WD 4 TB) | hddpool-1 (Toshiba 2 TB) |
| Immich dataset size | about 1.9 TB | about 825 GB |
| Forgejo | on HDD | on local NVMe |
| Stale datasets and leftovers | present | removed |
| Database backup | on HDD only | copied off-machine to personal PC |
| WD drive | in service | removed for reuse |
