# Kasm Workspaces Thin Pool Exhaustion

**Created:** 2026-07-29  
**Last updated:** 2026-08-06

## Incident Metadata

| Field | Value |
|---|---|
| Incident ID | ASU-KASM-20260729-001 |
| Start | 2026-07-29 22:24:09 EDT |
| Detected | 2026-07-29 by user report; exact minute not retained |
| Mitigated | 2026-07-29 22:56:13 EDT |
| Validated | Service restored 2026-07-29 22:56:13 EDT; prevention validated 2026-07-30 01:05:48 EDT |
| Duration | About 32 minutes |
| Status | Closed 2026-08-06; controlled image maintenance and replacement baseline complete; the automated alert was dropped rather than built |
| Severity | SEV-3 |
| Impact type | Availability of the Kasm Workspaces control plane and sessions |
| Affected services | Kasm Workspaces 1.19.0, VM 122, NPM proxy host 23 |

## Summary

`ssd-lvm2` reached 100 percent data use after I installed the Parrot OS registry entry. Proxmox paused VM 122 with `io-error` after 12 failed disk writes, which removed Kasm's TCP 443 backend and caused NPM to return HTTP `502`.

I rolled VM 122 back to `baseline-tiles-2026-07-28`. The pool fell to 52.51 percent before boot, PostgreSQL completed automatic recovery, all eight Kasm services returned healthy, & both NPM endpoints returned HTTP `200` at 22:56:13 EDT.

The controlled retry proved Kasm had refreshed the whole moving-image catalog, not only Parrot. I disabled automatic registry pulls, pruned unused layers, installed Parrot by itself, verified the requested lanes, and replaced both old snapshots with one post-Parrot baseline.

## Impact

The Kasm web interface and health endpoint were unavailable for about 32 minutes. Existing or new workspace sessions couldn't use the control plane while QEMU remained paused.

I found no evidence of SSD media failure, network-policy bypass, or credential exposure. The rollback removed changes after the 2026-07-28 23:08:18 EDT snapshot, including the incomplete Parrot image installation.

## Affected Assets

- `kasm-01`, VM 122 on `purple-server`.
- Purple's 228.11 GiB `ssd-lvm2` thin data pool on `/dev/sda`.
- Kasm Workspaces 1.19.0 service containers.
- NPM proxy host 23 for `kasm.alphasecunited.com`.

The Galaxy cluster remained quorate. NPM itself stayed online and returned `502` because its approved backend didn't answer.

## Symptoms

The Kasm root and health endpoint through NPM returned HTTP `502` after about 3.1 seconds. A direct request to `192.168.78.10` timed out after 10 seconds.

Proxmox reported:

```text
status: io-error
```

`pvesm status` showed `ssd-lvm2` with zero available KiB and 100.00 percent use.

## Timeline

| Time | Event |
|---|---|
| 22:05:09 EDT | `dmeventd` warned that `ssd-lvm2` was 90.02 percent full. |
| 22:09:39 EDT | The pool reached 95.10 percent. |
| 22:24:09 EDT | The pool reached 100.00 percent; VM 122 later reported `io-error`. |
| Exact minute not retained | The user reported an unexpected Kasm `502`. |
| About 22:36 EDT | Direct NPM and backend probes reproduced `502` and timeout results. |
| About 22:44 EDT | I stopped VM 122 and rolled back `baseline-tiles-2026-07-28`. |
| About 22:45 EDT | I started VM 122 with the pool at 52.51 percent. |
| 22:50:03 EDT | PostgreSQL completed automatic recovery and accepted connections. |
| 22:56:13 EDT | Both NPM endpoints returned HTTP `200`; all Kasm health checks passed. |
| Later on 2026-07-29 | I shut down VM 122 cleanly, enabled discard on the existing `scsi0`, started it, & ran `fstrim -av`. |
| 23:28 EDT | I completed the discard verification with all Kasm health checks passing, both public endpoints at HTTP `200`, & `ssd-lvm2` at 54.80 percent. |
| 23:42 EDT | I deleted `pre-workspace-buildout-2026-07-28` and retained `baseline-tiles-2026-07-28` as the only VM snapshot. |
| 23:43 EDT | The pool read 53.85 percent, all Kasm health checks passed, & both public endpoints returned HTTP `200`. |
| 23:56 EDT | I deleted `baseline-tiles-2026-07-28`; the pool fell from 53.87 to 52.10 percent and VM 122 had zero snapshots. |
| 23:58 EDT | The Parrot retry began and Kasm created its database row. |
| 00:22 through 00:44 EDT | The agent updated Terminal and Claude Code, then began Forensic OSINT. This exposed the catalog-wide refresh. |
| 00:45 EDT | I stopped `kasm_agent` at 68.67 percent; the incomplete pull cleared and the pool fell to 61.61 percent. |
| 00:48 EDT | I pruned seven unused dangling images, reclaimed 7.112 GB, trimmed the guest, and reduced the pool to 51.46 percent. |
| 00:49 through 00:57 EDT | I pulled only Parrot; the verified image completed with the pool at 67.44 percent. |
| 00:59 EDT | I disabled automatic registry pulls on the Kasm workspace rows and restarted the agent; no new pull started. |
| 01:01 through 01:03 EDT | I added Parrot Full, Normal, and VPN; renamed Debian Target to Debian Malware; and passed the four lane tests. |
| 01:05:48 EDT | I created `baseline-parrot-2026-07-30`; VM 122 had one snapshot, all services were healthy, and the local health endpoint returned HTTP `200`. |

## Findings

- The Samsung SSD exposes 250,059,350,016 bytes, or 232.88 GiB. LVM provides 228.11 GiB to the thin data pool.
- The current 200 GiB disk, 200 GiB baseline snapshot, & 150 GiB pre-build snapshot share that 228.11 GiB pool.
- The VM disk configuration did not include `discard=on`.
- The guest filesystem's 77 GiB free-space reading did not include snapshot-retained or unreclaimed thin blocks.
- Rolling back the post-baseline state released about 108 GiB of physical thin-pool allocation before PostgreSQL recovery wrote new blocks.
- The retry showed that Kasm's agent checks every defined image with a Docker Registry and refreshes moving tags. Parrot was one item in a catalog-wide pull queue.
- Parrot's Docker image inspection reports 13.67 GB, while expanded Docker accounting reports 40.92 GB unique and the guest filesystem grew by about 38 GB.
- The SSD returned SMART `PASSED` with zero reallocated sectors, uncorrectable errors, & CRC errors.
- NPM and UniFi configuration were unchanged; the `502` ended when the Kasm backend returned.

## Root Cause

I treated guest filesystem free space as the capacity gate for installing one large Docker image. The actual stop condition was Purple's `ssd-lvm2` `data_percent`, which included the current thin volume plus blocks retained by two snapshots.

The Kasm agent refreshed the configured `rolling-daily` catalog after the Parrot row was added. Docker allocated download and extraction blocks while VM 122's `scsi0` lacked discard and both snapshots retained older block versions. The pool reached 100 percent, QEMU paused on write failure, & Kasm disappeared behind NPM.

## Corrective Actions

1. I stopped the paused VM.
2. I rolled VM 122 back to `baseline-tiles-2026-07-28`.
3. I verified that the pool fell from 100 percent to 52.51 percent before starting the guest.
4. I started VM 122 and allowed PostgreSQL to complete automatic recovery.
5. I verified all eight Kasm services, the local API, & both NPM endpoints.
6. I left Parrot and further image expansion blocked pending storage correction.
7. I enabled `discard=on` on VM 122's existing `scsi0`, restarted it under control, & trimmed the guest filesystems.
8. I deleted the older pre-build snapshot and retained the verified baseline as VM 122's only snapshot.
9. I deleted the final 2026-07-28 baseline before the controlled retry and verified zero snapshots.
10. I stopped the catalog refresh below 70 percent, pruned seven unused images, trimmed the guest, and returned the pool to 51.46 percent.
11. I pulled only Parrot and verified its local digest.
12. I cleared the Docker Registry field on all existing Kasm workspace rows, which changed image maintenance from hourly rolling-tag checks to controlled manual pulls.
13. I verified Parrot Full, Normal, and VPN plus Debian Malware, then created `baseline-parrot-2026-07-30` as the only snapshot.

I changed no Kasm, NPM, UniFi, or Docker setting during the outage mitigation. The later prevention work changed VM 122's disk option and Kasm's per-image Docker Registry field. NPM and UniFi remained unchanged.

## Validation

All eight Kasm service containers run. Seven report Docker health `healthy`; `kasm_proxy` has no health check by design. The local Kasm API returns `{"ok":true}`.

The NPM root and health endpoint returned HTTP `200` in 31.507 ms and 31.085 ms at 22:56:13 EDT. `ssd-lvm2` reported 54.74 percent after database recovery, and the guest reported 73 GiB available on `/`.

After discard enablement, the live disk configuration read `discard=on`. `fstrim` submitted 72.7 GiB from `/`, but the pool moved from 54.91 to 54.78 percent because both snapshots still held references to old blocks. Kasm finished with all seven health checks passing, public HTTP `200` responses in 21.883 ms and 29.965 ms, & the pool at 54.80 percent.

Deleting `pre-workspace-buildout-2026-07-28` reduced the pool from 54.79 to 53.85 percent, about 2.14 GiB. The snapshot count returned one, `baseline-tiles-2026-07-28`; Kasm stayed online and both public checks returned HTTP `200`.

Deleting the last old baseline reduced the pool from 53.87 to 52.10 percent. After the bulk queue was stopped and unused Docker layers were pruned, the pool reached 51.46 percent and the guest had 77 GB free.

The controlled Parrot pull completed at digest `sha256:8dc7c7821c3e69f6e4c784851fa729773b273d72dddd736`. The pool ended at 67.44 percent and the guest retained 39 GB free. Full, Normal, VPN, and Malware lane tests passed. At snapshot creation the pool read 67.45 percent; the 01:18 EDT final readback was 68.25 percent data and 2.91 percent metadata. All eight services ran, seven health checks were healthy, and the local API returned HTTP `200`.

## Lessons

Guest `df` and host thin-pool allocation answer different questions. The guest saw free logical filesystem blocks; Proxmox had no free physical thin blocks after accounting for the current disk and two snapshot generations.

The existing 80 percent action threshold had no alert behind it. `dmeventd` logged 90 and 95 percent warnings, but nothing stopped the Parrot pull before the pool reached 100 percent.

Discard returns an unused guest block only when no retained snapshot still references it. Enabling discard worked, but the 72.7 GiB guest trim released about 0.13 percentage points from the pool while both 2026-07-28 snapshots remained.

Kasm's registry field is an update policy, not only a credential location. Leaving it set on 31 definitions told the agent to inspect all moving tags. Clearing it keeps local launches working and makes the next update an explicit maintenance action.

Docker's image-inspection size did not predict ext4 consumption. Parrot reported 13.67 GB there but occupied about 38 GB in the guest after expansion. Both guest and thin-pool headroom belong in the gate.

## Follow-Ups

| Action | Status |
|---|---|
| Keep Parrot and new workspace images blocked until storage correction passes | Complete: Parrot installed under the measured gate; current state blocks another new image |
| Decide which snapshots remain on `ssd-lvm2` | Complete: retain only `baseline-parrot-2026-07-30` |
| Enable discard, reboot under control, run `fstrim`, & measure reclaimed blocks | Complete: 54.91 to 54.78 percent immediately after trim |
| Add a thin-pool alert below the 80 percent action threshold | Dropped 2026-08-06: I decided against building the alert. The manual 80 percent hard stop and the image-install gate stand on their own |
| Use guest free space and thin-pool `data_percent` for future image-install gates | Complete: require pool at or below 55 percent and at least 70 GB guest free before a new image |
| Stop unattended moving-tag refreshes | Complete: Docker Registry is null on all Kasm workspace rows |
| Add and verify Parrot Full, Normal, VPN, and Debian Malware | Complete |
| Verify the restored Kasm and NPM paths | Complete |

## Closure Status

ASU-KASM-20260729-001 is closed. Kasm is available, discard is enabled, automatic catalog pulls are disabled, the manual capacity gate is recorded, and one verified baseline remains. I dropped the automated thin-pool alert on 2026-08-06 and closed the Kasm backlog with it, so the manual 80 percent hard stop is the standing control rather than an interim one. The pool stood at 69.90 percent on 2026-08-04.

## Linked Records

- [Kasm Thin Pool Exhaustion Paused VM 122](../../../Platforms/Kasm%20Workspaces/Documentation/Troubleshooting/Kasm%20Thin%20Pool%20Exhaustion%20Paused%20VM%20122%20-%202026-07-29.md)
- [Evidence index](Evidence/Thin%20Pool%20Exhaustion%20-%202026-07-29/Evidence-Index.md)
- [Kasm Parrot Workspace Build-Out - 2026-07-30](../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30.md)
