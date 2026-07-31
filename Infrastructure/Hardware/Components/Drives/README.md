# Drive Inventory

**Created:** 2026-07-24  
**Last updated:** 2026-07-31

I track every physical drive I own here, whether it's slotted in a node, sitting on the shelf as a spare, or retired and kept for a rollback. Each drive's raw SMART capture goes in a type subfolder (`NVMe/`, `SSD/`, `HDD/`), and this README is the quick-glance view: model, last-4 serial, capacity, power-on hours, wear, and health. For which drive does what job in which node, see [Galaxy node specifications](../../Nodes.md).

The tables show only the last four characters of each serial. Current captures replace the full serial and WWN with contextual placeholders before they enter the repository. I keep a dated file per capture rather than overwriting, named `smartctl-a_<model>_<serial-suffix>_<date>.txt`. `<model>` is the bare part number when the drive has one (`MZVLB256HAHQ`, `CT2000BX500SSD1`), or `Vendor-Model-Capacity` for consumer-branded drives whose part number isn't the name I'd recognize (`Samsung-850EVO-250GB`, `WDC-SN720-512G`). Don't transliterate smartctl's `Device Model` line straight into the filename; on the 850 EVO that produces `Samsung-SSD-850-EVO-250GB`, which splits `850 EVO` and repeats the `SSD` the type folder already carries.

That rule governs the capture files and tables here. It doesn't extend to `/dev/disk/by-id` paths, which embed the serial by design. Red's Seagate ST1000LM035 appears in full as `ata-ST1000LM035-1RK172_WCB0SRHK` on line 128 of the [Media Stack runbook](../../../../Platforms/Media%20Stack/Documentation/Runbook.md) and in the [HDD data migration record](../../../../Platforms/Media%20Stack/Documentation/Change%20Records/Media%20Stack%20HDD%20Data%20Migration%20-%202026-07-22.md). I keep both raw on purpose. The runbook line is a copy-paste diagnostic for CT 842 refusing startup, and a placeholder path resolves to nothing, so scrubbing it costs me time during the one fault it exists for. Scrubbing just one of the two would be worse than leaving both: the serial would still sit in the repository, and the migration record would no longer match the command I ran.

## Spare drives (not slotted)

| Drive | Serial (last 4) | Capacity | Power-on hours | Wear used | Health | Raw log |
| --- | --- | --- | --- | --- | --- | --- |
| Samsung MZVLB256HAHQ-000L7 (M.2 NVMe) | 2909 | 256 GB | 54,357 | 13% | PASSED | [log](NVMe/smartctl-a_MZVLB256HAHQ_2909_2026-07-24.txt) |
| WDC PC SN720 SDAQNTW-512G (M.2 NVMe) | 0542 | 512 GB | 29,603 | 6% | PASSED | [log](NVMe/smartctl-a_WDC-SN720-512G_0542_2026-07-24.txt) |

Both spares passed their overall SMART self-assessment with 0 media or integrity errors and 100% spare capacity. The Samsung MZVLB256HAHQ sits at 13% endurance used across 54,357 power-on hours; the WD SN720 at 6% across 29,603 hours, and at 512 GB it's the only drive here larger than 256 GB. The Samsung capture is a full `smartctl -a` read with no completed self-test on record; the WD SN720 capture shows an extended self-test that completed without error at 29,234 power-on hours.

The third spare left the shelf on 2026-07-25. The Toshiba THNSF5256GPUK (`****TALT`) is now purple's boot device, cloned from the Samsung MZVLB256HAHQ that wore out; see [Purple Boot NVMe Replacement](../../../Compute/Galaxy/Documentation/Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md). The Samsung spare above is the same model as the drive that failed, MZVLB256HAHQ-000L7, which is also what red-server boots from, so it's the drop-in for red if that one goes the same way.

## In-use drives (slotted in Galaxy nodes)

| Node | Device | Type | Model | Serial (last 4) | Capacity | Power-on hours | Wear used | Health | Role | Raw log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| grey | /dev/nvme0n1 | NVMe | Crucial CT1000P310SSD8 | A266 | 1 TB | 7,962 | 2% | PASSED | BIOS boot | [log](NVMe/smartctl-a_CT1000P310SSD8_A266_2026-07-24.txt) |
| grey | /dev/sda | SSD | Crucial CT2000BX500SSD1 | B600 | 2 TB | 8,023 | 2% | PASSED | LVM | [log](SSD/smartctl-a_CT2000BX500SSD1_B600_2026-07-24.txt) |
| grey | /dev/sdb | HDD | Toshiba DT01ACA200 | JVTS | 2 TB | 45,831 | n/a (HDD) | PASSED | ZFS | [log](HDD/smartctl-a_DT01ACA200_JVTS_2026-07-24.txt) |
| purple | /dev/nvme0n1 | NVMe | Toshiba THNSF5256GPUK | TALT | 256 GB | 23,148 | 30% | PASSED | BIOS boot | [log](NVMe/smartctl-a_THNSF5256GPUK_TALT_2026-07-25.txt) |
| purple | /dev/sda | SSD | Samsung SSD 850 EVO 250GB | 252T | 250 GB | 45,242 | see note | PASSED | `ssd-lvm2` LVM-thin; VM 122 | [log](SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-28.txt) |
| blue | /dev/nvme0n1 | NVMe | Samsung MZVLW256HEHP-000L7 | 1210 | 256 GB | 48,293 | 9% | PASSED | BIOS boot | [log](NVMe/smartctl-a_MZVLW256HEHP_1210_2026-07-24.txt) |
| blue | /dev/sda | HDD | WDC WD5000LPVX-08V0TT5 | 6NSN | 500 GB | 23,215 | n/a (HDD) | PASSED | Unused; empty GPT | [log](HDD/smartctl-a_WD5000LPVX_6NSN_2026-07-31.txt) |
| green | /dev/nvme0n1 | NVMe | Samsung MZVLB256HAHQ-000L7 | 2896 | 256 GB | 36,965 | 11% | PASSED | Proxmox boot | [log](NVMe/smartctl-a_MZVLB256HAHQ_2896_2026-07-31.txt) |
| green | /dev/sda | HDD | Hitachi HTS723232A7A364 | G91N | 320 GB | 43,950 | n/a (HDD) | FAILED extended test | Blank; do not use | [log](HDD/smartctl-a_HTS723232A7A364_G91N_2026-07-31.txt) |
| red | /dev/nvme0n1 | NVMe | Samsung MZVLB256HAHQ-000L7 | 5609 | 256 GB | 25,783 | 7% | PASSED | BIOS boot | [log](NVMe/smartctl-a_MZVLB256HAHQ_5609_2026-07-24.txt) |
| red | /dev/sda | HDD | Seagate ST1000LM035-1RK172 | SRHK | 1 TB | 24,007 | n/a (HDD) | PASSED | CT 842 `/data` bind mount | [log](HDD/smartctl-a_ST1000LM035_SRHK_2026-07-24.txt) |

The top-level SMART assessment still says `PASSED` on every slotted drive, but Green's Hitachi HDD failed its 2026-07-31 extended self-test at LBA `246502720` and now has two pending sectors. I classify that disk from the completed test instead of the top-level flag. Six drives passed a short self-test on 2026-07-24; Purple's Toshiba and Samsung 850 EVO passed their own on 2026-07-25. I captured the 850 EVO again after creating `ssd-lvm2` and moving VM 122 on 2026-07-28. Blue's WDC finished its own extended test without error at 23,215 power-on hours on 2026-07-31, at zero reallocated, pending, offline-uncorrectable, & CRC-error sectors. Two 320 GB and 500 GB HDDs went in on the same day; only one of them came back clean.

Wear percentage is the drive's own SMART endurance counter, reported by NVMe and by SATA SSDs that expose it. The 850 EVO doesn't publish a percentage-used field: its 2026-07-28 capture reports `Wear_Leveling_Count` raw 1,801 with a normalized value of 15 out of 100, alongside 0 reallocated sectors, 0 uncorrectable errors, and 0 CRC errors. Its 2026-07-25 short self-test completed without error with no failing LBA. Spinning HDDs report no wear counter at all.

Blue's WDC disk contained an older Proxmox installation when I added it. Its duplicate `pve` VG blocked Blue's NVMe `local-lvm` activation on 2026-07-30. I verified the current root and all three LXC disks were on the NVMe, then removed the WDC disk's LVM metadata, filesystem signatures, & GPT at about 00:00 EDT on 2026-07-31. I re-initialized it with an empty GPT from the Proxmox disk view at 09:10 EDT the same day, which is why `wipefs` now reports a `gpt` label and a PMBR at offset `0x1fe`. The table holds zero partitions, the drive carries no LVM PV and no filesystem, and `pvs` lists only `/dev/nvme0n1p3` in VG `pve`.

The extended test ran the drive hot. It peaked at 48 C against the 32 C maximum operating temperature the drive itself reports, with a lifetime maximum of 52 C. Its over-temperature counter still reads 0 because SCT sets that trip point at 60 C, so nothing flagged. I want a temperature check under sustained load before this disk carries anything.

Green's Hitachi disk was unused when I added it. Its extended test stopped with a read failure at 60 percent, and the pending-sector count rose from one to two. I retained the sanitized `smartctl -x` result and removed the unused partition metadata. The disk remains slotted for identification but is not an available storage device. Green's NVMe reports 11 percent endurance used, zero media-integrity errors, and 2,582 error-log entries; the raw capture preserves that distinction without treating the log-entry count as media loss.

## In-use drives (Jedi PC workstation)

Jedi PC is my Windows 11 workstation, not a Galaxy node, so its drives are listed separately. See [Jedi PC specifications](../../Jedi_Specs.md) for the full machine. I ran the 2026-07-24 short self-test from an elevated shell, since Windows blocks the NVMe self-test command without administrator rights.

| Machine | Volume | Model | Serial (last 4) | Capacity | Power-on hours | Wear used | Health | Raw log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jedi PC | C: (boot) | Samsung SSD 9100 PRO 2TB | 822D | 2 TB | 211 | 0% | PASSED | [log](NVMe/smartctl-a_Samsung-9100PRO-2TB_822D_2026-07-24.txt) |
| Jedi PC | D: (Storage) | Samsung SSD 990 PRO 2TB | 618A | 2 TB | 6,934 | 4% | PASSED | [log](NVMe/smartctl-a_Samsung-990PRO-2TB_618A_2026-07-24.txt) |

Both short tests completed without error. The 9100 PRO is nearly new at 211 power-on hours and 0% endurance used; the 990 PRO sits at 4% used across 6,934 hours. Neither reports a media or data-integrity error.

## Retired drives

| Drive | Serial (last 4) | Capacity | Power-on hours | Wear used | Health | Retired | Raw log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Samsung MZVLB256HAHQ-000L7 (M.2 NVMe) | 5659 | 256 GB | 49,373 | 169% | FAILED | 2026-07-25 | [log](NVMe/smartctl-a_MZVLB256HAHQ_5659_2026-07-24.txt) |

This is purple's original boot drive, replaced on 2026-07-25. It reports critical warning 0x04 (NVM subsystem reliability degraded) at 169% of rated write endurance across 49,373 power-on hours and 105 TB written, and its 2026-07-24 short self-test logged `Completed: failed segments` at NSID 1, segment 2. Media and data-integrity errors are still 0, so this was wear-out rather than corruption. The investigation is in [Purple NVMe Reliability Failure - 2026-07-22](../../../Compute/Galaxy/Documentation/Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md).

I'm keeping it rather than discarding it. It still boots and it hasn't lost data, so it's the rollback path if the Toshiba that replaced it misbehaves. It doesn't go back into a node for any other reason, and it isn't a spare.

## Layout

- `NVMe/` raw SMART captures for M.2 and U.2 NVMe drives
- `SSD/` raw SMART captures for SATA SSDs, created with the first capture
- `HDD/` raw SMART captures for spinning HDDs, created with the first capture
