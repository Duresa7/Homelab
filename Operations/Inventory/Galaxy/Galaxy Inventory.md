# Galaxy Inventory

**Created:** 2026-07-08  
**Last updated:** 2026-08-03

This index links the latest complete Galaxy snapshot set. I superseded the first 2026-08-03 service snapshot after a same-day staleness audit found newer workload versions, a larger Prometheus target set, and completed media verification. Node, VM, and LXC configuration did not change, so the current set reuses those verified snapshots.

| File | Contents |
| --- | --- |
| [Nodes Post-Green Expansion - 2026-07-31.md](Nodes%20Post-Green%20Expansion%20-%202026-07-31.md) | Current five-node Proxmox hardware and physical-storage snapshot |
| [VMs Post-Parrot - 2026-07-30.md](VMs%20Post-Parrot%20-%202026-07-30.md) | Current QEMU VM configuration snapshot; unchanged by the PXE deployment |
| [LXCs Post-Parrot - 2026-07-30.md](LXCs%20Post-Parrot%20-%202026-07-30.md) | Current LXC configuration snapshot; unchanged by the PXE deployment |
| [Services Post-Staleness Audit - 2026-08-03.md](Services%20Post-Staleness%20Audit%20-%202026-08-03.md) | Current workload snapshot: 19 guest records, 12 running, 49 Prometheus targets, 14 active Wazuh agents, and completed media verification |

## Snapshot sequence

Two complete sets carry the date 2026-07-28 because I changed the fleet twice that day. Two also carry 2026-08-03 because the audit superseded the earlier service record without rewriting it. Read the sequence in order; the post-staleness audit set is current.

| Set | Captures | Index |
| --- | --- | --- |
| `- 2026-07-27` | The fleet before the 850 EVO became `ssd-lvm2` | [Galaxy Inventory - 2026-07-27.md](Galaxy%20Inventory%20-%202026-07-27.md) |
| `- 2026-07-28` | After moving Kasm VM 122 onto `ssd-lvm2` and expanding `scsi0` to 150G | [Galaxy Inventory - 2026-07-28.md](Galaxy%20Inventory%20-%202026-07-28.md) |
| `Post-Kasm Build-Out - 2026-07-28` | After the workspace build-out: 200G disk, VLAN 75, four session lanes | [Galaxy Inventory Post-Kasm Build-Out - 2026-07-28.md](Galaxy%20Inventory%20Post-Kasm%20Build-Out%20-%202026-07-28.md) |
| `Post-Parrot - 2026-07-30` | After the controlled Parrot install, image-update control, and replacement snapshot | [Galaxy Inventory Post-Parrot - 2026-07-30.md](Galaxy%20Inventory%20Post-Parrot%20-%202026-07-30.md) |
| `Post-PXE - 2026-07-30` | After deploying the Galaxy PXE and TFTP workloads on `ansible-01` | [Galaxy Inventory Post-PXE - 2026-07-30.md](Galaxy%20Inventory%20Post-PXE%20-%202026-07-30.md) |
| `Post-Blue SATA Wipe - 2026-07-31` | After adding Blue's WDC disk, resolving its duplicate `pve` VG, & leaving the disk blank | [Galaxy Inventory Post-Blue SATA Wipe - 2026-07-31.md](Galaxy%20Inventory%20Post-Blue%20SATA%20Wipe%20-%202026-07-31.md) |
| `Post-Green Expansion - 2026-07-31` | After Green joined as the fifth node, the Blue and Green memory change, and the two extended HDD tests | [Galaxy Inventory Post-Green Expansion - 2026-07-31.md](Galaxy%20Inventory%20Post-Green%20Expansion%20-%202026-07-31.md) |
| `- 2026-08-02` | After adding the internal documentation workload on Docker Main | [Galaxy Inventory - 2026-08-02.md](Galaxy%20Inventory%20-%202026-08-02.md) |
| `- 2026-08-03` | After deploying Wazuh agents across twelve new endpoints and all five Galaxy nodes | [Galaxy Inventory - 2026-08-03.md](Galaxy%20Inventory%20-%202026-08-03.md) |
| `Post-Staleness Audit - 2026-08-03` | After checking current cluster, workload, monitoring, network, media, Portainer, and Wazuh state | [Galaxy Inventory Post-Staleness Audit - 2026-08-03.md](Galaxy%20Inventory%20Post-Staleness%20Audit%20-%202026-08-03.md) |

I keep both same-day sets rather than folding the later one into the earlier filenames. Each records a state the fleet actually held, and collapsing them would delete the only record of the intermediate one to satisfy a filename.
