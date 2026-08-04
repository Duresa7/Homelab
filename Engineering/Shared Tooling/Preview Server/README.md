# Preview Server

**Created:** 2026-07-25  
**Last updated:** 2026-08-04

A 91-line Node static file server so I can view repository HTML and SVG in the agent browser pane. It exists for one reason: the pane can't drive `file://` URLs. It loads such a page once and then ignores every later navigation, so an agent editing a local HTML file keeps inspecting the version it first loaded. Served over `http://127.0.0.1:8123` the same page navigates, reloads, and picks up edits normally.

## Running it

Start it through the browser pane, not by hand:

```
preview_start {"name": "preview"}
```

That reads [.claude/launch.json](../../../.claude/launch.json), which points at `serve.js` in this folder. `http://localhost:8123/` prints the folders it will serve; every other path is repo-relative, so `http://localhost:8123/Assets/Diagrams/galaxy-cluster.svg` renders that diagram.

To run it outside an agent session:

```bash
node "D:\Documents\Homelab\Engineering\Shared Tooling\Preview Server\serve.js"
```

## The two limits, and why they're there

**It binds `127.0.0.1` only.** The version I ran before 2026-07-25 called `.listen(8123)` with no host, so Node bound `0.0.0.0` and `[::]`. `netstat` confirmed both. While that server was up, `curl http://192.168.50.241:8123/Sensitive/Hardware/drive-serials.md` from anywhere on the LAN returned HTTP 200 and 2,082 bytes of full drive serial numbers. Nothing suggests anyone fetched it, but the path was open every time a preview ran.

That exposure has its own report: [Preview Server LAN-Exposed Repository Root - 2026-07-25](../../../Security/Incidents/Preview%20Server/LAN-Exposed%20Repository%20Root%20-%202026-07-25.md). It scopes what was reachable, which was all 573 files in `Sensitive/` including the pre-scrub git history bundle, and which zones could reach it, which was Internal & Vpn but not the internet.

On 2026-07-27 I also moved all three history bundles and the private redaction value map out of the Homelab tree to `D:\Documents\Redaction Map`. The preview server still keeps both protections because other private material remains under `Sensitive/`.

**It serves only the folders in `ALLOW`.** That's `Guides` and `Assets`. Assets joined on 2026-08-03 when the diagrams moved there, because a guide that references `../Assets/Diagrams/` would otherwise 404 in preview. `Mission Control` left the list on 2026-08-04 when that dashboard was deleted. The old script served the whole repository root, which is how `Sensitive/` became reachable. Requests outside the allow list return 404, and so do dotfiles and any path that resolves outside its allowed folder. Checked on 2026-08-04: `/Sensitive/Hardware/drive-serials.md`, `/CLAUDE.md`, `/Platforms/README.md`, `/Guides/../Sensitive/Hardware/drive-serials.md`, and `/Guides/.hidden` all return 404, while `/Guides/README.md` and `/Assets/Diagrams/immich-migration.svg` return 200.

Add a folder to `ALLOW` only when a preview actually needs it. Never add `Sensitive`.

## Responses carry `cache-control: no-store`

Without it the pane can hold a stale copy of a file I just edited, which wastes a verification round. With it, a reload always shows what's on disk. I confirmed that by appending a marker to a served file and re-fetching it in the same session: the byte count changed and the marker appeared.

## What the pane still can't do

Screenshots fail with `the Browser pane is not displayed, so the page is not compositing frames`, even though the page reports `visibilityState: "visible"` at 1280x720. That's the app's own panel being closed rather than anything about this server, and no server change fixes it. Text-based inspection through `read_page`, `javascript_tool`, and `computer` clicks all work.

## Related records

- [Preview Server LAN-Exposed Repository Root - 2026-07-25](../../../Security/Incidents/Preview%20Server/LAN-Exposed%20Repository%20Root%20-%202026-07-25.md), the incident that produced both limits above
- [Assets/Diagrams](../../../Assets/Diagrams/), what this now most often previews
