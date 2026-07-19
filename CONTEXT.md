# Homelab Glossary

**Created:** 2026-07-11  
**Last updated:** 2026-07-18

These are the terms I use with fixed meanings across my TODOs, plans, and change records. I wrote them down after catching myself using "project", "plan", and "task" interchangeably; pinning the vocabulary keeps every record findable by name.

## Project

A bounded effort with a definable done-state, named for its outcome: *Deploy Jellyfin*, *Migrate NetBird to an Ubuntu VM*. Projects are what the root [TODO.md](TODO.md) lists. A project enters as a TODO entry, gets a Plan, is executed as Steps, and closes with a Change Record; at that point its TODO entry moves to Recently Completed, linking that record.

A project is not a system's ongoing backlog. Per-system TODO files are **backlogs** (they never "complete"), and I cut a project from a backlog when I commit to the work.

I pick a project's name once and reuse it verbatim across its artifacts: the TODO entry, the plan filename, the evidence folder, and the change record. Everything belonging to one project is findable by its name.

## Plan

The single document that answers *how* a project will be done: approach, sequence, and priority. One plan per project, stored with the owning system (`Documentation/Change Plans/`). The root TODO's project entry links to it. A plan's body is organized as Steps.

## Step

The unit of planned work inside a plan, numbered hierarchically like a guide:

- **Step N** is a titled phase: *Step 1 - Create the virtual machine*, *Step 2 - Set up Docker*.
- **Step N.M** is a concrete instruction within that phase: *Step 1.1 - Deploy an Ubuntu VM*, *Step 1.2 - Configure sudo privileges*.
- A new phase begins when the work genuinely shifts topic, exactly like sections of a how-to guide.

When I execute a material step, I record its verification per the [Documentation Standard](Governance/Documentation-Standard.md); evidence files carry the step's number as an `S` prefix (`S01-...`, `S05A-...`).

**Retired term:** *Checkpoint* (and the `CP` file prefix) meant a verified, evidence-bearing unit of executed work. I renamed it to Step on 2026-07-11 and retroactively renamed existing records and evidence from `CP` to `S`.

## Change Record

The dated, backward-looking record of a completed (or abandoned) project: what I did, what I observed, verification, rollback points, and the step evidence. Lives in the owning system's `Documentation/Change Records/`. It is the durable proof that a project happened; the TODO entry and plan point to it when the project closes.

## Task

My informal word for a working session or errand ("document it in the same task"). Not a tracked planning unit; plans contain Steps, not tasks.
