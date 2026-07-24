# Drive Inventory

**Created:** 2026-07-24  
**Last updated:** 2026-07-24

I track every physical drive I own here, whether it's slotted in a node or sitting on the shelf as a spare. Each drive's raw SMART capture goes in a type subfolder (`NVMe/`, `SSD/`, `HDD/`), and this README is the quick-glance view: model, last-4 serial, capacity, power-on hours, wear, and health. For which drive does what job in which node, see [Galaxy node specifications](../../Nodes.md).

The logs and tables here show only the last four characters of each serial, and I strip the WWN and IEEE EUI-64 device IDs, so nothing published can be used for warranty fraud or to fingerprint a specific unit. Those last four match the tail of the serial printed on each drive's own label, so I can still identify the right physical drive when two share a model. The two Samsung MZVLB256HAHQ units read `5659` and `5609`, so even same-model drives stay distinct. Full serials and device IDs live in the gitignored `Sensitive/Hardware/drive-serials.md` for warranty claims.

Raw logs stay as verbatim smartctl output apart from that redaction; I keep a dated file per capture rather than overwriting, named `smartctl-a_<model>_<last4>_<date>.txt`. On 2026-07-24 I ran a SMART short self-test (`smartctl -t short`) on all seven slotted drives and stored a full `smartctl -a` transcript for each under `NVMe/`, `SSD/`, and `HDD/`. Every drive I own now has at least one stored capture here; this is the only home for these logs.

## Spare drives (not slotted)

| Drive | Serial (last 4) | Capacity | Power-on hours | Wear used | Health | Raw log |
| --- | --- | --- | --- | --- | --- | --- |
| Samsung MZVLB256HAHQ-000L7 (M.2 NVMe) | 2909 | 256 GB | 54,357 | 13% | PASSED | [log](NVMe/smartctl-a_MZVLB256HAHQ_2909_2026-07-24.txt) |
| Toshiba THNSF5256GPUK (M.2 NVMe) | TALT | 256 GB | 23,145 | 30% | PASSED | [log](NVMe/smartctl-a_THNSF5256GPUK_TALT_2026-07-24.txt) |

Both spares passed their overall SMART self-assessment with 0 media or integrity errors and 100% spare capacity. The Toshiba THNSF5256GPUK sits at 30% endurance used across 23,145 power-on hours; the Samsung MZVLB256HAHQ at 13% across 54,357 hours.

Neither drive has a completed short self-test on record yet, so I've got a retest planned on a direct NVMe connection to confirm one. The Samsung is the same model as purple's failing boot drive, which makes it a candidate replacement.

## In-use drives (slotted in Galaxy nodes)

| Node | Device | Type | Model | Serial (last 4) | Capacity | Power-on hours | Wear used | Health | Role | Raw log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| grey | /dev/nvme0n1 | NVMe | Crucial CT1000P310SSD8 | A266 | 1 TB | 7,962 | 2% | PASSED | BIOS boot | [log](NVMe/smartctl-a_CT1000P310SSD8_A266_2026-07-24.txt) |
| grey | /dev/sda | SSD | Crucial CT2000BX500SSD1 | B600 | 2 TB | 8,023 | 2% | PASSED | LVM | [log](SSD/smartctl-a_CT2000BX500SSD1_B600_2026-07-24.txt) |
| grey | /dev/sdb | HDD | Toshiba DT01ACA200 | JVTS | 2 TB | 45,831 | n/a (HDD) | PASSED | ZFS | [log](HDD/smartctl-a_DT01ACA200_JVTS_2026-07-24.txt) |
| purple | /dev/nvme0n1 | NVMe | Samsung MZVLB256HAHQ-000L7 | 5659 | 256 GB | 49,373 | 169% | FAILED | BIOS boot | [log](NVMe/smartctl-a_MZVLB256HAHQ_5659_2026-07-24.txt) |
| blue | /dev/nvme0n1 | NVMe | Samsung MZVLW256HEHP-000L7 | 1210 | 256 GB | 48,293 | 9% | PASSED | BIOS boot | [log](NVMe/smartctl-a_MZVLW256HEHP_1210_2026-07-24.txt) |
| red | /dev/nvme0n1 | NVMe | Samsung MZVLB256HAHQ-000L7 | 5609 | 256 GB | 25,783 | 7% | PASSED | BIOS boot | [log](NVMe/smartctl-a_MZVLB256HAHQ_5609_2026-07-24.txt) |
| red | /dev/sda | HDD | Seagate ST1000LM035-1RK172 | SRHK | 1 TB | 24,007 | n/a (HDD) | PASSED | CT 842 `/data` bind mount | [log](HDD/smartctl-a_ST1000LM035_SRHK_2026-07-24.txt) |

The 2026-07-24 short self-test completed without error on six of the seven, all reporting overall health `PASSED`. Purple's boot NVMe is the only failure; its short test logged `Completed: failed segments`. It reports critical warning 0x04 (NVM subsystem reliability degraded) at 169% of rated write endurance across 49,373 power-on hours, with 0 media errors so far, so it's a wear-out, not sudden corruption. I track it in [Purple NVMe Reliability Failure - 2026-07-22](../../../Compute/Galaxy/Documentation/Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md). Wear percentage is the drive's own SMART endurance counter for NVMe and SATA SSDs; spinning HDDs don't report it.

## In-use drives (Jedi PC workstation)

Jedi PC is my Windows 11 workstation, not a Galaxy node, so its drives are listed separately. See [Jedi PC specifications](../../Jedi_Specs.md) for the full machine. I ran the 2026-07-24 short self-test from an elevated shell, since Windows blocks the NVMe self-test command without administrator rights.

| Machine | Volume | Model | Serial (last 4) | Capacity | Power-on hours | Wear used | Health | Raw log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jedi PC | C: (boot) | Samsung SSD 9100 PRO 2TB | 822D | 2 TB | 211 | 0% | PASSED | [log](NVMe/smartctl-a_Samsung-9100PRO-2TB_822D_2026-07-24.txt) |
| Jedi PC | D: (Storage) | Samsung SSD 990 PRO 2TB | 618A | 2 TB | 6,934 | 4% | PASSED | [log](NVMe/smartctl-a_Samsung-990PRO-2TB_618A_2026-07-24.txt) |

Both short tests completed without error. The 9100 PRO is nearly new at 211 power-on hours and 0% endurance used; the 990 PRO sits at 4% used across 6,934 hours. Neither reports a media or data-integrity error.

## Layout

- `NVMe/` raw SMART captures for M.2 and U.2 NVMe drives
- `SSD/` raw SMART captures for SATA SSDs, created with the first capture
- `HDD/` raw SMART captures for spinning HDDs, created with the first capture
