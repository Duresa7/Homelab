# Image Cleanup and Schedules

**Created:** 2026-09-18  
**Last updated:** 2026-09-18

**Status:** Complete.  
**Cleanup window:** September 18, 2026, 12:46 PM to 12:48 PM Eastern.

I removed 57 untagged, unused images across the seven Docker hosts managed by Dockhand. Available filesystem space increased by 23.97 GB during the host-by-host cleanup. I checked security-01 and found no eligible images. This scope excludes app-01 and Coolify, which are outside this Dockhand deployment.

## Selection and removal

I listed Docker's dangling images, inspected each image, and checked references from every running and stopped container. The initial list contained 67 image IDs across the fleet. Three were still referenced by containers and seven returned nonempty image tags or references from inspection. I preserved all ten and selected the remaining 57. None of the selected images carried an image-level `dockhand.prune=false` label.

I used `docker image rm --no-prune <image-id>` for each reviewed image, without force, rather than passing the entire dangling list to a blanket prune. Immediately before each removal I checked the tags, container references, and protection label again. The command disables removal of untagged parent images beyond the selected ID. Every removal returned exit code 0, and every selected image was absent afterward.

I retained the executed [cleanup script](../../Evidence/Image%20Cleanup%20and%20Schedules%20-%202026-09-18/Logs/cleanup.py), preflight image inventories, and per-host structured [results](../../Evidence/Image%20Cleanup%20and%20Schedules%20-%202026-09-18/Exports/). The script received each host's reviewed image IDs and preflight hashes as its JSON argument and ran through SSH Manager with Python's standard library. The exports retain command exit codes, output hashes, comparison results, and storage readings. I did not retain complete terminal or image-removal transcripts.

| Host | Images removed | Increase in available space |
|---|---:|---:|
| docker-main | 22 | 8.56 GB |
| docker-blue | 2 | 0.44 GB |
| docker-network | 7 | 1.62 GB |
| monitor-01 | 2 | 2.12 GB |
| media-01 | 22 | 10.98 GB |
| alpha-prod-01 | 2 | 0.26 GB |
| security-01 | 0 | 0 GB |
| **Total** | **57** | **23.97 GB** |

These are decimal GB calculated from before-and-after available filesystem bytes. Live workloads continued writing, so the difference is an observed space increase rather than Docker's exact accounting of deleted layers. Shared layers and retained build cache also make the sum of image sizes unsuitable as a reclaimed-space measurement.

## Verification

I compared all 70 containers, including the six stopped or created updater helpers. Container IDs, image IDs, start timestamps, restart counts, running states, health states, and mount definitions were preserved. All 64 running containers stayed running. All 30 Docker volumes retained their names and inspected definitions. Every tagged image reference remained unchanged. I did not prune containers, volumes, networks, or build cache, and I did not update or recreate any application.

The first security-01 comparison returned exit code 2 because my hash treated Docker's mount-array order as meaningful. That host had an empty removal list and performed no mutation. I reproduced both the before and after hashes by permuting only the order of the same current mounts, confirming that the container fields and mount definitions were unchanged. The [follow-up verification](../../Evidence/Image%20Cleanup%20and%20Schedules%20-%202026-09-18/Exports/security_01-mount-order-verification.json) retains both matching hashes; the original failed comparison remains in the evidence.

The first read-only preflight attempted passwordless sudo, which was unavailable on the six remote agent hosts. I reran through the existing Docker access of each SSH account. The first docker-main inventory also exceeded the gateway's output limit; the complete compact preflight replaced that truncated read before any removal. No complete transcript is retained for those initial reads.

## Existing schedules

I read the live Dockhand database in SQLite read-only mode and captured the [schedule settings](../../Evidence/Image%20Cleanup%20and%20Schedules%20-%202026-09-18/Exports/Schedule-Settings.json) at 12:45 PM Eastern. I did not change the settings or trigger an update or scan.

| Environments | Update schedule, Eastern | Automatic updates | Scanner | Vulnerability block |
|---|---|---|---|---|
| docker-main, docker-blue, docker-network, monitor-01, media-01, security-01 | Daily, 3:00 AM | Enabled | None | Never |
| alpha-prod-01 | Monday, 3:00 AM | Enabled | Both scanners | Critical or high |

All seven environments have automatic dangling-image pruning enabled for Monday at 4:00 AM, with `America/New_York` as their timezone. There are no per-container auto-update entries. Automatic updates are enabled everywhere; alpha-prod-01 is the only environment configured to scan and block updates on critical or high vulnerabilities. This read verifies configuration, not successful execution of the new schedules or scanners.

I created no snapshots, backups, or host-side script files. No cleanup work remains open.
