# Root Filesystem Expansion Evidence

**Created:** 2026-08-30  
**Last updated:** 2026-08-30

Supports [Root Filesystem Expansion - 2026-08-29](../../Documentation/Change%20Records/Root%20Filesystem%20Expansion%20-%202026-08-29.md).

Step numbers run S01 to S21 across six evidence folders. This folder holds S04 and S05. All captures are headless, so no pointer appears in any of them.

| Step | Capture | What it shows |
|---:|---|---|
| 4 | [Root filesystem after expansion](Screenshots/S04-Splunk-Root-Filesystem-After-Expansion-2026-08-29.png) | Splunk's own partition view reporting `/` at 141.5 GB with 94.9 GB free. This is the figure Splunk reads for its disk-space guard, so it is the one that governs whether it keeps indexing. |
| 5 | [Index counts intact](Screenshots/S05-Splunk-Index-Counts-Intact-After-Rebuild-2026-08-29.png) | Event counts per index after the reboot, showing `netfw` and `netops` carried through unchanged. It also shows the internal indexes at 22.1 GB against 99 MB of real data, which is the finding in the record. |
