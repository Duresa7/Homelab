# Kasm Workspace Build-Out Evidence

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

This folder holds the command transcripts and controller read-backs for the 2026-07-28 Kasm workspace build-out.

| Step | Evidence | Result |
| --- | --- | --- |
| Phase 0 | [S00 Snapshot and Disk Growth](Logs/S00%20Snapshot%20and%20Disk%20Growth%20-%202026-07-28.md) | Snapshot created; VM disk grew from 150 GiB to 200 GiB; ext4 reports 193 GiB with 76 GiB free |
| Phase 1 | [S01 VLAN 75, Zone, and Firewall Final State](Logs/S01%20VLAN%2075,%20Zone,%20and%20Firewall%20Final%20State%20-%202026-07-28.md) | VLAN, zone, trunk admission, and all 17 policies verified; final user-defined policy count 118 |
| Phase 2 | [S02 VLAN 75 Guest and Docker State](Logs/S02%20VLAN%2075%20Guest%20and%20Docker%20State%20-%202026-07-28.md) | Fourth VirtIO NIC, addressless parent, persistent shim, and `lab75` macvlan verified |
| Phases 3 through 6 | [S03 Gate, Group, and Workspace State](Logs/S03%20Gate,%20Group,%20and%20Workspace%20State%20-%202026-07-28.md) | Gate traffic, Lab Sessions settings, six profile directories, 19 isolated workspaces, and 15 unisolated originals verified |
| Phase 7 | [S04 Acceptance, Reboot, and Cleanup](Logs/S04%20Acceptance,%20Reboot,%20and%20Cleanup%20-%202026-07-28.md) | Four real sessions passed egress and protected-target tests; reboot persistence, fresh launch, snapshots, and residue checks passed |
| Final readback | [S05 Full Final State Readback](Logs/S05%20Full%20Final%20State%20Readback%20-%202026-07-28.md) | Exact VM, storage, guest network, service, Kasm policy, workspace, profile, snapshot, and residue output retained |
| Phase 7 re-run | [S06 Lane Containment Probe Transcript](Logs/S06%20Lane%20Containment%20Probe%20Transcript%20-%202026-07-28.md) | Raw transcript for all four lanes: 36 of 36 protected probes timed out, DNS fails on 77 and 79, lane 74 exits via Proton and lane 75 via the ordinary WAN |

S04 records the Phase 7 matrix as a summary, because the sessions that produced it were destroyed before the transcript was kept. S06 re-ran the same matrix and retains the output.
