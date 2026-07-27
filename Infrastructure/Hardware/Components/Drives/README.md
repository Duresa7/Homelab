# Drive Inventory

**Created:** 2026-07-24  
**Last updated:** 2026-07-27

I track every physical drive I own here, whether it's slotted in a node, sitting on the shelf as a spare, or retired and kept for a rollback. Each drive's raw SMART capture goes in a type subfolder (`NVMe/`, `SSD/`, `HDD/`), and this README is the quick-glance view: model, last-4 serial, capacity, power-on hours, wear, and health. For which drive does what job in which node, see [Galaxy node specifications](../../Nodes.md).

The logs and tables here show only the last four characters of each serial, and I strip the WWN and IEEE EUI-64 device IDs, so nothing published can be used for warranty fraud or to fingerprint a specific unit. Those last four match the tail of the serial printed on each drive's own label, so I can still identify the right physical drive when two share a model. The two Samsung MZVLB256HAHQ units read `5659` and `5609`, so even same-model drives stay distinct. Full serials and device IDs live in the gitignored `Sensitive/Hardware/drive-serials.md` for warranty claims.

Raw logs stay as verbatim smartctl output apart from that redaction; I keep a dated file per capture rather than overwriting, named `smartctl-a_<model>_<last4>_<date>.txt`. On 2026-07-24 I ran a SMART short self-test (`smartctl -t short`) on all seven drives that were slotted that day and stored a full `smartctl -a` transcript for each under `NVMe/`, `SSD/`, and `HDD/`. Every drive I own has at least one stored capture here; this is the only home for these logs.

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
| purple | /dev/sda | SSD | Samsung SSD 850 EVO 250GB | 252T | 250 GB | 45,165 | see note | PASSED | Permanent general VM and LXC storage; configuration pending | [log](SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-25.txt) |
| blue | /dev/nvme0n1 | NVMe | Samsung MZVLW256HEHP-000L7 | 1210 | 256 GB | 48,293 | 9% | PASSED | BIOS boot | [log](NVMe/smartctl-a_MZVLW256HEHP_1210_2026-07-24.txt) |
| red | /dev/nvme0n1 | NVMe | Samsung MZVLB256HAHQ-000L7 | 5609 | 256 GB | 25,783 | 7% | PASSED | BIOS boot | [log](NVMe/smartctl-a_MZVLB256HAHQ_5609_2026-07-24.txt) |
| red | /dev/sda | HDD | Seagate ST1000LM035-1RK172 | SRHK | 1 TB | 24,007 | n/a (HDD) | PASSED | CT 842 `/data` bind mount | [log](HDD/smartctl-a_ST1000LM035_SRHK_2026-07-24.txt) |

Every slotted drive reports overall health `PASSED` as of 2026-07-25. Six passed a short self-test on 2026-07-24; purple's Toshiba & Samsung 850 EVO passed their own on 2026-07-25 at 23,148 and 45,165 power-on hours. The one failure in this table's history was purple's original Samsung MZVLB256HAHQ, which I replaced on 2026-07-25 and moved to the retired list below.

Wear percentage is the drive's own SMART endurance counter, reported by NVMe and by SATA SSDs that expose it. The 850 EVO doesn't publish a percentage-used field: it reports `Wear_Leveling_Count` at 1,800 program/erase cycles with a normalized value of 15 out of 100, alongside 0 reallocated sectors, 0 uncorrectable errors, and 0 CRC errors. Its 2026-07-25 short self-test completed without error with no failing LBA. Spinning HDDs report no wear counter at all.

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
