# Platforms

**Created:** 2026-07-09  
**Last updated:** 2026-07-09

Platforms contains deployed applications and services. A platform folder may also contain its application source because this workspace intentionally doubles as a development workspace.

Use only the subfolders justified by the platform:

- `Documentation/` — architecture, build/change logs, runbooks, troubleshooting, and TODOs
- `Source/` — application source when separating it is safe for that project
- `Configuration/` — versioned service configuration and reference exports
- `Scripts/` — deployment, migration, maintenance, and recovery automation
- `Tests/` — automated validation
- `Evidence/` — screenshots, exports, logs, and an evidence index

Do not move active source merely to satisfy this shape when doing so would break imports, tooling, or deployment paths. Refactor an active project deliberately and verify it afterward.

