# Galaxy Storage Configuration

**Created:** 2026-07-09  
**Last updated:** 2026-08-19

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
| Current allocation | 0.00 percent after VM 122 retirement |
| Current workload | None |

I created the pool on 2026-07-28 with `pvesh create /nodes/purple-server/disks/lvmthin` and restricted the storage entry to Purple. The boot NVMe remains separate. The first workload was Kasm VM 122, which I destroyed with all of its volumes on 2026-08-19. `pvesm status` then reported the pool at 0.00 percent used. The drive reported SMART `PASSED`, normalized wear 15, and zero reallocated, CRC, or uncorrectable errors after the original migration. The [node record's Cluster Storage section](../../../../Hardware/Nodes.md#cluster-storage) explains why node-restricted storage reads `disabled` when `pvesm status` is run on a different node and holds the current Purple result.

The exact Proxmox storage stanza is in [ssd-lvm2.storage.cfg](ssd-lvm2.storage.cfg). The implementation and stop conditions are in [Kasm Session Isolation](../../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md). The full unchanged [SMART capture](../../../../Hardware/Components/Drives/SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-28.txt) is stored with the drive inventory.
