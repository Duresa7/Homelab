# Kasm Thin Pool Exhaustion Evidence

**Created:** 2026-07-29  
**Last updated:** 2026-07-30

**Incident:** [Kasm Workspaces Thin Pool Exhaustion](../Kasm-Workspaces-Incident-Report-2026-07-29-Thin-Pool-Exhaustion.md)

| Step | Artifact | Demonstrates |
|---|---|---|
| S01 | [Diagnosis](Logs/S01%20Diagnosis%20-%202026-07-29.md) | NPM `502`, direct timeout, VM `io-error`, full thin pool, & capacity timeline |
| S02 | [Rollback and Verification](Logs/S02%20Rollback%20and%20Verification%20-%202026-07-29.md) | Baseline rollback, recovered pool capacity, PostgreSQL recovery, healthy containers, & HTTP `200` |
| S03 | [Discard Enablement and Trim](Logs/S03%20Discard%20Enablement%20and%20Trim%20-%202026-07-29.md) | Controlled shutdown, `discard=on`, guest trim result, healthy Kasm containers, & public HTTP `200` |
| S04 | [Older Snapshot Removal](Logs/S04%20Older%20Snapshot%20Removal%20-%202026-07-29.md) | Exact deletion target, one retained baseline, 2.14 GiB reclaimed, healthy Kasm, & public HTTP `200` |
| S05 | [Final Baseline Removal](Logs/S05%20Final%20Baseline%20Removal%20-%202026-07-29.md) | Last rollback point removed, zero snapshots, 4.04 GiB reclaimed, trim, healthy Kasm, & public HTTP `200` |

The controlled retry, queue stop, image cleanup, Parrot pull, automatic-update control, lane tests, and replacement snapshot are retained in the [Kasm Parrot Workspace Build-Out evidence](../../../../../Platforms/Kasm%20Workspaces/Evidence/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30/Evidence-Index.md).
