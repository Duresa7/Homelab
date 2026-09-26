# HQ-WS001 Memory at 8 GiB

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Observed on:** 2026-09-24  
**Status:** Recorded after the fact; the change has no earlier record  
**Affected systems:** VM 310 `HQ-WS001` on `grey-server`

## What changed

VM 310 has 8 GiB of memory and was stopped. I built it on 2026-09-10 with 4 GiB because `grey-server` was running 51 GiB of its 62 GiB at the time. [HQ-WS001 Workstation Join](../../../../../Platforms/Active%20Directory/Documentation/Change%20Records/HQ-WS001%20Workstation%20Join%20-%202026-09-10.md).

On 2026-09-24 `qm config 310` returned `memory: 8192`, `balloon: 0` and `onboot: 0`, and the cluster resource list showed the VM `stopped`. The VM was running on 2026-09-19, when I enabled SSH on it. I have no record of when the memory changed or when the VM stopped. [HQ-WS001 SSH Enablement](../../../../../Platforms/Active%20Directory/Documentation/Change%20Records/HQ-WS001%20SSH%20Enablement%20-%202026-09-19.md).

## Current state

- 4 vCPUs, 8 GiB fixed memory, ballooning off, 80G system disk on `ssd-lvm1`.
- Stopped, with `onboot: 0`, so a Grey reboot does not start it.
- Grey used 51.61 of 62.72 GiB with this VM stopped on 2026-09-24. Starting it adds 8 GiB, which leaves about 3 GiB free on Grey. I check Grey's available memory before I start it.

## Verification

The [VM inventory](../../../../../Operations/Inventory/Galaxy/VMs.md) now reads 8 GiB and stopped. Grey's task log would date the `qmconfig` and `qmshutdown` tasks; I did not read it.
