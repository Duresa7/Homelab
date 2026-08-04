# Recurring `pvestatd` Failure on `blue-server`

**Created:** 2026-07-22  
**Last updated:** 2026-08-04

**First retained occurrence:** 2026-06-19  
**Investigated:** 2026-07-13  
**Owner:** Galaxy / Proxmox  
**Status:** Open, quiescent since 2026-07-22; cause still unestablished

## Correction, 2026-08-04

**I briefly closed this record against the wrong fault, and I am reopening it.** The reasoning was that the duplicate `pve` volume group found on 2026-07-30 explained the crashes. It does not. That disk was installed shortly before the 2026-07-30 shutdown, so a duplicate volume group that did not exist in June cannot explain a June crash. What the duplicate VG did explain is a different symptom: ten-second `activating LV 'pve/data' failed` messages from a `pvestatd` that was running fine otherwise. Those are fixed and confirmed gone. This record is about the daemon being killed, which is not the same thing.

I am recording the mistake rather than quietly reverting it, because the two faults share a daemon name and will invite the same conflation next time. The distinguishing test is simple: this fault terminates the process, and with `Restart=no` the node goes `unknown`; the other leaves it up and merely noisy.

The correction also surfaced **a fifth crash that this record never listed**, on 2026-07-22 at 22:13:26 EDT, same `status=11/SEGV`. The retained journal now only reaches back to 2026-07-09, so the June occurrences survive only in the table below. That is the argument for having written them down.

Live state on 2026-08-04: `pvestatd` `active`, `Result=success`, `NRestarts=0`, running since `2026-08-01 11:11:21 EDT`, and no `SIGSEGV` or `SIGABRT` in the journal since 2026-07-22.

**Thirteen days without a crash is not a fix.** The five retained crashes span 2026-06-19 to 2026-07-22, a mean interval of about eight days, so the current quiet period is under twice that. Nothing was changed on Blue that would plausibly have fixed it: no BIOS update, no memory test, no microcode change, no `pvestatd` configuration change. The firmware lead below is still the leading hypothesis and is still untested.

## Retained crash occurrences

| Date and time (EDT) | Result | Relevant observation |
|---|---|---|
| 2026-06-19 17:42:16 | `SIGSEGV` | Fault in Perl at executable offset `0x1a76f6` |
| 2026-06-24 03:52:39 | `SIGABRT` | Occurred just after the daily PVE package-list update; causation is not established |
| 2026-07-05 07:50:09 | Exit status `1` | Preceded by uninitialized `$upid` warnings in `PVE/RESTEnvironment.pm` |
| 2026-07-11 15:50:35 | `SIGSEGV` | Same Perl executable offset `0x1a76f6` as the June 19 crash |
| 2026-07-22 22:13:26 | `SIGSEGV` | Added 2026-08-04; postdates this record's original investigation |

## Symptom and impact

The Proxmox cluster resource view reported `blue-server` with status `unknown`, while the host, its guests, and cluster communications remained online. Blue remained reachable over SSH, reported healthy CPU, memory, disk, and network metrics, and had more than two weeks of uptime. Corosync reported all four nodes present and the cluster quorate.

The loss of status was limited to the node and resource information normally published by `pvestatd`. It did not stop the hypervisor or its running workloads.

## Exact failure

`pvestatd.service` was failed with `Result=signal`, `ExecMainStatus=11`, and `signal=SEGV`. The most recent retained crash occurred at `2026-07-11 15:50:35 EDT` inside the Perl runtime. The unit declares `Restart=no`, so the daemon remained stopped after the crash and Proxmox continued to show the node as unknown.

At the time of this investigation the journal showed four failures since the Proxmox 9 installation. A fifth followed on 2026-07-22. All five are in the Retained crash occurrences table above.

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

## Original 2026-07-13 finding

The immediate cause of the unknown Proxmox status was confirmed at the time: `pvestatd` crashed and its unit did not restart automatically. The deeper cause had not yet been established. Blue-specific firmware or hardware instability was my leading hypothesis because the retained failures occurred only on this node, included allocator-pointer corruption and an abort, and the BIOS predated Lenovo's corrected minimum. A node-specific Proxmox/Perl code path also remained possible because only `pvestatd` had been observed crashing.

I performed no service restart, firmware change, stress test, offline memory test, or configuration change during this investigation.

## Original deferred follow-up

I track a controlled follow-up in the [Galaxy TODO](../TODO.md#blue-server-recurring-pvestatd-crashes), beginning with evidence capture and non-disruptive integrity checks before any BIOS work or extended offline memory testing. **That plan is still live.** The 2026-08-04 review confirmed the crashes have not recurred since 2026-07-22 but changed nothing on Blue, so nothing in it has been retired.

## Related records

- I recorded the first operational discovery and temporary restart in the [NetBird troubleshooting record](../../../../../Platforms/Netbird/Documentation/Troubleshooting/pvestatd%20Was%20Failed%20on%20blue-server%20-%202026-07-10.md).
- Lenovo BIOS notice: <https://support.lenovo.com/us/en/solutions/ht507019-new-recommended-version-of-system-bios-available-for-thinkcentre-all-m700-m710q-m800-m900s-m900t-all-m910-and-thinkstation-p320-tiny-systems>
- Lenovo M910q BIOS package: <https://pcsupport.lenovo.com/it/it/products/desktops-and-all-in-ones/thinkcentre-m-series-desktops/thinkcentre-m910q/downloads/ds120436>
- Proxmox discussion of the recurring crash pattern: <https://forum.proxmox.com/threads/pvestatd-segfaults.170897/>
