# Galaxy Grey Server HA Daemon Restoration - 2026-07-22

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Implementation date:** 2026-07-22  
**Status:** Complete  
**Primary owner:** Infrastructure/Compute/Galaxy (Proxmox HA)  
**Affected systems:** `pve-ha-lrm.service`, `pve-ha-crm.service`, & `watchdog-mux.service` on `grey-server`; no guest or HA resource configuration change

## Scope

I restored the default enabled & running state of Grey's Proxmox HA Local Resource Manager and Cluster Resource Manager. Proxmox had retained Grey's last LRM heartbeat from `2025-08-22 23:47:05 EDT`, even though the node remained online in Corosync.

## Starting State

- Galaxy had four Corosync members, four votes, quorum 3, & active CRM master `purple-server`.
- Grey's `pve-ha-lrm` & `pve-ha-crm` units were loaded but `inactive`, `dead`, & `disabled`. Their installed presets were enabled.
- `/etc/pve/nodes/grey-server/lrm_status` had not changed since `2025-08-22 23:47:05 -0400` and contained `mode: restart` with `state: wait_for_agent_lock`.
- `ha-manager status` showed Grey as `old timestamp - dead?` with `watchdog standby`.
- CT 107 & CT 108 were started on Blue and constrained there by `pin-blue-local-storage`.

The complete starting-state command & output are in the [S01 pre-change transcript](../../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S01-grey-ha-prechange-2026-07-22.txt).

## Decisions

- I restored both HA units because the package preset was enabled, the peer HA daemons were active, & neither Grey unit showed a failure result.
- I left `resources.cfg`, CT 107, CT 108, & `pin-blue-local-storage` unchanged. Neither HA resource belonged on Grey.
- I didn't edit or remove `lrm_status`. A running LRM had to replace the stale heartbeat through the normal pmxcfs path.
- I checked the result from Grey & Purple, then confirmed both HA containers directly on Blue.

## Step 1: Confirm the stale LRM state

I checked quorum, both Grey unit states, HA status, HA resources, & HA rules at 02:21:54 EDT. The cluster had four votes; Grey's HA units were disabled & inactive; CT 107 and CT 108 were started on Blue. This reproduced the fault without changing cluster state.

**Evidence:** [S01 pre-change transcript](../../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S01-grey-ha-prechange-2026-07-22.txt)

## Step 2: Enable and start both HA units

I ran:

```text
systemctl enable --now pve-ha-lrm pve-ha-crm
```

Systemd returned exit 0 & created both `multi-user.target.wants` links. The CRM started at 02:22:12 EDT; the LRM started one second later.

**Evidence:** [S02 service restoration transcript](../../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S02-grey-ha-enable-services-2026-07-22.txt)

## Step 3: Verify HA state and workloads

Both units reported `enabled`, `active`, & `running`. `watchdog-mux` also became active. Grey rewrote its LRM status file at 02:22:28 EDT, and both Grey & Purple reported a current `lrm grey-server (idle, watchdog standby, ...)` entry instead of the 2025 dead timestamp.

I repeated the HA query at 02:23:16 EDT. Grey's heartbeat advanced to 02:23:13, both HA units remained active, the HA journal held no warning-or-higher entries since startup, & Purple returned the same Grey timestamp. Blue reported CT 107 & CT 108 as `running`.

**Evidence:** [S03 after-change verification transcript](../../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S03-grey-ha-verification-2026-07-22.txt)

## Resulting Configuration

| Item | Result |
|---|---|
| `pve-ha-lrm.service` | enabled; active/running |
| `pve-ha-crm.service` | enabled; active/running |
| `watchdog-mux.service` | active/running |
| Grey LRM state | idle; current heartbeat; watchdog standby because Grey hosts no HA resource |
| CRM master | `purple-server` |
| Fencing | armed; CRM watchdog active |
| HA resources | CT 107 & CT 108 started on Blue |
| HA placement rule | `pin-blue-local-storage` unchanged |

## Verification

| Check | Observed result |
|---|---|
| Grey unit persistence | both units `enabled` |
| Grey unit runtime | both units `active`; `watchdog-mux` active |
| LRM heartbeat | 2025-08-22 timestamp replaced; heartbeat advanced from 02:22:28 to 02:23:13 EDT |
| Cross-node view | Purple reported Grey idle with the same current timestamp |
| Quorum | four nodes, four votes, quorum 3, quorate |
| Workloads | CT 107 & CT 108 remained started/running on Blue |
| HA journal | no entries at warning or higher after startup |

## Root Cause

Grey's disabled LRM & CRM units caused the stale HA heartbeat. The last `lrm_status` write occurred on 2025-08-22 with mode `restart`, but that mode covers both a daemon restart and a conditional-policy node reboot; it doesn't identify when or why systemd enablement was removed. The disabled state survived later boots and package upgrades, so the old entry remained visible for 334 days. Retained logs begin on 2026-02-16, and neither shell history nor repository records identify the command or caller.

## Rollback

If either daemon causes a new fault, I can stop both with `systemctl stop pve-ha-lrm pve-ha-crm` while I collect the unit journals. Disabling them again would recreate this fault, so `systemctl disable` isn't a normal rollback. No resource or rule edit needs reversal.

## Remaining Work

The repair is complete. The 2025 actor can't be reconstructed from the retained records, and no open technical step depends on that attribution.

## Related Record

I added the chronological diagnosis & repair summary to the [Grey HA troubleshooting record](../Troubleshooting/Disabled%20HA%20Daemons%20on%20grey-server%20-%202026-07-22.md).
