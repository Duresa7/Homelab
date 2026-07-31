# Galaxy Storage Configuration

**Created:** 2026-07-09  
**Last updated:** 2026-07-31

This directory records Galaxy-owned storage pools and the change records that established them.

## `ssd-lvm2`

| Setting | Value |
| --- | --- |
| Node | `purple-server` only |
| Device | `/dev/sda`, Samsung SSD 850 EVO 250GB |
| Proxmox type | LVM-thin |
| Volume group / thin pool | `ssd-lvm2` / `ssd-lvm2` |
| Content | VM images and LXC root directories |
| Capacity | 239,185,920 KiB |
| Allocated after VM 122 migration | 26,382,206 KiB, 11.03 percent |
| First workload | Kasm VM 122 |

I created the pool on 2026-07-28 with `pvesh create /nodes/purple-server/disks/lvmthin` and restricted the storage entry to Purple. The boot NVMe remains separate. The drive reported SMART `PASSED`, normalized wear 15, and zero reallocated, CRC, or uncorrectable errors after the migration.

The exact Proxmox storage stanza is in [ssd-lvm2.storage.cfg](ssd-lvm2.storage.cfg). The implementation and stop conditions are in [Kasm Session Isolation](../../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md). The full unchanged [SMART capture](../../../../Hardware/Components/Drives/SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-28.txt) is stored with the drive inventory.
