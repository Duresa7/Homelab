# Platforms

**Created:** 2026-07-09  
**Last updated:** 2026-07-24

This directory holds my deployed applications & services. A platform can also keep its application source here when moving it would break imports, tooling, or deployment paths.

Each platform uses only the directories its workload needs:

- `Documentation/`: architecture, change records, runbooks, troubleshooting, & TODOs.
- `Source/`: application source when the project can keep it here safely.
- `Configuration/`: versioned service configuration & reference exports.
- `Scripts/`: deployment, migration, maintenance, & recovery automation.
- `Tests/`: automated validation.
- `Evidence/`: screenshots, exports, logs, & evidence indexes.

When I move active source, I verify its imports, tooling, & deployment path after the change.

[Kasm Workspaces](Kasm%20Workspaces/README.md) is the newest platform here. Kasm 1.19.0 Community Edition runs on `kasm-01` at `192.168.80.30` as of 2026-07-24. The platform is live & verified; attaching the isolated lab VLANs to its sessions is still open.

