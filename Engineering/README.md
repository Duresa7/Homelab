# Engineering

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

Engineering holds shared automation, reusable tooling, and projects that haven't become operated services. One project lives here today.

| Project | What it is |
|---|---|
| [Preview Server](Preview%20Server/README.md) | A 90-line Node static server on `127.0.0.1:8123` so my editor's preview browser pane can render repository HTML and SVG, which it can't do over `file://` |

Cross-owner automation belongs in its own project folder here, such as `Engineering/<Project>/`. Once I operate a project as a service, its primary home moves to `Platforms/<Service>/`; service-specific scripts move with it.
