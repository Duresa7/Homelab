# Memory Test Failures on green-server

**Created:** 2026-09-20  
**Last updated:** 2026-09-21

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
