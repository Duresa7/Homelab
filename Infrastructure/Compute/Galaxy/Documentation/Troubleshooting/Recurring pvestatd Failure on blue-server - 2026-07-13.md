# Recurring `pvestatd` Failure on `blue-server`

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**First retained occurrence:** 2026-06-19  
**Investigated:** 2026-07-13  
**Owner:** Galaxy / Proxmox  
**Status:** Known issue; I deferred the corrective work

## Symptom and impact

The Proxmox cluster resource view reported `blue-server` with status `unknown`, while the host, its guests, and cluster communications remained online. Blue remained reachable over SSH, reported healthy CPU, memory, disk, and network metrics, and had more than two weeks of uptime. Corosync reported all four nodes present and the cluster quorate.

The loss of status was limited to the node and resource information normally published by `pvestatd`. It did not stop the hypervisor or its running workloads.

## Exact failure

`pvestatd.service` was failed with `Result=signal`, `ExecMainStatus=11`, and `signal=SEGV`. The most recent retained crash occurred at `2026-07-11 15:50:35 EDT` inside the Perl runtime. The unit declares `Restart=no`, so the daemon remained stopped after the crash and Proxmox continued to show the node as unknown.

The retained journal shows four failures since the Proxmox 9 installation:

| Date and time (EDT) | Result | Relevant observation |
|---|---|---|
| 2026-06-19 17:42:16 | `SIGSEGV` | Fault in Perl at executable offset `0x1a76f6` |
| 2026-06-24 03:52:39 | `SIGABRT` | Occurred just after the daily PVE package-list update; causation is not established |
| 2026-07-05 07:50:09 | Exit status `1` | Preceded by uninitialized `$upid` warnings in `PVE/RESTEnvironment.pm` |
| 2026-07-11 15:50:35 | `SIGSEGV` | Same Perl executable offset `0x1a76f6` as the June 19 crash |

The repeated fault offset maps to `Perl_newSVhek`, where Perl attempted to read an invalid internal pointer. This is consistent with memory corruption but does not by itself distinguish a software defect from firmware, CPU, or RAM instability.

## Tests and findings

- `pve-cluster`, `corosync`, `pvedaemon`, and `pveproxy` were running; only `pvestatd` was stopped among the Proxmox services I checked.
- Grey, Purple, and Red ran the same relevant Proxmox and Perl versions and had no comparable retained `pvestatd` failures.
- Blue's relevant installed package files passed `dpkg -V`; the only reported modification was its expected APT source configuration file.
- I found no OOM kill, filesystem or NVMe error, machine-check event, or EDAC error in the retained logs.
- No retained core dump was available. The host has no `coredumpctl`, and no matching core file was found.
- Intel microcode was current at the time of inspection.
- Blue is a Lenovo ThinkCentre M910q with BIOS `M1AKT35A` dated 2018-03-21. Lenovo identifies `M1AKT36A` as a corrected minimum for this model family and publishes the newer `M1AKT5AA`; firmware age is therefore a material lead, not a confirmed cause.
- Similar recurring `pvestatd`/Perl crashes have been reported to Proxmox. Proxmox staff guidance for this failure pattern includes package verification, firmware and microcode review, and extended CPU/RAM testing. Package verification and the live log review did not expose a software-installation or disk fault on Blue.
- Repeating `ip6tables-restore` errors from `pve-firewall` were present near the latest crash. They continued independently and are not presently linked to the `pvestatd` segmentation fault.

## Confirmed failure and open cause

The immediate cause of the unknown Proxmox status is confirmed: `pvestatd` crashed and its unit does not restart automatically. The deeper cause remains open. Blue-specific firmware or hardware instability is my leading hypothesis because the failures recur only on this node, include allocator-pointer corruption and an abort, and the BIOS predates Lenovo's corrected minimum. A node-specific Proxmox/Perl code path remains possible because only `pvestatd` has been observed crashing.

I performed no service restart, firmware change, stress test, offline memory test, or configuration change during this investigation.

## Deferred follow-up

The controlled follow-up is tracked in the [Galaxy TODO](../TODO.md#blue-server-recurring-pvestatd-crashes). It should begin with evidence capture and non-disruptive integrity checks, then use an approved maintenance window for BIOS work and extended offline memory testing.

## Related records

- I recorded the first operational discovery and temporary restart in the [NetBird troubleshooting record](../../../../../Platforms/Netbird/Documentation/Troubleshooting/pvestatd%20Was%20Failed%20on%20blue-server%20-%202026-07-10.md).
- Lenovo BIOS notice: <https://support.lenovo.com/us/en/solutions/ht507019-new-recommended-version-of-system-bios-available-for-thinkcentre-all-m700-m710q-m800-m900s-m900t-all-m910-and-thinkstation-p320-tiny-systems>
- Lenovo M910q BIOS package: <https://pcsupport.lenovo.com/it/it/products/desktops-and-all-in-ones/thinkcentre-m-series-desktops/thinkcentre-m910q/downloads/ds120436>
- Proxmox discussion of the recurring crash pattern: <https://forum.proxmox.com/threads/pvestatd-segfaults.170897/>
