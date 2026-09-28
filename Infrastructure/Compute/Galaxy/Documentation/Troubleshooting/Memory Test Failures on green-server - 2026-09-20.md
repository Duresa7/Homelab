# Memory Test Failures on green-server

**Created:** 2026-09-20  
**Last updated:** 2026-09-27

**Status:** Confirmed memory data corruption; component isolation and repair remain open.

While installing VM 103 `win11-dev`, Windows Setup stopped with `PFN_LIST_CORRUPT (0x4E)`. Green already had a [2026-08-09 cross-process fault investigation](Status%20Unknown%20and%20Cross-Process%20Faults%20on%20green-server%20-%202026-08-09.md), when two 1 GiB online memory passes had passed and the hardware cause remained unproven. This larger test now fails independently of Windows and its drivers.

## Tests and results

I stopped VM 103 before testing. No other guest was on Green. I ran:

```sh
systemd-run --unit=win11-dev-memory-check --property=MemoryMax=10G --property=MemorySwapMax=0 --property=RuntimeMaxSec=300 /usr/sbin/memtester 8192M 1
```

`memtester` 4.7.1 locked all 8,192 MiB. Within about a minute it reported repeated failures. I retained 25 `FAILURE` lines, including:

```text
FAILURE: possible bad address line at offset 0x00000000aee85f00.
FAILURE: 0xb7734449dff99f28 != 0xb7734449dff99f68 at offset 0x00000000aee8abc8.
FAILURE: 0x8160d05508d8fc3a != 0x8160d05508d8fc38 at offset 0x00000000aee84a08.
```

The failures span Stuck Address and data comparisons, including XOR and SUB. The offsets are within the test allocation, not physical DIMM addresses. I stopped the test after the failures, before the full requested pass completed. `ExecMainStatus=0` and `Result=success` following that stop are service-lifecycle results, not a passing test. [Memory-Test.log](../../Evidence/win11-dev%20Provisioning%20and%20Green%20Memory%20Failure%20-%202026-09-20/Logs/Memory-Test.log) is a journal export with terminal backspace sequences normalized, not an unedited terminal transcript.

The current kernel boot held 41 segmentation/general-protection/hardware-error matches; the last shown faults were Python processes on August 17. The preceding 30 minutes showed no new kernel memory, disk-I/O or OOM event. Non-ECC memory can fail without a machine-check report, so the observed data mismatches determine the result.

I also compared installation-media hashes:

| File / location | SHA-256 |
| --- | --- |
| Windows 11 ISO on Grey | `d141f6030fed50f75e2b03e1eb2e53646c4b21e5386047cb860af5223f102a32` |
| Initial Windows 11 copy on Green, twice | `84fd2bf09b5df55aed37b6cbbb184ccc5f9ccd368d2db319403bab146f3f11f3` |
| Green after `rsync -ac --inplace` | `d141f6030fed50f75e2b03e1eb2e53646c4b21e5386047cb860af5223f102a32` |
| VirtIO 0.1.285, both nodes | `e14cf2b94492c3e925f0070ba7fdfedeb2048c91eea9c5a5afb30232a3976331` |

The media comparison proves the first copy differed and the repair matched. It does not independently locate the corruption's cause. The host memory test proves a separate failure outside the Windows installer. No full terminal transcript of the hash calls was retained.

## Independent repeat

I repeated the same 8 GiB locked test in `win11-dev-memory-recheck.service` with a 180-second runtime bound after questioning whether the fault belonged to Windows. VM 103 remained stopped for the entire test. `dpkg -V memtester` reported no package-file discrepancy.

The repeat returned four failure lines before I stopped it, including:

```text
FAILURE: possible bad address line at offset 0x00000001602afea8.
FAILURE: 0xffffffffffffffff != 0xfffffffffffffff7 at offset 0x00000000602aaa20.
```

The second example differs by one bit. This reproduces corruption in a fresh allocation directly on the Proxmox host, without a running Windows guest. It still does not isolate the physical component. [Memory-Recheck.log](../../Evidence/win11-dev%20Provisioning%20and%20Green%20Memory%20Failure%20-%202026-09-20/Logs/Memory-Recheck.log) retains the journal export with terminal backspaces normalized. Neither test completed a full pass. After stopping the repeat, Green had 13,598 MiB available RAM and zero swap use; VM 103 remained stopped.

## Containment and next step

I left VM 103 stopped with `onboot=0`, removed its temporary credential-bearing installation media, and removed Green's Windows ISO copy. No other guest or node was stopped. Five-vote quorum and all checked Proxmox services remained healthy. The [provisioning record](../Change%20Records/win11-dev%20Provisioning%20and%20Green%20Memory%20Failure%20-%202026-09-20.md) holds the allocation and cleanup verification.

Green's physical memory path is unreliable. A DIMM is the leading suspect, but this online test cannot distinguish a module from a slot, motherboard or memory controller. The recorded pair is Micron 8 GB `8ATF1G64HZ-2G6E1` and SK Hynix 8 GB `HMA81GS6CJR8N-VK`. Repair needs a separate maintenance decision: power down, isolate the modules and slots, replace any failing component, and validate with an offline full-memory test. I have not performed those physical steps or rebooted the host. After repair I must reinstall the VM from verified media and complete SSH registration.

## Subsequent guest provisioning

On 2026-09-20 I chose to continue the Windows build without resolving this host fault. I completed VM 103 and verified SSH Manager access after a restart on 2026-09-21. The guest now runs with automatic startup enabled. That success does not establish that Green's physical memory path is healthy. The [completion record](../Change%20Records/win11-dev%20Completion%20-%202026-09-21.md) supersedes the stopped-guest state in the original containment above.

## Component diagnosis on 2026-09-27

I resumed the investigation after the [2026-09-23 move to Grey](../Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md). That migration encountered a rejected SSH packet and four differing blocks in the copied system disk. Direct reads produced two matching source manifests, and recopying the four ranges produced a complete matching destination. The guest now runs on Grey. Green has no VMs or LXCs; its hardware fault remains open.

At 8:17 AM Eastern, Green had 14,028 MiB available RAM and five-vote cluster quorum. No systemd unit was failed. The CPU package measured 42°C and all exposed core and package thermal-throttle counters were zero. The current kernel journal still contained faults in unrelated Python and PHP processes; the latest matching process fault was September 20. There was no matching NVMe I/O, OOM or thermal-throttle event in the inspected output. These read-only observations have no separately retained full terminal capture.

The live SMBIOS readback identifies:

| Slot | Module | Configuration |
| --- | --- | --- |
| `ChannelA-DIMM0` | Micron `8ATF1G64HZ-2G6E1`, 8 GB | DDR4 SO-DIMM, single rank, 2666 MT/s, 1.2 V |
| `ChannelB-DIMM0` | SK Hynix `HMA81GS6CJR8N-VK`, 8 GB | DDR4 SO-DIMM, single rank, 2666 MT/s, 1.2 V |

Neither module provides ECC, and Linux exposes no EDAC memory-controller instance. The firmware's interleaved address descriptions and the test's allocation-relative offsets do not identify a faulty physical module. Different manufacturers alone do not establish incompatibility.

The boot Samsung NVMe reported SMART passed, zero critical warning and zero media errors at 34°C. Its cumulative error-log count was 2,584; the returned error entry was `Invalid Field in Command`, not a media read failure. I did not treat that command-error count as proof of a bad drive. The unused failed Hitachi HDD is separate from the locked-RAM test. These filtered SMART observations have no separately retained full terminal capture.

BIOS remains `M1UKT45A`, dated 2019-07-11. I retrieved Lenovo's [M1UKT78A package README](https://download.lenovo.com/pccbbs/thinkcentre_bios/m1ujt78usa.txt), which lists the M920q among supported systems. This establishes that a newer release exists, not that firmware caused this fault or that an update fixes it. I left firmware unchanged while memory integrity is unresolved.

### Fresh reproduction

I verified the host had no guests, required more than 12 GiB available RAM and ran the installed, package-verified `memtester` 4.7.1-1:

```sh
systemd-run --unit=green-memory-diagnosis-20260927 --property=MemoryMax=9G --property=MemorySwapMax=0 --property=RuntimeMaxSec=180 --property=Nice=10 /usr/sbin/memtester 8192M 1
```

The test started at 8:18:51 AM Eastern, locked the full 8 GiB at 8:18:53 AM and failed at 8:18:57 AM:

```text
FAILURE: possible bad address line at offset 0x0000000061135e30.
```

I stopped it after observing the failure. It exited at 8:19:20 AM with 8 GiB peak memory use. This is a failed test, not a completed pass; the stopped transient unit's `Result=success` and exit status 0 describe service termination only. The [test readback](../../Evidence/Green%20Memory%20Diagnosis%20-%202026-09-27/Logs/Test-Readback.json) retains the launch, stop, verification and filtered journal commands and their results. The first timestamp extraction encountered a null journal message; the corrected query handled null and binary messages and returned the timestamps above.

Afterward, no `memtester` process remained, available memory returned to 14,010 MiB, swap use stayed at 559 MiB, and the CPU package measured 47°C. Corosync, pve-cluster, pvestatd, pve-firewall, pvedaemon and pveproxy were active. Quorum remained at five votes. I made no boot-order, firmware or service-configuration change and did not reboot Green.

### Cause assessment and isolation plan

The repeated failures establish that Green's memory path remains unreliable. A faulty SO-DIMM or its contact is my leading hypothesis. The SK Hynix module added on 2026-07-31 is the first isolation candidate because the cross-process failures followed that expansion. That sequence is correlation, not proof against that module. A defective slot, instability with the pair, motherboard faults and the CPU memory controller remain alternatives. The present temperatures and storage checks give no positive evidence for overheating or NVMe media failure as the cause.

The next useful experiment changes the physical module/slot combination. Repeating the same two-module online test cannot resolve those alternatives. [Memtest86+ documents selective module removal and the limits of attributing a memory error to a component](https://memtest.org/readme#trouble-shooting-memory-errors).

1. After approval, shut down Green and disconnect its power before touching either SO-DIMM. Record each module and slot. No guest shutdown is needed, but Green will leave the five-node cluster during maintenance.
2. Test the Micron module alone in `ChannelA-DIMM0`, then test the SK Hynix module alone in that same slot. Keep the firmware settings and test configuration unchanged.
3. Cross-check a failing module in the other slot and a passing module in the suspect slot where the supported single-module layout permits it. An error that follows the module points to that module; errors that follow a slot with otherwise passing modules point to the slot or channel path.
4. If both modules pass separately but fail together, investigate pairing, memory training and the controller. If neither module is a reliable reference, repeat with known-good compatible memory.
5. After correcting the failing configuration, complete an extended offline test across the final installed memory before placing a guest on Green.

Memtest86+ 7.20-1 is already installed, with x64 EFI and legacy images referenced in GRUB. I have not selected an offline boot entry. Physical access is needed for module isolation and to observe the boot-time test; a usable remote firmware console has not been established. Shutdown and that physical test remain pending approval and hands-on access.
