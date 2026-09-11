# Galaxy Inventory

**Created:** 2026-07-08  
**Last updated:** 2026-09-11

This index points to the living records that hold Galaxy's current state. The dated records in the snapshot sequence below preserve earlier states and are not the current answer.

I refreshed the living VM record on 2026-08-20 after confirming VM 117 `supabase-01` had been deleted and cleaning its remaining references. I did not create another dated inventory snapshot because the living files are the current-state view.

On 2026-09-06 I audited all four living records against the cluster: `pvesh get /cluster/resources`, every guest configuration file, the storage status on each node, and the running services on all 13 workload guests. The VM record had missed the 2026-08-26 `kali-pen` rebuild as VM 102, the LXC record had missed `docker-blue` growing to two vCPUs and 2 GiB on 2026-09-01, and the service record carried several superseded versions. Each is corrected in its living file; the findings and verification are in [Documentation Staleness Audit - 2026-09-06](../../Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md).

On 2026-09-08 I updated the VM and node records for `ubuntu-dev`'s move to M.2 NVMe storage and removal of its two unused SSD source volumes. The [change record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20NVMe%20Storage%20Move%20-%202026-09-08.md) includes live verification and recovered space.

On 2026-09-10 I set VM 105 `ubuntu-dev` on Grey to 12 GiB pending, leaving its running allocation at 16 GiB. I did not restart anything, so the 4 GiB reduction has not yet released host capacity. The [memory assessment and change record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20Memory%20Assessment%20-%202026-09-10.md) holds the verification.

On 2026-09-11 I completed app-01's 64 GiB boot disk replacement on Grey and removed its old 200 GiB volume. The [change record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/app-01%2064%20GiB%20Boot%20Disk%20Replacement%20-%202026-09-11.md) holds verification and the pre-existing Wazuh connection issue. I then completed both guests' move to Purple's NVMe-backed `local-lvm`, verified services and monitoring, and confirmed their source volumes absent on Grey. Wazuh connectivity is restored for all 16 remote agents. The [migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/app-01%20and%20edge-01%20Purple%20Migration%20-%202026-09-11.md) holds final verification.

## Current state

| File | Contents |
| --- | --- |
| [Nodes](../../../Infrastructure/Hardware/Nodes.md) | Current Galaxy node hardware, physical storage, and cluster-storage state |
| [VMs](VMs.md) | Current QEMU virtual machines and templates |
| [LXCs](LXCs.md) | Current Linux containers |
| [Services](Services.md) | Current workloads, monitoring targets, and service versions |

## Snapshot sequence

Two complete sets carry the date 2026-07-28 because I changed the fleet twice that day. Two also carry 2026-08-03 because the audit superseded the earlier service record without rewriting it. Read the sequence in order; the post-staleness audit set is the most recent capture. For current state, use the living records above rather than the last snapshot in this list.

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
