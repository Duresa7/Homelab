# Galaxy TODO

**Created:** 2026-07-14  
**Last updated:** 2026-07-27

This backlog contains the scheduled CT 105 deletion, follow-ups from Purple's boot NVMe replacement, the deferred `pvestatd` issue, & the accepted-risk cluster maintenance done during the earlier Kasm prep. The root [TODO](../../../../TODO.md) links here without copying detailed implementation steps.

## `ai-bravo-02` Deletion Scheduled

**Status:** Stopped, autostart disabled, & archived 2026-07-25  
**Deletion date:** 2026-08-15  
**Archive record:** [ai-bravo-02 Archived Guest](../../../../Archive/Operations/Inventory/Galaxy/AI%20Bravo%2002%20Archived%20Guest%20-%202026-07-25.md)

- [ ] On 2026-08-15, confirm CT 105 is still stopped & `onboot` remains `0`.
- [ ] Read the archived guest record, TNIO platform tree, walkthrough, & diagrams before deleting the guest.
- [ ] Identify any guest backup retained outside this repository & record its location or record that no restorable backup exists.
- [ ] Capture the final `pct config 105` output without private values, then delete CT 105 & its `ssd-lvm1:vm-105-disk-0` root volume.
- [ ] Confirm guest ID 105 & hostname `ai-bravo-02` are absent from cluster resources, configuration, storage, DNS, DHCP, SSH Manager, local SSH state, & active automation.
- [ ] Update the archive record from stopped & archived to deleted & retired, with the observed deletion result.

## `purple-server` Boot NVMe Replaced

**Status:** Hardware issue closed 2026-07-25. A Toshiba THNSF5256GPUK cloned from the failing Samsung is Purple's boot device, health `PASSED`, and Galaxy is back to four of four votes.  
**Change record:** [Purple Boot NVMe Replacement](Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md)  
**Troubleshooting record:** [Purple NVMe Reliability Failure](Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md)

- [x] Choose whether the failed device blocks Kasm placement. Moot after the 2026-07-23 teardown removed the Kasm guests from Purple.
- [x] Take Purple offline for the NVMe replacement. Done 2026-07-24. Corosync showed nodeid 2 `disconnected` on both links, consistent with a powered-down node.
- [x] Avoid taking Grey, Blue, or Red offline until Purple rejoins. Held for the whole 19-hour-33-minute window; Purple rejoined at `07:19:56 EDT` on 2026-07-25 and the cluster is back to four votes.
- [x] Reassess the remaining rolling reboot order after the failed-device risk is removed or explicitly accepted.
- [x] After replacement, verify storage, Proxmox VE 9.2.5, kernel, bridges, Corosync, HA, and a controlled reboot. The cold boot off the cloned drive is the reboot check: `local` and `local-lvm` active, `pve-manager/9.2.5/20242970da7fbcef` on kernel `7.0.14-6-pve` with nothing pending, both rings connected, all seven units active, fencing armed.
- [ ] Watch the Toshiba's endurance counter along with media errors, filesystem errors, controller resets, and cluster stability. It's a used spare at 30% endurance used and 23,148 power-on hours, not a new drive, so plan its own replacement rather than treating this as permanent.
- [x] Keep the Samsung SSD 850 EVO 250 GB installed permanently and use it as ordinary Proxmox storage for VM disks and LXC root volumes. I made that role decision on 2026-07-27.
- [ ] Wipe the empty 16 MiB partition, create the storage layout, add it to Proxmox with VM image and LXC root-directory content enabled, and verify a test guest disk can be created and removed. The disabled `ssd-lvm1` entry predates this drive and must not be reused without confirming its backing device.

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
