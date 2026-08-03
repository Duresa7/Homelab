# Platforms

**Created:** 2026-07-09  
**Last updated:** 2026-08-02

This directory holds my deployed applications & services. A platform can also keep its application source here when moving it would break imports, tooling, or deployment paths.

Each platform uses only the directories its workload needs:

- `Documentation/`: architecture, change records, runbooks, troubleshooting, & TODOs.
- `Source/`: application source when the project can keep it here safely.
- `Configuration/`: versioned service configuration & reference exports.
- `Scripts/`: deployment, migration, maintenance, & recovery automation.
- `Tests/`: automated validation.
- `Evidence/`: screenshots, exports, logs, & evidence indexes.

When I move active source, I verify its imports, tooling, & deployment path after the change.

[Docusaurus](Docusaurus/README.md) is the newest platform here. Docusaurus 3.10.2 builds the versioned Markdown source, and an unprivileged Nginx 1.29.5 container serves the static site from Docker Main on TCP 3010.
