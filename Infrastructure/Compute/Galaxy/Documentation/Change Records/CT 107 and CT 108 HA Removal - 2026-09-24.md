# CT 107 and CT 108 HA Removal

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Observed on:** 2026-09-24  
**Status:** Recorded after the fact; the removal itself has no earlier record  
**Affected systems:** Proxmox HA resources `ct:107` (`docker-network`) and `ct:108` (`docker-blue`), HA rule `pin-blue-local-storage`, Galaxy cluster

## What changed

Neither container is an HA resource any more, and the strict node-affinity rule that pinned them to `blue-server` is gone. I made no record when that happened. I found it on 2026-09-24 while reading the cluster back for the inventories.

| Date | Source | HA state |
| --- | --- | --- |
| 2026-09-04 | [PVE 9.2.11 Package Update](PVE%209.2.11%20Package%20Update%20-%202026-09-04.md) | `ha-manager status` showed `ct:107` and `ct:108` started on Blue |
| 2026-09-06 | [Documentation Staleness Audit](../../../../../Operations/Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md) | The HA rule still pinned CT 107 and CT 108 to `blue-server` |
| 2026-09-23 | [win11-dev Grey Migration](win11-dev%20Grey%20Migration%20-%202026-09-23.md) | HA had no configured resources |
| 2026-09-24 | Readback from `grey-server` through SSH Manager | `ha-manager config` and `ha-manager rules config` returned nothing |

So the removal happened between 2026-09-06 and 2026-09-23. On 2026-09-24 `ha-manager status` reported quorum OK, the CRM master on `green-server` idle since 2026-09-09, and all five LRMs idle. An idle master since 2026-09-09 fits a removal between 2026-09-06 and 2026-09-09, but it does not prove the date.

## Current state

- `ha-manager config` is empty. No guest in Galaxy is HA-managed.
- `ha-manager rules config` is empty. `pin-blue-local-storage` no longer exists.
- CT 107 and CT 108 run on `blue-server` with `onboot` set, so they start when Blue boots. Their root volumes stay on Blue's node-local `local-lvm`.

## What it means

With node-local disks and a Blue-only rule, HA could only ever restart these two containers on Blue. It could not move them. Without HA, a Blue outage still stops both until Blue returns, which is the same result, and the relocation path that stranded them on 2026-07-20 no longer exists. [HA Local-Storage Stranding](../../../../../Security/Incidents/Galaxy/HA%20Local%20Storage%20Stranding%20-%202026-07-20.md).

The [shared storage research](../Shared%20Storage%20Migration%20and%20Load%20Balancing%20Research%20-%202026-08-23.md) of 2026-08-23 counted these two as Galaxy's only HA resources. That count is now zero.

## Verification

The [LXC inventory](../../../../../Operations/Inventory/Galaxy/LXCs.md) and the [cluster architecture](../Architecture/Cluster%20Architecture.md) now record HA as disabled for every guest. No Proxmox task-log entry for the removal was read; searching `/var/log/pve/tasks/` on `grey-server` for `ha-manager` operations between 2026-09-06 and 2026-09-23 would date it.
