# Homelab Glossary

**Created:** 2026-07-11  
**Last updated:** 2026-07-15

The ubiquitous language for work in this workspace. Use these terms with exactly these meanings in TODOs, plans, change records, and conversation. When a document conflicts with this glossary, fix the document or challenge the glossary — don't let the two drift.

## Project

A bounded effort with a definable done-state, named for its outcome: *Deploy Jellyfin*, *Migrate NetBird to an Ubuntu VM*. Projects are what the root [TODO.md](TODO.md) lists. A project enters as a TODO entry, gets a Plan, is executed as Steps, and closes with a Change Record — at which point its TODO entry moves to Recently Completed, linking that record.

A project is not a system's ongoing backlog: per-system TODO files are **backlogs** (they never "complete"), and a project is cut from a backlog when work is committed to.

A project's name is chosen once and reused verbatim across its artifacts — the TODO entry, the plan filename, the evidence folder, and the change record — so everything belonging to one project is findable by its name.

## Plan

The single document that answers *how* a project will be done: approach, sequence, and priority. One plan per project, stored with the owning system (`Documentation/Change Plans/`). The root TODO's project entry links to it. A plan's body is organized as Steps.

## Step

The unit of planned work inside a plan, numbered hierarchically like a guide:

- **Step N** is a titled phase: *Step 1 — Create the virtual machine*, *Step 2 — Set up Docker*.
- **Step N.M** is a concrete instruction within that phase: *Step 1.1 — Deploy an Ubuntu VM*, *Step 1.2 — Configure sudo privileges*.
- A new phase begins when the work genuinely shifts topic, exactly like sections of a how-to guide.

When a material step is executed, it must record its verification and evidence (see the [Documentation Standard](Governance/Documentation-Standard.md)); evidence files carry the step's number as an `S` prefix (`S01-...`, `S05A-...`).

**Retired term:** *Checkpoint* (and the `CP` file prefix) meant a verified, evidence-bearing unit of executed work. Renamed to Step on 2026-07-11; existing records and evidence were retroactively renamed from `CP` to `S`.

## Change Record

The dated, backward-looking record of a completed (or abandoned) project: what was done, what was observed, verification, rollback points, and the step evidence table. Lives in the owning system's `Documentation/Change Records/`. The durable proof that a project happened; the TODO entry and plan point to it when the project closes.

## Task

Informal word for a working session or errand ("document it in the same task"). Not a tracked planning unit — plans contain Steps, not tasks.

## Mission Control

The local-only dashboard at `Mission Control/index.html` — intentionally excluded from the public repository — is a pane of glass over active Projects, showing each one's Steps across board columns (Planning, In progress, Needs me, Done), a consolidated list of items blocked on the operator, and a plain-language report per project. It reflects the records; it is not itself a system of record. See `Mission Control/README.md` locally for the update rules.
