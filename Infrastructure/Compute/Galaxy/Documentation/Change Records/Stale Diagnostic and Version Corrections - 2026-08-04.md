# Stale Diagnostic and Version Corrections

**Created:** 2026-08-04  
**Last updated:** 2026-08-04

**Change date:** 2026-08-04  
**Scope:** Galaxy diagnostic records, `ssd-lvm2` interpretation, Portainer CE version, and NetBird dashboard version  
**Status:** Complete

## What I changed

I separated two `blue-server` `pvestatd` faults that had been treated as one, having first conflated them myself and closed the wrong item before catching it the same day.

The ten-second `activating LV 'pve/data' failed` messages were a symptom of the duplicate `pve` volume-group name fixed on 2026-07-30. Those are resolved, and I added the 2026-08-04 confirmation to the existing [duplicate-VG troubleshooting record](../Troubleshooting/Duplicate%20pve%20Volume%20Group%20on%20blue-server%20-%202026-07-30.md) without replacing its original diagnosis.

The recurring `SIGSEGV` crashes are a different fault and **remain open**. The disk carrying the duplicate volume group was installed shortly before the 2026-07-30 shutdown, so it cannot explain the crash retained from 2026-06-19. I reopened [Recurring `pvestatd` Failure on `blue-server`](../Troubleshooting/Recurring%20pvestatd%20Failure%20on%20blue-server%20-%202026-07-13.md), added a fifth crash on 2026-07-22 that it had never listed, and restored the deferred BIOS and memory-test plan I had wrongly retired. The crashes are quiescent since 2026-07-22, which at thirteen days is under twice their roughly eight-day mean interval, and nothing was changed on Blue that would plausibly have fixed them.

The distinguishing test, recorded so the next reader does not repeat the conflation: this fault kills the daemon and `Restart=no` leaves the node `unknown`, while the other leaves it running and merely noisy.

I kept the node-scoped `pvesm status` rule in the [hardware node record](../../../../Hardware/Nodes.md#cluster-storage) and linked it from the Galaxy storage reference. `ssd-lvm2` is restricted to `purple-server`, so a `disabled` result from another node is that node's correct answer rather than an administrative disablement.

I marked Portainer CE 2.39.5 and NetBird dashboard 2.90.8 as verified on 2026-08-04 in their living platform, guide, runbook, and services records. The Portainer status endpoint is unauthenticated, and the running NetBird dashboard image carries its version in OCI labels. Neither check needed an application login.

## Verification

- `pvestatd` was `active` with `NRestarts=0` and `ActiveEnterTimestamp=Sat 2026-08-01 11:11:21 EDT`.
- Its last error of any kind was at 23:58:37 EDT on 2026-07-30, with zero errors from 2026-07-31 onward.
- Filtering the unit journal for `SEGV`, `SIGABRT`, `signal`, `Main process exited`, and `Failed with result` returned five crash events, the most recent at 2026-07-22 22:13:26 EDT with `status=11/SEGV`, and none after it. `Restart=no` and `Result=success` confirm the running process has not crashed since it started.
- The journal retains back only to 2026-07-09, so the 2026-06-19, 2026-06-24, and 2026-07-05 occurrences exist only in the troubleshooting record.
- `vgs -o vg_name,vg_uuid,pv_count` reported one `pve` volume group, UUID `bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e`, with one physical volume.
- On Purple, `ssd-lvm2` reported `active` at 69.90 percent data use. The pool's metadata use was 3.06 percent. The reverse node check showed Grey-restricted `ssd-lvm1` and `hddpool-1` as `disabled` from Purple, and `/etc/pve/storage.cfg` held no `disable` flag.
- Portainer's `https://localhost:9443/api/status` response reported `Version` `2.39.5`.
- The NetBird dashboard image reported `org.opencontainers.image.version=v2.90.8` and revision `9fab9d7a837f7b67b835fbc83e0624df1e4392a5`.
- Repository searches found no remaining record that presents the Blue `pvestatd` item as open or the `ssd-lvm2` cause as unknown. The three remaining `ssd-lvm2 disabled` lines are unchanged retained transcripts from Blue, where that node-scoped result was correct.

I made no live-system or deployment change for this record.

## What remains open

The automated Kasm thin-pool warning remains open. `ssd-lvm2` stood at 69.90 percent data and 3.06 percent metadata against the 80 percent hard stop on 2026-08-04, but this change did not build the alert.

Portainer and NetBird are still deployed from `latest` tags. On 2026-08-04 I decided to keep all 14 tracked image tags at `:latest`: automatic fixes on pull are worth more to me here than reproducible version numbers. The [version-figure rule](../../../../../README.md#version-figures) governs the figures those images report. I changed no image tag or live deployment in this documentation work.
