# Galaxy TODO

**Created:** 2026-07-14  
**Last updated:** 2026-07-20

This backlog contains one deferred Galaxy issue: recurring `pvestatd` crashes on `blue-server`. The root [TODO](../../../../TODO.md) links here without copying the six recovery steps.

## `blue-server` Recurring `pvestatd` Crashes

**Status:** Deferred known issue  
**Priority:** Schedule with a maintenance window  
**Troubleshooting record:** [Recurring `pvestatd` failure on `blue-server`](Troubleshooting-Log.md#1-recurring-pvestatd-failure-on-blue-server)

- [ ] Recheck service, cluster, kernel, & package state before recovery; retain the failure window and a core dump if one becomes available.
- [ ] Record the current Lenovo BIOS settings, confirm the M910q update and rollback procedure, & update BIOS from `M1AKT35A` during a maintenance window.
- [ ] Run an extended offline memory test after the firmware review; record per-pass results and any failing address or module information.
- [ ] If memory passes, run a fixed-duration CPU test plus storage health & integrity checks, then compare the results with the other Galaxy nodes.
- [ ] Restore `pvestatd`, verify node and resource status from a peer, & monitor for another crash beyond the prior failure window.
- [ ] After finding the root cause, decide whether a systemd restart policy should cover a later daemon crash.

A manual restart isn't resolution. Previous restarts restored status, then `pvestatd` failed again.
