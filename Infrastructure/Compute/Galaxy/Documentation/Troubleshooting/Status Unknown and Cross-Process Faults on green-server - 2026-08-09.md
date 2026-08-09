# Status Unknown and Cross-Process Faults on `green-server`

**Created:** 2026-08-09  
**Last updated:** 2026-08-09

**First retained occurrence:** 2026-08-08  
**Investigated and mitigated:** 2026-08-09  
**Owner:** Galaxy / Proxmox  
**Status:** Mitigated; hardware cause remains open

## Symptom and impact

The Proxmox cluster resource view reported `green-server` with status `unknown` while the host, CT 123 `game-01`, Corosync, and the other core Proxmox services remained online. Green still participated in the five-vote quorate cluster.

The loss of status came from `pvestatd` being stopped. A second failure also left `pve-firewall` stopped, so this was not only a cosmetic node-status problem. The existing rules remained loaded, but the legacy firewall daemon could not apply later changes while it was down.

## Exact failures

`pvestatd.service` aborted at 4:56:03 PM EDT on 2026-08-08 with `Result=signal`, `ExecMainStatus=6`, and `SIGABRT`. The unit declares `Restart=no`, so it stayed failed and Green's resource status became `unknown`.

The journal immediately before the abort included `sdn status update error: malformed JSON` from `PVE/Network/SDN/Zones.pm` line 200. That code consumes the JSON emitted by `ifquery -a -c -o json`.

`pve-firewall.service` then crashed at 6:49:47 AM EDT on 2026-08-09 with `Result=signal`, `ExecMainStatus=11`, and `SIGSEGV`. Its journal had repeated `status update error: unable to apply firewall changes` messages before the crash.

The same boot contained 37 kernel-recorded user-space faults from 2026-08-08 onward: 27 in `python3`, nine in `php`, and one in `pve-firewall`. The faults occurred at different instruction and memory addresses across all six CPU cores and involved Python 3.13, libc, musl's loader, Perl, and PHP. That cross-process pattern is the evidence that separates this event from an isolated `pvestatd` software fault.

## Tests and findings

- The tight status check ran from `grey-server` against `/cluster/resources`. It returned `green-server-status=unknown` and exit status 1 before the repair.
- Green was otherwise healthy: low CPU load, 10 percent root-filesystem use, working networking, CT 123 running, and five-vote quorum. `pve-cluster`, Corosync, `pvedaemon`, `pveproxy`, and HA remained active.
- Grey, Purple, Blue, and Red were on the same Proxmox VE 9.2.6 and `7.0.14-8-pve` kernel level. They recorded no comparable Python, PHP, Perl, or firewall faults during the same boot interval. Green recorded 37.
- `dpkg -V` found no unexpected changes in Python 3.13, libc, Perl, ifupdown2, `pve-firewall`, or `pve-manager`. The only reported missing path was the deliberately absent enterprise APT source.
- The current `ifquery -a -c -o json` output parsed successfully in 20 repeated pre-repair checks. The malformed output was intermittent rather than a persistent interface configuration error.
- The kernel reported no OOM kill, NVMe I/O fault, machine-check event, or EDAC error. Green's boot NVMe reported zero media errors and no critical warning. The separate Hitachi SATA HDD is known bad but blank and unused.
- The current boot had no recorded process faults before CT 123 started at 4:04:34 PM EDT on 2026-08-07. The first occurred at 4:04:01 AM EDT on 2026-08-08 after the workload began using memory above Green's former 8 GB capacity. This is correlation, not proof.
- Green has a Micron 8 GB `8ATF1G64HZ-2G6E1` module and an SK Hynix 8 GB `HMA81GS6CJR8N-VK` module running together at 2666 MT/s. The SK Hynix module moved from Blue to Green on 2026-07-31. Neither module provides ECC reporting.

## Online memory test

I installed Debian's `memtester` 4.7.1-1 and ran two passes over a locked 1 GiB allocation while CT 123 remained online. I bounded the transient service to 1.4 GB, disabled its swap allocation, and set a 15-minute runtime limit. I watched available memory, swap, the current-boot fault count, and CT 123 throughout the run.

The first transient wrapper failed with exit status 2 because its nested shell variables were expanded before `systemd-run` started it. `memtester` did not execute in that attempt, no memory was allocated, and the fault counter stayed at 37. I replaced the wrapper with a direct transient unit running `/usr/sbin/memtester 1024M 2`.

The direct run locked the full 1 GiB, completed both passes, printed `Done.`, and exited 0. Every completed subtest reported `ok`. Available memory stayed near 5.8 GiB, swap use stayed below 1 MiB, CT 123 remained running, and the kernel fault count stayed at 37.

This clears only the tested allocation. A userspace test cannot cover pages held by the kernel, Proxmox, or running guests, and it cannot map an error to one physical module. The clean result therefore does not disprove intermittent RAM, memory-controller, motherboard, CPU, or mixed-module instability.

No separate terminal transcript was retained. The result above comes from the live transient-unit status, journal summary, service state, and current-boot fault counter read immediately after the test.

## Mitigation and reboot

`pve-firewall compile` exited 0 before I restarted any service. I restarted `pvestatd` first. It became active at 1:11:42 PM EDT, and the same cluster status check that had failed immediately returned `green-server-status=online`.

I then restarted `pve-firewall`. It became active at 1:12:01 PM EDT and reported `Status: enabled/running` without a new update error.

After confirming CT 123 had `onboot: 1`, I issued a normal reboot. Proxmox took several minutes to shut the guest down gracefully. I did not force-reset the node. The previous boot reached `reboot.target`, stopped its journal at 1:17:05 PM EDT, and Green returned on the same `7.0.14-8-pve` kernel. CT 123 started automatically.

## Verification

- Green rejoined Corosync as node 5 on both cluster links, Galaxy remained quorate with five votes, and the cluster API reported the node `online` in three consecutive checks.
- `pvestatd`, `pve-firewall`, `proxmox-firewall`, `pve-cluster`, Corosync, `pvedaemon`, `pveproxy`, and SSH all reported active after the reboot.
- `pve-firewall status` reported `enabled/running`.
- `pve-firewall` logged two startup update errors at 1:17:54 PM and 1:18:05 PM EDT because another process held the xtables lock. They stopped after startup, the daemon remained active, and no current-boot log reproduced the malformed JSON, abort, or segmentation fault.
- CT 123 `game-01` returned automatically and its health check passed with 19.1 percent CPU use, 51.81 percent memory use, and 7 percent root-filesystem use.
- The new boot's kernel fault count was 0.
- A one-minute post-boot loop completed 12 of 12 samples. Each sample found zero kernel faults, all three status and firewall daemons active, CT 123 running, and valid JSON from `ifquery` parsed through Python.
- The original status check now passes. Green no longer reports `unknown`.

## Root cause and remaining work

The immediate root cause of the `unknown` status is confirmed: `pvestatd` aborted and did not restart. Restarting that daemon changed the original red check to green.

The cause of the memory corruption remains unconfirmed. My leading hypothesis is instability in Green's physical memory path, with the SK Hynix module added on 2026-07-31 or the mixed Micron and SK Hynix pair first. The prediction is that an extended bootable memory test or single-module isolation will reproduce errors with one module or one pairing. Firmware, the CPU memory controller, and the motherboard remain alternatives. A Green-specific software defect is less likely because unrelated Python, PHP, Perl, and firewall processes faulted at varied addresses while four matching Proxmox nodes did not.

The next conclusive step is an offline Memtest86+ run across the full 16 GB. Any error is actionable. If it reports one, I will power Green down and test the modules individually, beginning with removal of the added SK Hynix module. Until that test is complete, a clean reboot and zero current faults are mitigation, not proof of repaired hardware.

## Related records

- [Galaxy Green and Blue Hardware Changes](../../../../Hardware/Documentation/Change%20Records/Galaxy%20Green%20and%20Blue%20Hardware%20Changes%20-%202026-07-31.md)
- [Recurring `pvestatd` Failure on `blue-server`](Recurring%20pvestatd%20Failure%20on%20blue-server%20-%202026-07-13.md)
