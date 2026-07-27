# Engineering

**Created:** 2026-07-09  
**Last updated:** 2026-07-26

Engineering holds shared automation, reusable tooling, & projects that haven't become operated services. One project lives here today.

| Project | What it is |
|---|---|
| [Shared Tooling/Preview Server](Shared%20Tooling/Preview%20Server/README.md) | A 90-line Node static server on `127.0.0.1:8123` so the agent browser pane can render repository HTML & SVG, which it can't do over `file://` |

Cross-owner automation belongs in `Engineering/Automation/`. Once I operate a project as a service, its primary home moves to `Platforms/<Service>/`; service-specific scripts move with it.
