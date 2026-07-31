# Galaxy Green and Blue Hardware Changes

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Implementation date:** 2026-07-30 through 2026-07-31  
**Status:** Complete  
**Affected hardware:** `green-server` and `blue-server`

## Scope

I moved one 8 GB SO-DIMM from Blue to Green, added a 2 GB SO-DIMM to Blue, installed one SATA HDD in each node, and checked the resulting hardware from the running Proxmox systems. Both extended HDD tests finished and both disks are blank. One of the two drives is unfit for data.

## Starting State

Blue had one 4 GB SO-DIMM and an 8 GB SO-DIMM. Green had one 8 GB SO-DIMM. Both systems used a 256 GB Samsung NVMe device for Proxmox.

The WDC HDD added to Blue retained an older Proxmox installation. Its `pve` volume-group name collided with Blue's active NVMe `pve` group during the 2026-07-30 boot. I repaired and erased that old layout under the [duplicate VG troubleshooting record](../../../Compute/Galaxy/Documentation/Troubleshooting/Duplicate%20pve%20Volume%20Group%20on%20blue-server%20-%202026-07-30.md).

## Step 1: Redistribute the Memory

I moved Blue's 8 GB module to Green and installed a 2 GB Samsung module in Blue's open slot. The live SMBIOS read-back reports:

| Node | Slot 1 | Slot 2 | Installed total | Proxmox usable bytes |
|---|---|---|---:|---:|
| Blue | Samsung 2 GB DDR4-2133, `M471A5644EB0-CPB` | SK Hynix 4 GB DDR4-2400, `HMA851S6AFR6N-UH` | 6 GB | 6,094,282,752 |
| Green | Micron 8 GB DDR4-2667, `8ATF1G64HZ-2G6E1` | SK Hynix 8 GB DDR4-2667, `HMA81GS6CJR8N-VK` | 16 GB | 16,599,257,088 |

Blue runs both modules at 2133 MT/s. Green runs both modules at 2666 MT/s.

## Step 2: Verify the Installed Drives

The running systems report the expected devices:

| Node | Device | Model | Capacity | Role |
|---|---|---|---:|---|
| Blue | `/dev/nvme0n1` | Samsung MZVLW256HEHP-000L7 | 256,060,514,304 bytes | Proxmox boot, root, and `local-lvm` |
| Blue | `/dev/sda` | WDC WD5000LPVX-08V0TT5, serial suffix `6NSN` | 500,107,862,016 bytes | Unused SATA HDD, empty GPT |
| Green | `/dev/nvme0n1` | Samsung MZVLB256HAHQ-000L7 | 256,060,514,304 bytes | Proxmox boot, root, and `local-lvm` |
| Green | `/dev/sda` | Hitachi HTS723232A7A364, serial suffix `G91N` | 320,072,933,376 bytes | Unused SATA HDD under extended test |

Before each test I resolved the exact `/dev/disk/by-id` link, matched its serial and byte size, required a whole-disk target, and checked mounts, swap, LVM, ZFS, and Proxmox configuration references. Neither HDD was in use.

## Step 3: Run the Extended SMART Tests

I started an extended SMART self-test on both SATA HDDs on 2026-07-31. Green's test started at about 09:47 EDT with a 76-minute estimate. Blue's test started at about 09:47 EDT with a 103-minute estimate.

Green's pre-test counters included one current pending sector at 43,949 power-on hours. Its extended test stopped at 60 percent with a read failure at LBA `246502720`. The pending-sector count increased to two at 43,950 hours. The top-level assessment still said `PASSED`, but the completed self-test proves that the disk is unreliable.

Blue's pre-test critical counters were zero at 23,213 power-on hours. Its extended test finished at 11:32 EDT and logged `Extended offline Completed without error` at 23,215 hours with no failing LBA. Reallocated, pending, offline-uncorrectable, and CRC-error counts all stayed at 0 through a full surface read.

Reading `smartctl -l selftest` on its own would have produced a false pass. At 11:22 EDT that log's top entry was a stale `Vendor (0x50)` record showing `Completed without error` at a `LifeTime` of 0 hours, while `smartctl -c` still reported execution status `241`, ten percent remaining. Status `241` means running. The execution-status field decides whether a result exists; the self-test log only says what the last finished result was.

Blue's drive did run hot. Its SCT table reports a 48 C peak against the 32 C maximum operating temperature the drive itself publishes, with a 52 C lifetime maximum, and its over-temperature counter stayed at 0 because SCT trips at 60 C.

The sanitized [Green SMART capture](../../Components/Drives/HDD/smartctl-a_HTS723232A7A364_G91N_2026-07-31.txt) retains the complete 244-line `smartctl -x` result, and the [Blue capture](../../Components/Drives/HDD/smartctl-a_WD5000LPVX_6NSN_2026-07-31.txt) the 202-line result. Both replace the drive serial and WWN with contextual placeholders. [S02 records Blue's result and disk state](../../Evidence/Galaxy%20Green%20and%20Blue%20Hardware%20Changes%20-%202026-07-31/Logs/S02%20Blue%20Extended%20SMART%20Result%20-%202026-07-31.md).

## Step 4: Wipe Green's Unused SATA Metadata

After the failed test was retained, I repeated the identity and no-use gates against the exact Green by-id path. I required `/dev/sda`, the expected serial and 320,072,933,376-byte size, whole-disk type, no mounts, no LVM, no ZFS, no swap, no Proxmox or `fstab` reference, and no active SMART test.

I destroyed both GPT headers with `sgdisk --zap-all`, removed other signatures with `wipefs --all --force`, reread the partition table with `blockdev --rereadpt`, and waited for udev. The final `lsblk`, `wipefs`, and `blkid` checks found no partition-table type, filesystem, signature, UUID, or mount. Galaxy remained quorate at five votes, Green's `local` and `local-lvm` stayed active, and Prometheus still reported Green `up=1`. [S01 records the test and wipe](../../Evidence/Galaxy%20Green%20and%20Blue%20Hardware%20Changes%20-%202026-07-31/Logs/S01%20Green%20Extended%20SMART%20and%20Metadata%20Wipe%20-%202026-07-31.md).

## Step 5: Reconcile Blue's Disk State

Blue's `/dev/sda` carries an empty GPT, not the bare disk the 00:00 EDT wipe left behind. `wipefs` reports a `gpt` label at `0x200`, its backup at `0x7470c05e00`, and a PMBR at `0x1fe`; `blkid` reports `PTTYPE="gpt"`.

The Proxmox task index names what wrote it. A `wipedisk:sda` task followed by a `diskinit:sda` task ran as `root@pam` at 09:10:37 and 09:10:39 EDT on 2026-07-31, nine hours after the wipe. That is the disk view's Wipe Disk and Initialize Disk with GPT pair. The result is a valid partition table holding zero partitions.

Nothing regressed. `lsblk` shows no child partitions, the disk carries no filesystem, and `pvs` lists only `/dev/nvme0n1p3` in VG `pve`, so the duplicate volume group that caused the 2026-07-30 outage cannot come back from this disk.

## Resulting Configuration

Galaxy now has five physical nodes. Green has 16 GB installed and Blue has 6 GB installed. Proxmox remains on each node's NVMe device. The two added SATA HDDs are separate whole disks and are not Proxmox storage.

The two disks ended in different places. Blue's WDC passed a full extended read at 23,215 hours and is available if I want to assign it, subject to a temperature check under sustained load. Green's Hitachi is blank, failed its extended read at LBA `246502720`, sits at two pending sectors, and must not receive data.

## Rollback

The RAM change can be reversed by powering both M920q systems down and returning the 8 GB module to Blue. The HDDs can be removed while their node is shut down because neither is referenced by a guest, Proxmox storage, LVM, swap, ZFS, or a mounted filesystem.

## Remaining Work

None for the hardware itself. Blue's capture is sanitized and stored, its disk state is reconciled against the Proxmox task log, and the [drive inventory](../../Components/Drives/README.md) carries both final health results.

Green's Hitachi stays slotted as failed hardware. If I want the SATA bay back for a working disk, that's a separate change with its own record.

