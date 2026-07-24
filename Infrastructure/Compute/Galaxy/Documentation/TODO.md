# Galaxy TODO

**Created:** 2026-07-14  
**Last updated:** 2026-07-24

This backlog contains Purple's failed boot NVMe, the deferred `pvestatd` issue, and the accepted-risk cluster maintenance done during the earlier Kasm prep. The root [TODO](../../../../TODO.md) links here without copying detailed implementation steps.

## `purple-server` Failed NVMe Health Assessment

**Status:** Replacement underway. Purple went offline on 2026-07-24 for the planned NVMe swap, so Galaxy is running on three of four votes against an expected three.  
**Troubleshooting record:** [Purple NVMe Reliability Failure](Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md)

- [x] Choose whether the failed device blocks Kasm placement. Moot after the 2026-07-23 teardown removed the Kasm guests from Purple.
- [x] Take Purple offline for the NVMe replacement. Done 2026-07-24. Corosync showed nodeid 2 `disconnected` on both links, consistent with a powered-down node.
- [ ] Avoid taking Grey, Blue, or Red offline until Purple rejoins. With Purple down, quorum sits at exactly three of three available votes, so one more node leaves the cluster inquorate.
- [ ] Monitor Purple for new media errors, filesystem errors, controller resets, or cluster instability once it returns.
- [x] Reassess the remaining rolling reboot order after the failed-device risk is removed or explicitly accepted.
- [ ] After replacement, verify storage, Proxmox VE 9.2.5, kernel, bridges, Corosync, HA, and a controlled reboot.

## Cluster Maintenance Done During Kasm Prep

**Status:** Complete. All four nodes run Proxmox VE 9.2.5. I removed the preflight change record from the repository on 2026-07-23 while rebuilding Kasm from scratch; a copy is in the cleanup backup outside the repository.

- [x] Capture and verify root-only Proxmox configuration archives on Grey, Purple, Blue, and Red.
- [x] Record that I waived the guest-backup target and accepted that the node-local configuration archives cannot restore guest disks.
- [x] Update guest-free Purple to Proxmox VE 9.2.5 and verify quorum, HA, services, storage, networking, and package state after reboot.
- [x] Resume and finish the one-node-at-a-time updates. Red, Grey, and Blue reached Proxmox VE 9.2.5 on 2026-07-23 after I accepted the Purple risk.

## `blue-server` Recurring `pvestatd` Crashes

**Status:** Deferred known issue  
**Priority:** Schedule with a maintenance window  
**Troubleshooting record:** [Recurring `pvestatd` failure on `blue-server`](Troubleshooting/Recurring%20pvestatd%20Failure%20on%20blue-server%20-%202026-07-13.md)

- [ ] Recheck service, cluster, kernel, & package state before recovery; retain the failure window and a core dump if one becomes available.
- [ ] Record the current Lenovo BIOS settings, confirm the M910q update and rollback procedure, & update BIOS from `M1AKT35A` during a maintenance window.
- [ ] Run an extended offline memory test after the firmware review; record per-pass results and any failing address or module information.
- [ ] If memory passes, run a fixed-duration CPU test plus storage health & integrity checks, then compare the results with the other Galaxy nodes.
- [ ] Restore `pvestatd`, verify node and resource status from a peer, & monitor for another crash beyond the prior failure window.
- [ ] After finding the root cause, decide whether a systemd restart policy should cover a later daemon crash.

A manual restart isn't resolution. Previous restarts restored status, then `pvestatd` failed again.
