# Purple Boot NVMe Replacement

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

**Implemented:** 2026-07-25  
**Node:** `purple-server` (192.168.70.11, nodeid 2)

## What I did

I pulled the worn-out Samsung MZVLB256HAHQ boot NVMe out of `purple-server`, cloned it with Clonezilla onto a Toshiba THNSF5256GPUK, and put the Toshiba in as the boot device. I also added a Samsung SSD 850 EVO 250 GB on SATA for secondary storage. Purple booted off the clone at `2026-07-25 07:19:56 EDT` and rejoined Galaxy as nodeid 2 with four of four votes. The hardware issue tracked in [Purple NVMe Reliability Failure](../Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md) is closed.

The clone was clean. Nothing needed a repair pass, no cluster object changed, and the new drive reports SMART overall health `PASSED` with critical warning `0x00`.

## Starting state

The outgoing drive was a Samsung MZVLB256HAHQ-000L7 (serial `****5659`), 256 GB, reporting overall health `FAILED`, NVMe critical warning `0x04`, 169% of rated write endurance used across 49,373 power-on hours, and 2,462 error-log entries. Its 2026-07-24 SMART short self-test logged `Completed: failed segments` at NSID 1, segment 2. Media and data-integrity errors were still zero, so this was wear-out rather than corruption.

Purple carried no guests. The 2026-07-23 Kasm teardown removed `kasm-agent-01` and `inetsim-01`, and I never placed another workload there while the warning stood. I shut the node down at `2026-07-24 11:46:33 EDT`, which left Galaxy quorate at three of three available votes against an expected four.

## Hardware changes

| Slot | Before | After |
|---|---|---|
| M.2 NVMe (`/dev/nvme0n1`) | Samsung MZVLB256HAHQ-000L7 `****5659`, 256 GB, health FAILED, 169% used | Toshiba THNSF5256GPUK `****TALT`, 256 GB, health PASSED, 30% used |
| SATA (`/dev/sda`) | empty | Samsung SSD 850 EVO 250 GB `****252T`, 232.9 GiB, health PASSED |

I used the Toshiba instead of the same-model Samsung MZVLB256HAHQ spare that the [drive inventory](../../../../Hardware/Components/Drives/README.md) had called the cleanest drop-in. The Toshiba carries 23,148 power-on hours against that spare's 54,357, so it's the lower-mileage of the two even though it reports 30% endurance used against the Samsung's 13%. The Samsung spare stays on the shelf and is still the same-model fallback.

## The clone, not a reinstall

I imaged the failing drive to the Toshiba with Clonezilla rather than installing Proxmox VE fresh, so the node kept its own identity. No `pvecm add`, no reissued certificates, no HA reconfiguration, and no storage recreation. Cluster config version stayed at 8.

The Toshiba's own SMART counters show the copy. Its `Data Units Written` went from 71,529,613 on the 2026-07-24 shelf capture to 72,030,221 in today's, a rise of 500,608 units at 512 KB each, or 256.3 GB against the drive's 256,060,514,304-byte capacity. That's a whole-device write, with a few gigabytes of Purple's own post-boot writes on top. `Data Units Read` rose 480,160 units over the same window, 245.8 GB, which is a full-device read of a drive that had just been written and is consistent with a read-back pass rather than normal boot traffic. Power cycles went 9,009 to 9,032 and unsafe shutdowns 817 to 836, which is the bench work.

## Resulting configuration

`/dev/nvme0n1` (Toshiba, 238.5 GiB) carries the cloned layout: a 1007 KiB BIOS boot partition, a 1 GiB vfat ESP mounted at `/boot/efi`, and a 237 GiB LVM PV. The `pve` volume group holds `root` at 69.25 GiB ext4 mounted on `/`, `swap` at 8 GiB, and the `data` thin pool at 140.87 GiB, with 16 GiB free in the VG. `df` reports `/` at 6.2 GiB used of 68 GiB.

`pvesm status` shows `local` active at 67.6 GiB with 9.07% used, and `local-lvm` active at 140.87 GiB with 0.00% used. `hddpool-1` and `ssd-lvm1` are still disabled on this node, exactly as they were before the swap.

The 850 EVO is physically in and visible, and that's all. It holds one empty 16 MiB partition, has no filesystem, and has no Proxmox storage entry pointing at it. The disabled `ssd-lvm1` storage predates this drive and isn't attached to it. Its SMART capture at [smartctl-a_Samsung-850EVO-250GB_252T_2026-07-25.txt](../../../../Hardware/Components/Drives/SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-25.txt) returns overall health `PASSED` with 0 reallocated sectors, 0 uncorrectable errors, and 0 CRC errors across 45,165 power-on hours. Wear-leveling count sits at 1,800 cycles with a normalized value of 15.

## Verification

The Toshiba passes its own health check. `smartctl -a /dev/nvme0` returns overall health `PASSED`, critical warning `0x00`, available spare 100% against a 10% threshold, 30% endurance used, 23,148 power-on hours, zero media and data-integrity errors, zero error-log entries, and 41 C. The outgoing Samsung had 2,462 error-log entries; the Toshiba has none. The full capture is stored at [smartctl-a_THNSF5256GPUK_TALT_2026-07-25.txt](../../../../Hardware/Components/Drives/NVMe/smartctl-a_THNSF5256GPUK_TALT_2026-07-25.txt).

I ran `smartctl -t short /dev/nvme0` after the node came up. The log reports `Short  Completed without error` at 23,148 power-on hours with no failing LBA. That's the first self-test on record for this drive; the 2026-07-24 shelf capture logged none. The drive it replaced failed the same test at 49,373 hours.

I ran `smartctl -t short /dev/sda` on the Samsung 850 EVO at `2026-07-25 08:47:11 EDT`. The self-test log reports `Short offline  Completed without error` at 45,165 power-on hours with no failing LBA. The post-test capture returns overall health `PASSED`, 0 reallocated sectors, 0 uncorrectable errors, 0 CRC errors, and no entries in the SMART error log.

Software state matches what Purple ran before it went down. `pveversion` reports `pve-manager/9.2.5/20242970da7fbcef` on kernel `7.0.14-6-pve`, and `apt list --upgradable` returns nothing.

Cluster membership came back on its own. `pvecm status` from Grey reports Quorate Yes with nodes 4, expected votes 4, total votes 4, quorum 3, and config version 8. `pvecm nodes` lists nodeid 2 as `purple-server`. `corosync-cfgtool -s` on Purple shows both rings connected to nodeids 1, 3, and 4: `LINK ID 0` on `192.168.70.11` and `LINK ID 1` on `192.168.71.11`. `ip -br addr` confirms `vmbr0` up with `vmbr0.70` at 192.168.70.11/24 and `vmbr0.71` at 192.168.71.11/24.

`ha-manager status` reports quorum OK, master `blue-server` active, fencing armed with the CRM watchdog active, and `lrm purple-server (idle, watchdog standby)`. CT 107 and CT 108 stayed started on `blue-server` throughout; nothing needed to move. All seven checked units are active: `pve-cluster`, `corosync`, `pvedaemon`, `pveproxy`, `pvestatd`, `pve-ha-lrm`, and `pve-ha-crm`. `smartd` is active too, which is what caught the original failure.

The boot log is clean on the storage side. `dmesg` shows `nvme nvme0: pci function 0000:01:00.0` with 6/0/0 default/read/poll queues, `nvme0n1: p1 p2 p3`, and the ext4 root mounting and remounting read-write with no I/O error, controller reset, or filesystem repair. The `journalctl -p err -b` output holds 60 lines of pre-existing ACPI BIOS, `sof-audio` firmware, `blkmapd` pipe, and `openipmi` noise plus the normal pmxcfs-before-corosync startup messages. The previous boot had 61 of the same, so none of it is new and none of it touches storage.

## Downtime

Purple was powered off from `2026-07-24 11:46:33 EDT` to `2026-07-25 07:19:56 EDT`, which `last` records as 19 hours 33 minutes. The swap and clone themselves took about an hour of bench work; the rest of that window is the node sitting powered down between the shutdown and the reinstall. Galaxy held quorum at three of three available votes for the whole 19.5 hours, so no other node could come offline during it. No guest was affected, because Purple carried none.

## Rollback point

The failed Samsung `****5659` is intact and still bootable. It reports `FAILED` at 169% endurance used, but it hasn't lost data and its media-error count is still zero, so refitting it is a real fallback if the Toshiba misbehaves. I'm keeping it in the [drive inventory](../../../../Hardware/Components/Drives/README.md) under retired drives rather than discarding it.

## Remaining work

The Toshiba is used stock, not a new drive. It sits at 30% endurance used across 23,148 power-on hours and 36.8 TB written, so it buys years rather than settling the question forever. I'll watch its endurance counter alongside the media-error count.

The 850 EVO needs a decision: either give it a Proxmox storage role or take it back out. Purple's per-sandbox concurrency budget in the [Agent Sandbox plan](../../../../../Platforms/Agent%20Sandbox/Documentation/Agent%20Sandbox%20Plan.md) was capped partly on memory and partly on having one 256 GB boot device to work from, and this drive is the answer to the open question of whether to add an SSD to Purple.

Purple is still guest-free and can now take a workload again. Both open items are tracked in the [Galaxy TODO](../TODO.md).

## Related records

- [Purple NVMe Reliability Failure](../Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md), the investigation this closes
- [Drive Inventory](../../../../Hardware/Components/Drives/README.md), which holds every SMART capture named here
- [Galaxy node specifications](../../../../Hardware/Nodes.md), updated for Purple's new boot device and added SSD
- [Kasm Lab Proxmox Teardown](Kasm%20Lab%20Proxmox%20Teardown%20-%202026-07-23.md), which left Purple guest-free for this swap
