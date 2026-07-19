# Platforms

**Created:** 2026-07-09  
**Last updated:** 2026-07-18

Platforms holds my deployed applications and services. A platform folder can also carry its own application source, because this workspace doubles as a development workspace.

I use only the subfolders a platform justifies:

- `Documentation/`: architecture, build/change logs, runbooks, troubleshooting, and TODOs
- `Source/`: application source when separating it is safe for that project
- `Configuration/`: versioned service configuration and reference exports
- `Scripts/`: deployment, migration, maintenance, and recovery automation
- `Tests/`: automated validation
- `Evidence/`: screenshots, exports, logs, and an evidence index

I don't move active source just to satisfy this shape when doing so would break imports, tooling, or deployment paths. I refactor an active project deliberately and verify it afterward.

