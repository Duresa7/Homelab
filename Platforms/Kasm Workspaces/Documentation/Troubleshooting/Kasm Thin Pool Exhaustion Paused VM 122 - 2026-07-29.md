# Kasm Thin Pool Exhaustion Paused VM 122

**Created:** 2026-07-29  
**Last updated:** 2026-07-30

## Symptom

The Kasm NPM hostname returned HTTP `502` while a Parrot OS workspace image was downloading. The same request had returned HTTP `200` before the image installation.

## Exact Error

The NPM route reproduced the failure in 3.13 seconds:

```text
https://kasm.alphasecunited.com/|502|192.168.85.2|3.134773
https://kasm.alphasecunited.com/api/__healthcheck|502|192.168.85.2|3.176288
https://192.168.78.10/api/__healthcheck|000||10.016189
```

Proxmox reported the backend failure directly:

```text
status: io-error
```

`pvesm status` showed `ssd-lvm2` at 100 percent with zero available KiB. QEMU had recorded 12 failed writes against VM 122's `scsi0`.

## Reproduction

I requested the Kasm root and health endpoint through NPM, then requested the health endpoint directly at `192.168.78.10`. NPM returned `502` twice, while the direct request timed out after 10 seconds.

The [diagnosis transcript](../../../../Security/Incidents/Kasm%20Workspaces/Evidence/Thin%20Pool%20Exhaustion%20-%202026-07-29/Logs/S01%20Diagnosis%20-%202026-07-29.md) retains those requests, the VM status, thin-pool readback, & capacity timeline.

## Hypotheses and Tests

| Rank | Hypothesis | Prediction | Result |
|---:|---|---|---|
| 1 | VM 122 or its HTTPS listener was down | Proxmox or the guest services report a stopped or failed state | Confirmed: Proxmox reported `io-error` |
| 2 | Kasm was healthy but the NPM-to-Kasm path failed | The local Kasm health endpoint answers while NPM returns `502` | Rejected: the direct health request timed out |
| 3 | The Parrot pull exhausted storage or other VM resources | Purple reports a full backing pool or the guest reports resource pressure | Confirmed: `ssd-lvm2` held zero free KiB |
| 4 | NPM's proxy-host or upstream TLS setting changed | The backend answers from another source while NPM alone fails | Rejected by the failed direct health request; I changed no NPM setting |

## Root Cause

The 228.11 GiB `ssd-lvm2` data pool reached 100 percent after I installed the Parrot OS registry entry. VM 122 carried a 200 GiB current disk, a 200 GiB baseline snapshot, & a 150 GiB pre-build snapshot. Those 550 GiB of logical volumes shared unchanged thin blocks, but each new or overwritten block still needed physical space.

The VM disk lacked `discard=on`. Its Ubuntu filesystem reported 77 GiB free before the pull, but deleted or replaced guest blocks didn't return capacity to the LVM-thin pool. The two snapshots also retained the older versions of blocks that changed. `dmeventd` recorded 90.02 percent use at 22:05:09 EDT, 95.10 percent at 22:09:39, & 100.00 percent at 22:24:09.

The controlled retry on 2026-07-30 exposed the missing part of the cause. Kasm did not pull only Parrot. Its agent checked every workspace row with a Docker Registry and moved through the `rolling-daily` catalog, including Terminal, Claude Code, and Forensic OSINT. Kasm documents that an agent checks all defined images and pulls configured registry tags again each hour. The 108 GiB rollback delta was catalog churn retained by two snapshots, not a 108 GiB Parrot image.

Proxmox paused QEMU after the thin pool stopped accepting writes. Kasm then stopped answering on TCP 443, so NPM returned `502`. The Samsung SSD passed its live SMART health check with zero reallocated sectors, uncorrectable errors, or CRC errors; no raw SMART artifact was retained for this troubleshooting record.

## Corrective Action

I stopped the paused QEMU process and rolled VM 122 back to `baseline-tiles-2026-07-28`, captured at 2026-07-28 23:08:18 EDT. The rollback removed the incomplete Parrot installation and reduced `ssd-lvm2` from 100 percent to 52.51 percent before boot.

PostgreSQL replayed its write-ahead log after the unclean stop. Redo finished after 83.22 seconds, the recovery checkpoint completed, & the database accepted connections at 02:50:03 UTC. The dependent Kasm containers then restarted through their existing `unless-stopped` policies.

I changed no Kasm, NPM, UniFi, or Docker configuration during recovery.

Later on 2026-07-29, I shut down VM 122 cleanly and changed its existing disk entry to `scsi0: ssd-lvm2:vm-122-disk-1,discard=on,iothread=1,size=200G,ssd=1`. I started the same disk, waited for the QEMU guest agent, & ran `fstrim -av`. The guest submitted 72.7 GiB from `/`, 757.9 MiB from `/boot`, & 98.2 MiB from `/boot/efi`.

`ssd-lvm2` fell from 54.91 to 54.78 percent immediately after trim, a release of about 0.13 percentage points. Both snapshots still reference most of the old blocks, so enabling discard doesn't replace the snapshot-retention decision.

I then deleted only `pre-workspace-buildout-2026-07-28` while VM 122 remained online. Proxmox removed its disk and cloud-init snapshot volumes, retained `baseline-tiles-2026-07-28`, & reduced `ssd-lvm2` from 54.79 to 53.85 percent. That returned about 2.14 GiB and left one snapshot.

At 23:56 EDT, I deleted `baseline-tiles-2026-07-28` before retrying Parrot. That removed the last old rollback point and reduced the pool from 53.87 to 52.10 percent. VM 122 then had zero snapshots.

The retry started another catalog refresh. I stopped `kasm_agent` at 68.67 percent while Forensic OSINT was pulling. Canceling the incomplete pull reduced the pool to 61.61 percent. I pruned seven untagged images with no container references, reclaimed 7.112 GB, trimmed 23.1 GiB from `/`, and reduced the pool to 51.46 percent.

With the agent stopped, I pulled only `kasmweb/parrotos-7-desktop:1.19.0-rolling-daily`. It completed at the verified digest `sha256:8dc7c7821c3e69f6e7d4bbef0a55d84f6e4c784851fa729773b273d72dddd736`. The pool ended at 67.44 percent and the guest retained 39 GB free.

I cleared the Docker Registry field on all 31 Kasm workspace rows that existed before the Parrot clones. That preserves local-image launches and stops the agent from polling every moving tag. I restarted the agent, observed no new pull, added the three Parrot variants, renamed Debian Target to Debian Malware, and created `baseline-parrot-2026-07-30` after the lane checks passed.

## Verification

- VM 122 reports `status: running`.
- All eight Kasm service containers run; the seven containers with Docker health checks report `healthy`.
- The local `/api/__healthcheck` endpoint returns `{"ok":true}`.
- The NPM root and health endpoint each returned HTTP `200` in 32 ms or less at 22:56:13 EDT.
- `ssd-lvm2` reported 54.74 percent data use after PostgreSQL recovery and final service checks.
- The guest root filesystem reported 121 GiB used and 73 GiB available.
- No container remained in `Created`, `Restarting`, or `unhealthy` state.
- VM 122's live `scsi0` readback includes `discard=on`.
- After the controlled restart, all seven Docker health checks returned `healthy`; `kasm_proxy` has no health check.
- The public root and health endpoint returned HTTP `200` in 21.883 ms and 29.965 ms.
- `ssd-lvm2` settled at 54.80 percent after Kasm finished writing startup state.
- `qm listsnapshot 122` reported zero snapshots after the old baseline deletion and exactly one after the completed change: `baseline-parrot-2026-07-30`.
- After the older snapshot deletion, `ssd-lvm2` reported 53.85 percent data and 2.44 percent metadata.
- The final public root and health checks returned HTTP `200` in 31.308 ms and 30.693 ms.
- The controlled Parrot pull completed with one named Docker pull and raised `ssd-lvm2` from 51.46 to 67.44 percent.
- Parrot Full, Normal, and VPN used the default, VLAN 75, and VLAN 74 networks. Debian Malware on VLAN 77 failed DNS and direct TCP as designed.
- The agent logged no image pull after automatic registry checks were disabled.
- At snapshot creation, `ssd-lvm2` reported 67.45 percent data. The 01:18 EDT final readback reported 68.25 percent data and 2.91 percent metadata; all Kasm services remained healthy and the local health endpoint returned HTTP `200`.

The [rollback and verification transcript](../../../../Security/Incidents/Kasm%20Workspaces/Evidence/Thin%20Pool%20Exhaustion%20-%202026-07-29/Logs/S02%20Rollback%20and%20Verification%20-%202026-07-29.md) retains the commands and results.

The [discard and trim transcript](../../../../Security/Incidents/Kasm%20Workspaces/Evidence/Thin%20Pool%20Exhaustion%20-%202026-07-29/Logs/S03%20Discard%20Enablement%20and%20Trim%20-%202026-07-29.md) retains the controlled shutdown, disk change, trim output, & final service checks.

The [snapshot deletion transcript](../../../../Security/Incidents/Kasm%20Workspaces/Evidence/Thin%20Pool%20Exhaustion%20-%202026-07-29/Logs/S04%20Older%20Snapshot%20Removal%20-%202026-07-29.md) retains the before-and-after snapshot trees, pool readings, & health checks.

The [final old-baseline removal transcript](../../../../Security/Incidents/Kasm%20Workspaces/Evidence/Thin%20Pool%20Exhaustion%20-%202026-07-29/Logs/S05%20Final%20Baseline%20Removal%20-%202026-07-29.md) records the zero-snapshot boundary before the retry.

The [Parrot build-out evidence](../../Evidence/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30/Evidence-Index.md) retains the queue stop, dangling-image cleanup, controlled pull, update-policy change, tile readback, lane tests, and replacement snapshot.

## Failed Attempts

I first treated the `502` as a proxy-path fault. The direct Kasm request timed out, and `qm status 122` then moved the investigation below NPM.

The first post-rollback API checks still returned `502` while PostgreSQL replayed 83 seconds of WAL and completed a 160-second recovery checkpoint. I didn't restart the database or dependent containers during that interval. PostgreSQL reached its consistent state, and Docker's existing restart policies recovered the application services.

## Remaining Work

The Parrot retry, automatic-pull control, capacity gate, tile changes, and replacement snapshot are complete. The automated alert below the 80 percent action threshold was dropped on 2026-08-06 rather than built, so the manual hard stop is the standing control. The current pool and guest free space fail the new-image gate, so another large image remains blocked.

## Rollback

The current rollback point is `baseline-parrot-2026-07-30`, created after the completed Parrot and Debian checks. Rolling back to it preserves this correction. I retained no recovery path to the failed incomplete-pull state.

## Linked Records

- [Kasm Workspaces Thin Pool Exhaustion Incident](../../../../Security/Incidents/Kasm%20Workspaces/Thin%20Pool%20Exhaustion%20-%202026-07-29.md)
- [Kasm Workspace Build-Out - 2026-07-28](../Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md)
- [Kasm Parrot Workspace Build-Out - 2026-07-30](../Change%20Records/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30.md)
- [Galaxy TODO](../../../../Infrastructure/Compute/Galaxy/Documentation/TODO.md)
