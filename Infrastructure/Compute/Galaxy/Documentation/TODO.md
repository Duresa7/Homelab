# Galaxy TODO

**Created:** 2026-07-14  
**Last updated:** 2026-07-18

This is my detailed backlog for the Galaxy Proxmox cluster. The root [TODO](../../../../TODO.md) links here but doesn't duplicate these steps.

## `blue-server` Recurring `pvestatd` Crashes

**Status:** Deferred known issue  
**Priority:** Schedule with a maintenance window  
**Troubleshooting record:** [Recurring `pvestatd` failure on `blue-server`](Troubleshooting-Log.md#1-recurring-pvestatd-failure-on-blue-server)

- [ ] Recheck current service, cluster, kernel, and package state before any recovery action; retain the failure window and a core dump if one becomes available.
- [ ] Review and preserve the current Lenovo BIOS settings, confirm the appropriate M910q update and rollback procedure, and update BIOS from `M1AKT35A` during an approved maintenance window.
- [ ] Run an extended offline memory test after the firmware review; record per-pass results and any failing address or module information.
- [ ] If memory testing passes, run bounded CPU verification and storage health/integrity checks, then compare results with the other Galaxy nodes.
- [ ] Restore `pvestatd` only as part of the approved work, verify node/resource status from a peer, and monitor for recurrence long enough to distinguish recovery from another temporary restart.
- [ ] After the root cause is established, decide whether a bounded systemd restart policy is appropriate as resilience against a future daemon crash.

I won't treat a successful manual restart alone as resolution; previous restarts restored status temporarily before the daemon failed again.
