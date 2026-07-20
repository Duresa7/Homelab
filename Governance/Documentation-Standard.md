# Documentation Standard

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

## Purpose

I use this standard for change records, walkthroughs, incident reports, evidence links, filenames, & metadata. Small experiments need one operating record. A security platform needs dependencies, recovery steps, validation, resource specifications, & dated change records.

## Voice

I write in my own first person. "I changed the rule" names who did the work; "the operator changed the rule" doesn't. I don't credit an AI as author, preparer, reviewer, or commit co-author.

Every technical claim carries something a reader can check: a version, address, port, host, date, command result, file path, or measured count. Short sentences state the result. Longer sentences explain the mechanism & the check that proved it.

I use contractions in normal prose, vary sentence length, & keep headings literal. Repository prose has no emoji, em dash characters, filler, intensifiers, generic transitions, dramatic headings, repeated conclusions, or claims that end without a fact.

Examples name the missing value with placeholders such as `<YOUR_WAN_IP>`, `<YOUR_ADMIN_USERNAME>`, & `<YOUR_NETBIRD_DOMAIN>`. Markdown prose wraps each placeholder in backticks. Executable examples keep the raw placeholder when backticks would change the syntax.

## Work Terms

### Project

A project is a bounded effort with a named outcome & a definable finish. The root [TODO](../TODO.md) lists active projects. A project can have one plan, numbered steps, a same-named evidence folder, & a dated change record.

A platform TODO is an ongoing backlog, not a project. I cut a project from that backlog when I commit to a bounded piece of work.

### Plan

A plan records how I intend to complete one project: the approach, sequence, checks, rollback points, & stop conditions. It lives with the owning system under `Documentation/Change Plans/`.

### Step

A step is one unit of planned work. `Step N` names a phase; `Step N.M` records one instruction inside that phase. Evidence filenames use the same number with an `S` prefix, such as `S01`, `S03.2`, or `S05A`.

### Change Record

A change record is the dated account of work I completed or abandoned. It records the starting state, actions, observed results, verification, rollback points, & remaining work under `Documentation/Change Records/`.

### Task

Task is my informal name for a working session or errand. Plans contain steps, not tasks.

## Documentation Tiers

### Tier 1: Small or Experimental

One deployment and operations document plus the scripts or configuration needed to reproduce the service.

### Tier 2: Established Service

An architecture or overview document, build/change log, runbook, troubleshooting log, TODO, relevant configuration, and evidence.

### Tier 3: Critical Infrastructure or Security Platform

Everything in Tier 2 plus dependencies, recovery procedures, rollback information, validation evidence, resource specifications, and dated change records.

Actual availability or security incidents get their own records under `Security/Incidents/` regardless of service tier.

## Change Records

A material change record needs nine things: date, scope, starting state, actions, decisions, resulting configuration, verification, rollback points, & remaining work. A command by itself proves nothing. I record the output or state that shows what changed.

## Evidence

Evidence stays with the service, infrastructure component, change, or incident that produced it. Each bounded job gets one folder beneath the owner's `Evidence/` directory. Its `Screenshots/`, `Exports/`, `Logs/`, & `Evidence-Index.md` stay inside that folder; unrelated jobs don't share artifact directories.

One artifact is enough. I keep the file in its evidence directory, then link it beside the matching step in the build log or change record. An evidence index can catalog the set, but it can't replace the chronological walkthrough.

Each material walkthrough step uses a `Step N: <action>` heading. It records the action, exact command or UI path when retained, observed result, verification, & evidence. Screenshots appear in the applicable step, not in a gallery or collapsed block. If a step has no retained capture or transcript, I say so there.

Historical work keeps the filenames & transcript boundary it had when I performed it. I don't invent a command, rename an old artifact, or publish a withheld transcript to make a 2026-04 record look like work captured under the 2026-07 standard. The walkthrough states whether each step has the exact command, a text transcript, a screenshot, or no retained artifact.

Filenames are descriptive and carry ISO dates (`YYYY-MM-DD`) when the capture date matters. The associated documentation explains what the evidence demonstrates.

Raw `smartctl` output goes unchanged under `Operations/Diagnostics/SMART/`, following the existing lowercase, hyphenated naming convention.

### Step-Based Evidence

I collect evidence when each implementation, migration, repair, or troubleshooting step completes. Waiting until the end loses the command, failure, or UI state that explains the result.

Plans number steps like a guide: `Step N` is a titled phase and `Step N.M` is a concrete instruction within it. Evidence filenames carry the step number as an `S` prefix: `S01`, `S03.2`, or `S05A` for work inserted between planned steps.

For a new deployment, I capture the validated state after each material graphical step. A fabricated before state proves nothing. For a change to existing state, I retain a before-and-after pair when both states show a real difference.

For each material step I:

1. Record the action exactly as performed.
2. Capture the immediate result, including failures or partial results.
3. Perform and record an explicit verification.
4. Capture the validated resulting state.

When a graphical interface is involved, step identifiers go in the filenames. `before` or `after` appears only for a meaningful existing-state pair. A single final screenshot isn't a substitute for step-by-step evidence.

For terminal, CLI, SSH, API, or automation-driven work, I retain a text transcript that includes:

- capture timestamp and target system;
- execution mechanism, shell, and working directory when relevant;
- the exact command or request as issued;
- complete standard output and standard error;
- exit code or structured success/error result;
- the follow-up verification command and its result.

Terminal screenshots may supplement a transcript, but they don't replace the exact command & textual output. Transcripts live under the project's `Evidence/<Project - YYYY-MM-DD>/Logs/` folder, linked from the applicable step in the change record.

The owning change record links each screenshot, command transcript, or request export to the verification it supports. A separate evidence table is optional when the walkthrough already maps every step. If a capture adds no information or can't be made, I record the reason in that step.

When a public example requires a reader-supplied value, I use a contextual placeholder that names the value's role. I don't publish a live value or turn its omission into a separate explanation.

## Troubleshooting Records

Operational problems go in the owning `Documentation/Troubleshooting-Log.md` in time order. Each entry records the symptom, exact error, failed attempts, hypotheses, tests, root cause when known, corrective action, & verification.

## Incident Reports

Incident reports live under `Security/Incidents/`, even when the affected service keeps its records under `Platforms/`. They follow the existing TeamSpeak naming convention: `<Service>-Incident-Report-YYYY-MM-DD[-Short-Description].md`.

Each report includes metadata, summary, impact, affected assets, symptoms, timeline when available, findings, root cause or current hypothesis, corrective actions, validation, lessons, follow-ups, & closure status.

Routine troubleshooting belongs in the platform troubleshooting log. If it becomes an incident, I create the incident report and cross-link both records. When an incident has supporting files, it gets an incident-specific folder with `Evidence/` beneath it.

## Filename Dates and Update Metadata

Living documents that I maintain over time keep stable, undated filenames: indexes, TODOs, architecture overviews, runbooks, build logs, troubleshooting logs, and current configuration references.

Files that represent an event or captured state keep dates in their filenames: incident reports, bounded change records, migrations, audits, assessments, evidence reports, and inventory snapshots.

Every Markdown file carries `**Created:** YYYY-MM-DD` & `**Last updated:** YYYY-MM-DD` beneath its H1. `Created` stays fixed. `Last updated` changes with the content, while event, implementation, migration, & snapshot dates remain separate facts.
