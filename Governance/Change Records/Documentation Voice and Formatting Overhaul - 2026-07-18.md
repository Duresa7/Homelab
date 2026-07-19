# Documentation Voice and Formatting Overhaul - 2026-07-18

**Created:** 2026-07-18  
**Last updated:** 2026-07-18

## Scope

I rewrote the tracked documentation across the whole repository so every record reads as my own first-person work, renders cleanly on GitHub, and carries no AI-authorship or agent-instruction material. I did not change the repository structure, rename any tracked file, or alter any `REDACTED_*` placeholder. I re-voiced and reformatted prose only; commands, configuration excerpts, captured output, and table values stayed verbatim.

## Why

The repository is my public homelab portfolio. Much of it had been written in a third-person or tooling voice that named a generic operator or credited an AI model as a document's author, a few records narrated an automation process rather than the work, and no screenshots rendered inline because every image was linked rather than embedded. I wanted the whole repository to read as records I keep for myself and reviewers, with working links and visible evidence.

## What I changed

- **Voice.** Converted third-person and passive documentation to first person across every tracked area: Governance, Architecture, Infrastructure (Galaxy, UniFi, Cloudflare, Hardware), Platforms (Splunk, NetBird, Nginx Proxy Manager, Media Stack, Ansible, Termix, Wazuh, Prometheus, Portainer, TNIO, OpenClaw, TeamSpeak, Immich), Operations, and Security. Removed every generic third-person reference to myself.
- **AI attribution.** Removed the model-authorship line from the TNIO fixes report and the AI preparer rows from the OpenClaw docs and the TeamSpeak UDP relay incident report. Added a rule to the [Documentation Standard](../Documentation-Standard.md) and to my local working notes: documentation is written in my first person, no AI is credited as author, preparer, or reviewer, and no AI co-author trailer goes on any commit.
- **Agent-instruction material.** Removed the `Agent Instructions Consolidation` change record from the public tree; it documented local agent configuration that does not belong in the portfolio. Re-voiced records that referenced local agent-instruction files to describe the outcome in repository terms.
- **Research docs.** Rewrote the [persistent remote development research](../../Architecture/Remote-AI-Development-Research-2026-07-12.md) and the two Media Stack research notes as my own research and decisions, with inline citations consolidated into numbered Sources sections.
- **Formatting.** Removed em dashes and emoji from tracked documents, replaced dramatic or vague headings with descriptive ones, and cut filler and intensifier language.
- **Links.** Removed references to step-evidence transcripts, exports, and evidence indexes that are retained offline and are not part of the published tree, keeping the factual claims those artifacts supported.
- **Images.** Converted linked screenshots to inline embeds, using collapsible galleries where a record carries five or more, so evidence renders on GitHub. Placed previously unreferenced screenshots (the Splunk build set, the NetBird first-peer set, the Wazuh re-enrollment capture, and a node memory photo) into the records they evidence.
- **Root README.** Rebuilt as a portfolio landing page: a factual badge row, a table of contents, an architecture diagram, a repository-layout table, a selected-records table, and a roadmap drawn from the central TODO.
- **Diagrams.** Added `Architecture/Diagrams/` with an exported SVG lab-overview diagram and a remote-development flow diagram, each kept alongside its editable source, replacing an earlier inline diagram markup.

## Verification

- A repository link check confirmed every relative link resolves to a tracked file with exact case, and that no tracked image is left unreferenced.
- A banned-pattern scan over the tracked Markdown confirmed no remaining third-person self-references, AI-authorship rows, em dashes, or emoji, and I reviewed the remaining writing-style matches by hand.
- Every changed file carries `**Last updated:** 2026-07-18` with its original `**Created:**` date preserved.
- I confirmed no commit on this work carries an AI co-author trailer.

## Rollback

All work was done on the `docs-overhaul` branch as a series of per-area commits, so any single area can be reverted independently, and the whole change can be dropped by resetting the branch before it merges to `main`.
