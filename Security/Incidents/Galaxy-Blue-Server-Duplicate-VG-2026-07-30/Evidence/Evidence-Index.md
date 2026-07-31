# Blue-Server Duplicate VG Evidence

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

These transcripts retain the SSH Manager commands, returned output, standard error, and exit status for the diagnosis, storage repair, destructive WDC wipe, & final workload verification.

| Step | Evidence | What it proves |
|---|---|---|
| S01 | [Diagnosis](Logs/S01%20Diagnosis%20-%202026-07-30.md) | `local-lvm` was inactive because two different VGs were named `pve`; the current guest disks stayed on the active NVMe VG. |
| S02 | [VG rename and storage recovery](Logs/S02%20VG%20Rename%20and%20Storage%20Recovery%20-%202026-07-30.md) | Renaming the inactive SATA VG by UUID made `local-lvm` active without changing the NVMe VG. |
| S03 | [WDC disk wipe](Logs/S03%20WDC%20Disk%20Wipe%20-%202026-07-31.md) | The guarded destructive command removed the stale LVM layout and GPT from the exact WDC device identity; follow-up returned a blank disk. |
| S04 | [Final verification](Logs/S04%20Final%20Verification%20-%202026-07-31.md) | The NVMe is the only LVM PV, all three LXCs and workloads run, HA is started, quorum is intact, & no activation error recurred. |

The sanitized WDC SMART output will be linked from the [drive inventory](../../../../Infrastructure/Hardware/Components/Drives/README.md) after its extended test completes.
