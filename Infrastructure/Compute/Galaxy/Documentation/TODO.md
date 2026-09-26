# Galaxy TODO

**Created:** 2026-07-14  
**Last updated:** 2026-09-25

Open Galaxy work only. Closed sections are listed in the root [COMPLETED](../../../../COMPLETED.md) file with links to their change records, and the root [TODO](../../../../TODO.md) links here.

## <a id="green-memory-repair-and-win11-dev-provisioning"></a>Green Memory Repair

**Status:** Open since 2026-09-20. Green holds no guests.  
**Troubleshooting record:** [Memory Test Failures on green-server](Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md)

- [ ] Isolate the faulty module or slot and run an offline memory test. The 2026-08-09 [cross-process fault record](Troubleshooting/Status%20Unknown%20and%20Cross-Process%20Faults%20on%20green-server%20-%202026-08-09.md) left the hardware cause unproven; the 2026-09-20 online test then produced 25 failure lines.
- [ ] Place no guest on Green until a full test passes.

## win11-dev Activation

**Status:** Open. VM 103 runs on Grey since 2026-09-23. [Completion record](Change%20Records/win11-dev%20Completion%20-%202026-09-21.md), [migration record](Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md).

- [ ] Activate Windows with a valid license.

## Scope of the `galaxy-pxe-join` Key

**Status:** Open, found 2026-08-15 while repairing Grey's root key file  
**Troubleshooting record:** [Broken Node Shell and Standalone authorized_keys on grey-server](Troubleshooting/Broken%20Node%20Shell%20and%20Standalone%20authorized_keys%20on%20grey-server%20-%202026-08-15.md)

- [ ] Decide whether `galaxy-pxe-join` stays trusted for root on all five nodes or is re-scoped to `grey-server` alone. On 2026-07-31 that key was trusted on Grey only, and [Galaxy Artifact Cleanup and Green SSH Parity](../../../../Operations/Maintenance/Galaxy%20Artifact%20Cleanup%20and%20Green%20SSH%20Parity%20-%202026-07-31.md) records the standalone `authorized_keys` on Grey as the mechanism that kept it that way, calling a widening to five nodes a downgrade. The key was already in `/etc/pve/priv/authorized_keys` before the 2026-08-15 repair, so it reached all five nodes while the file that was supposed to scope it had stopped doing so. Symlinking Grey's file on 2026-08-15 removed that mechanism for good. Its private half is what lets a newly installed node run `pvecm add --use_ssh`, and `cluster_peer: 192.168.70.10` in the PXE registry means only Grey needs to accept it. Re-scoping it means holding it outside the cluster-backed file, which is the arrangement that just caused a silent divergence, so the decision is which of the two costs to carry.

## Records to Complete

**Status:** Open, found 2026-09-24 during the inventory readback

- [ ] Capture the live five-node `config_version: 9` `corosync.conf` into [Configuration/Corosync](../Configuration/Corosync/README.md). The tracked copy is the four-node version 8 file.
- [ ] Date the HA removal, the monitor-01 rootfs resize and the HQ-WS001 memory change from the task logs under `/var/log/pve/tasks/` on `grey-server` and `blue-server`, and add the dates to their [change records](Change%20Records/).
- [ ] Find what released about 200 GiB on `hddpool-1` between 2026-09-06 (82.46%) and 2026-09-24 (70.7%). [Nodes](../../../Hardware/Nodes.md#cluster-storage).
