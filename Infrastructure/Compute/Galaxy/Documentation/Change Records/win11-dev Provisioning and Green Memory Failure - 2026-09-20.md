# win11-dev Provisioning and Green Memory Failure

**Created:** 2026-09-20  
**Last updated:** 2026-09-21

I created VM 103 `win11-dev` on `green-server` for a standalone Windows 11 Pro development workstation. I selected Windows and SSH only, with development tools left for later. The first installation crashed, and an independent host memory test returned 25 failure lines. I initially left the VM stopped with automatic startup disabled. Later the same evening I chose to continue on Green despite the unresolved memory fault. The resumed installation reached the desktop that evening. I completed SSH and restart verification on 2026-09-21; the [completion record](win11-dev%20Completion%20-%202026-09-21.md) holds the current state.

## Allocation and installation

| Setting | Observed configuration |
| --- | --- |
| VM / host | 103 `win11-dev`, `green-server` (`192.168.70.14`) |
| CPU / RAM | 4 host-model vCPUs, 8 GiB fixed RAM |
| System disk | 120 GiB, `local-lvm:vm-103-disk-1`, virtio-scsi-single, discard, SSD flag and I/O thread |
| Firmware | OVMF, pre-enrolled Secure Boot keys, 4 MiB EFI volume `vm-103-disk-0` |
| TPM | Emulated TPM 2.0, 4 MiB volume `vm-103-disk-2` |
| Network | VirtIO on `vmbr0`, Personal-A VLAN 40; no guest address verified |
| Intended account | Local `dkadi`; credential stored securely, account creation not verified |
| First-attempt state | Stopped; `onboot=0`; installation media detached; no usable OS or SSH service verified |

At preflight Green had no guests, 13,538 MiB available RAM, and an empty 141.23 GiB thin pool. Galaxy held five votes and quorum. I copied the existing Windows 11 25H2 and VirtIO 0.1.285 media from Grey and built an answer disc using declarative `DiskConfiguration`, a local account, and first-logon guest-agent installation. The XML parsed before boot. VM creation and startup succeeded at about 7:49 PM Eastern.

Setup paused for a product key. I selected the no-key installation option. It proceeded, then crashed with `PFN_LIST_CORRUPT (0x4E)` before the QEMU guest agent became available. Windows activation, first logon, local-account creation, SSH and domain-state checks were never reached. I retained the [crash screen](../../Evidence/win11-dev%20Provisioning%20and%20Green%20Memory%20Failure%20-%202026-09-20/Windows-Setup-PFN-LIST-CORRUPT.png).

## Diagnosis

The [memory-failure record](../Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md) holds the host test and media checks. An 8 GiB locked `memtester` allocation produced 25 failure lines across address and data comparisons. A second independent 8 GiB host test reproduced four more failure lines with the VM still stopped, and package integrity verification found no modification to `memtester`. The physical memory path is failing; the particular DIMM, slot or controller has not been isolated.

The first copied Windows ISO had a stable SHA-256 mismatch against Grey. A checksum-based rsync repair restored the source hash. I still removed the copied Windows ISO because installation cannot be trusted on this host until the memory fault is repaired.

## Containment and verification

I stopped the new VM, disabled automatic startup, detached all three installation discs, and removed the temporary password file, generated answer file and answer ISO. I also removed the local and SSH Manager password staging copies. After retaining the evidence I removed the remote build directory and remaining task staging files. The credential remains in secure storage for the intended machine; it is not evidence that Windows created its account. A rebuild should use a fresh credential.

I stopped the memory test after failures were conclusive. It did not finish a full pass. Its final systemd result was `success` after the explicit stop, which does not mean memory passed. No host reboot, RAM replacement, snapshot, backup, directory change, network-policy change or SSH Manager registration occurred.

At 7:56 PM Eastern, VM 103 was stopped with `onboot=0`, Galaxy was quorate with five votes, and `pvestatd`, `pve-cluster`, Corosync and `pve-firewall` were active. Green had 13,544 MiB available memory and no swap in use. Its thin pool held 547,921 KiB of allocated data (0.37%), with 147,538,862 KiB available. The failed 298.09 GiB SATA HDD remains unused. [Final verification](../../Evidence/win11-dev%20Provisioning%20and%20Green%20Memory%20Failure%20-%202026-09-20/Final-Verification.json) retains the exact final query, output and exit code. Earlier setup and containment calls have no separately retained terminal transcript.

## Resumed installation

Later on 2026-09-20 I explicitly chose to proceed on Green without repairing its memory first. I replaced the installation media copy and verified its SHA-256 against Grey: both returned `d141f6030fed50f75e2b03e1eb2e53646c4b21e5386047cb860af5223f102a32`. I rotated and saved the intended local credential, rebuilt the answer disc, and verified that the saved credential matched the staged setup credential without displaying either value.

I attached the Windows, VirtIO and answer discs, started VM 103, and selected the no-product-key option. Setup reached 80% in its installation phase. These steps have no separately retained terminal capture. The earlier containment state above describes the first failed attempt, not the resumed build.

## Open

Windows, SSH Manager and restart verification were completed on 2026-09-21. Green's memory fault and Windows activation remain open. See the [completion record](win11-dev%20Completion%20-%202026-09-21.md).
