# Galaxy TODO

**Created:** 2026-07-14  
**Last updated:** 2026-11-09

Open Galaxy work only. Closed sections are listed in the root [COMPLETED](../../../../COMPLETED.md) file with links to their change records, and the root [TODO](../../../../TODO.md) links here.

## I219 Transmit Hang Prevention

**Status:** Open after the 2026-10-14 outage; I recovered Purple on 2026-10-15 with a physical power cycle. TSO, GSO and GRO have been off on `nic0` on Purple, Green and Red since 2026-10-15, confirmed after a reboot on each, and on Blue since its move to an M920q on 2026-11-09; the other preventive changes are not yet applied.  
**Incident:** [Purple Server NIC Transmit Hang](../../../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md)  
**Troubleshooting record:** [e1000e Transmit Hang on purple-server](Troubleshooting/e1000e%20Transmit%20Hang%20on%20purple-server%20-%202026-10-14.md)

- [x] Disable TSO, GSO and GRO persistently on `nic0` on Purple, Green and Red. On 2026-10-15 I added `post-up /sbin/ethtool -K nic0 tso off gso off gro off` to each node's `nic0` stanza and applied it with `ifup nic0` without a link drop. [Change record](Change%20Records/nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md). This is a community workaround, not a vendor fix.
- [x] Confirm `ethtool -k nic0` reads TSO, GSO and GRO off after a reboot. Green, Red and Purple all did on 2026-10-15 ([verification](Change%20Records/nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md#after-reboot-verification)).
- [x] Carry the workaround to Blue's M920q. On 2026-11-09 I added the same `post-up` line to Blue's `nic0` stanza and applied it live; `ethtool -k nic0` read all three off. [Chassis swap](../../../Hardware/Documentation/Change%20Records/Blue%20Chassis%20Swap%20and%20Green%20Memory%20Upgrade%20-%202026-11-09.md#step-6-nic0-offloads-on-blue).
- [ ] I need to check Lenovo for a newer M920q BIOS/ME firmware than `M1UKT45A` dated 2019-07-11.
- [ ] I need a NIC watchdog on Purple, Green, Red and Blue: a systemd timer that pings the MGMT-A gateway `192.168.70.1` and, after about a minute of failures, bounces `nic0` and logs that it did. On 2026-10-14 the hang never cleared by itself and lasted 50 minutes 36 seconds until the power button; I have not yet tested whether a bounce clears it, so the watchdog has to log the result and fall back to a reboot if the link stays dead.
- [ ] I need out-of-band power control on the M920q nodes for failures a watchdog can't handle. The AMT SOL controller is present at `00:16.3`, but I have no provisioning record and treat AMT as unprovisioned.
- [ ] I need to consider a second physical NIC, USB or M.2 A+E, for Corosync link1 so both links no longer share one NIC and cable.
- [ ] I need to watch Purple, Green, Red and Blue for `e1000e` / `Detected Hardware Unit Hang`, record any recurrence against this incident, and widen the `post-up` line to every offload if it returns.

LAN/public Minecraft, TeamSpeak and TS3 Manager checks passed on 2026-10-15. Minecraft's external DNS failure was corrected by a container restart, and I [pinned its DNS server](../../../../Platforms/Minecraft/Documentation/Change%20Records/Pinned%20DNS%20Resolver%20-%202026-10-15.md) the same morning so the boot race can't recur.

## <a id="green-memory-repair-and-win11-dev-provisioning"></a>Green Memory Repair

**Status:** Done 2026-10-28. Single-module tests traced the errors to the SK Hynix module, which failed in both slots. I removed it, and Green ran on the 8 GB Micron module alone until a second Micron module brought it back to 16 GB on 2026-11-09.  
**Troubleshooting record:** [Memory Test Failures on green-server](Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md)

- [x] Reproduce the fault on the empty host and check temperatures, NVMe health, firmware and module layout. The [2026-09-27 diagnosis](Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md#component-diagnosis-on-2026-09-27) records the failure and isolation plan.
- [x] Isolate the faulty module or slot. The SK Hynix failed alone in both slots on 2026-10-28 and the Micron passed 20 minutes; the [single-module tests](Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md#sk-hynix-alone-in-channelb-dimm0) hold the readback. The 2026-08-09 [cross-process fault record](Troubleshooting/Status%20Unknown%20and%20Cross-Process%20Faults%20on%20green-server%20-%202026-08-09.md) left the hardware cause unproven; the 2026-09-20 online test then produced 25 failure lines.
- [ ] Replace the SK Hynix with a compatible 8 GB DDR4-2666 SO-DIMM and test the pair before raising Green back to 16 GB. On 2026-11-09 a second Micron `8ATF1G64HZ-2G6E1` went into `ChannelB-DIMM0` and Green reports 15.46 GiB; the pair is under a 12 GiB `memtester` pass, and I close this item when it finishes clean. [Chassis swap](../../../Hardware/Documentation/Change%20Records/Blue%20Chassis%20Swap%20and%20Green%20Memory%20Upgrade%20-%202026-11-09.md#memory-test).

## Blue Chassis Swap Follow-ups

**Status:** Open, from the 2026-11-09 [chassis swap](../../../Hardware/Documentation/Change%20Records/Blue%20Chassis%20Swap%20and%20Green%20Memory%20Upgrade%20-%202026-11-09.md)

- [ ] Buy two 8 GB DDR4 SO-DIMMs for Blue, test them, and replace its 2 GB and 4 GB modules. Blue is the only node under 15 GiB.
- [ ] Identify the M.2 drive that came with the M920q, record its model and capacity, and read its SMART data into the [drive inventory](../../../Hardware/Components/Drives/README.md) before it holds anything.
- [ ] Reboot Blue at the next maintenance window and confirm `ethtool -k nic0` still reads TSO, GSO and GRO off.
- [ ] Regenerate the Galaxy cluster and homelab overview diagrams. `galaxy_cluster.py` and `homelab_overview.py` still give Blue an i5-7500T with 5.68 GiB and Green 7.60 GiB.
- [ ] Decide whether to remove Blue's `50-pmx-nic1.link` and `iface nic1 inet manual` stanza, which match no interface on the M920q.

## win11-dev Activation

**Status:** Done. On 2026-10-30 Windows reported a retail licence with `LicenseStatus 1` ([Phase 1 Build](../../../../Platforms/CI%20Runners/Documentation/Change%20Records/Phase%201%20Build%20-%202026-10-30.md)). VM 103 runs on Grey since 2026-09-23. [Completion record](Change%20Records/win11-dev%20Completion%20-%202026-09-21.md), [migration record](Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md).

- [x] Activate Windows with a valid license.

## Scope of the `galaxy-pxe-join` Key

**Status:** Open, found 2026-08-15 while repairing Grey's root key file  
**Troubleshooting record:** [Broken Node Shell and Standalone authorized_keys on grey-server](Troubleshooting/Broken%20Node%20Shell%20and%20Standalone%20authorized_keys%20on%20grey-server%20-%202026-08-15.md)

- [ ] Decide whether `galaxy-pxe-join` stays trusted for root on all five nodes or is re-scoped to `grey-server` alone. On 2026-07-31 that key was trusted on Grey only, and [Galaxy Artifact Cleanup and Green SSH Parity](../../../../Operations/Maintenance/Galaxy%20Artifact%20Cleanup%20and%20Green%20SSH%20Parity%20-%202026-07-31.md) records the standalone `authorized_keys` on Grey as the mechanism that kept it that way, calling a widening to five nodes a downgrade. The key was already in `/etc/pve/priv/authorized_keys` before the 2026-08-15 repair, so it reached all five nodes while the file that was supposed to scope it had stopped doing so. Symlinking Grey's file on 2026-08-15 removed that mechanism for good. Its private half is what lets a newly installed node run `pvecm add --use_ssh`, and `cluster_peer: 192.168.70.10` in the PXE registry means only Grey needs to accept it. Re-scoping it means holding it outside the cluster-backed file, which is the arrangement that just caused a silent divergence, so the decision is which of the two costs to carry.

## Records to Complete

**Status:** Open, found 2026-09-24 during the inventory readback

- [ ] Capture the live five-node `config_version: 9` `corosync.conf` into [Configuration/Corosync](../Configuration/Corosync/README.md). The tracked copy is the four-node version 8 file.
- [ ] Date the HA removal, the monitor-01 rootfs resize and the HQ-WS001 memory change from the task logs under `/var/log/pve/tasks/` on `grey-server` and `blue-server`, and add the dates to their [change records](Change%20Records/).
- [ ] Find what released about 200 GiB on `hddpool-1` between 2026-09-06 (82.46%) and 2026-09-24 (70.7%). [Nodes](../../../Hardware/Nodes.md#cluster-storage).
