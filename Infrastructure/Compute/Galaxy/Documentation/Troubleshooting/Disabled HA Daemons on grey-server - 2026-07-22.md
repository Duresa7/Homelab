# Disabled HA Daemons on `grey-server`

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-22  
**Owner:** Galaxy / Proxmox HA  
**Status:** Resolved

## Symptom and impact

Proxmox HA reported `lrm grey-server (old timestamp - dead?, watchdog standby, Fri Aug 22 23:47:05 2025)`. All four nodes returned the same status, so the date came from cluster state rather than a browser cache. Grey remained online in Corosync & continued to cast one vote, but its Local Resource Manager wasn't publishing heartbeats or available to manage an HA resource placed on the node.

No guest went down. The only HA resources were CT 107 `docker-network` & CT 108 `docker-blue`; both remained started on `blue-server` under the `pin-blue-local-storage` node-affinity rule.

## Tests and root cause

Grey's clock read `2026-07-22T02:11:25-04:00`, ruling out a current clock error. `systemctl show` identified the fault: `pve-ha-lrm.service` & `pve-ha-crm.service` were `inactive`, `dead`, & `disabled`, although each installed unit carried `preset: enabled`. Both reported `Result=success` with no current-boot start timestamp, so neither daemon had crashed.

`/etc/pve/nodes/grey-server/lrm_status` was valid JSON with mode `restart`, state `wait_for_agent_lock`, & modification time `2025-08-22 23:47:05 -0400`. The installed `PVE::HA::LRM` code uses mode `restart` for a daemon restart and for a conditional-policy node reboot, so that field doesn't distinguish the two paths. The retained journal begins on 2026-02-16 & contains no Grey HA daemon entries before this repair; the repository & retained root history contain no matching disable record. I can prove the disabled units caused the stale heartbeat, but the command, caller, & date of the disable are no longer retained.

The stale timestamp file was readable, and the other three nodes updated their LRM files normally. That ruled out pmxcfs corruption. `watchdog-mux` was inactive because neither Grey HA daemon had requested it; `watchdog standby` was a result of the stopped LRM, not a watchdog failure.

## Corrective action

I ran `systemctl enable --now pve-ha-lrm pve-ha-crm` on `grey-server`. Systemd created both `multi-user.target.wants` links & started the CRM at 02:22:12 EDT and the LRM at 02:22:13 EDT. I didn't edit `/etc/pve/ha/resources.cfg`, change `pin-blue-local-storage`, move a guest, or delete the stale LRM status file.

## Verification

- Both Grey units report `enabled`, `active`, & `running`; `watchdog-mux` is active.
- Grey rewrote `lrm_status` at 02:22:28 EDT. `ha-manager status` changed its entry to `lrm grey-server (idle, watchdog standby, Wed Jul 22 02:22:28 2026)`.
- A second check at 02:23:16 EDT showed another current Grey heartbeat at 02:23:13. Purple independently returned the same Grey state.
- The Galaxy cluster remained quorate with four votes during the repair. Purple remained CRM master & fencing remained armed.
- CT 107 & CT 108 remained `started` in HA and `running` under `pct status` on Blue.
- Grey logged no warning, error, critical, alert, or emergency entries for either HA daemon after startup.

## Related records

- [Grey Server HA Daemon Restoration change record](../Change%20Records/Galaxy%20Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22.md)
- [Pre-change transcript](../../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S01-grey-ha-prechange-2026-07-22.txt)
- [Service restoration transcript](../../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S02-grey-ha-enable-services-2026-07-22.txt)
- [After-change verification transcript](../../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S03-grey-ha-verification-2026-07-22.txt)
