# Platforms

**Created:** 2026-07-09  
**Last updated:** 2026-07-31

This directory holds my deployed applications & services. A platform can also keep its application source here when moving it would break imports, tooling, or deployment paths.

Each platform uses only the directories its workload needs:

- `Documentation/`: architecture, change records, runbooks, troubleshooting, & TODOs.
- `Source/`: application source when the project can keep it here safely.
- `Configuration/`: versioned service configuration & reference exports.
- `Scripts/`: deployment, migration, maintenance, & recovery automation.
- `Tests/`: automated validation.
- `Evidence/`: screenshots, exports, logs, & evidence indexes.

When I move active source, I verify its imports, tooling, & deployment path after the change.

[Galaxy PXE](Galaxy%20PXE/README.md) is the newest platform here. Its service runs on `ansible-01`, while this platform owns the machine registry, installer policy, deployment source, tests, troubleshooting, and evidence. Green completed the repaired physical run and joined Galaxy as its fifth node on 2026-07-31.
