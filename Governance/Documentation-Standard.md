# Documentation Standard

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

## Purpose

This standard defines how I write change records, walkthroughs, incident reports, evidence references, and file metadata. Documentation depth scales with the system's maturity, complexity, and operational importance.

## Voice

I write in my own first person. I don't hide work behind terms such as "the operator," and I don't credit an AI as author, preparer, reviewer, or commit co-author.

Every technical claim carries a checkable detail: a version, address, port, host, date, command result, file path, or measured count. Short sentences state the result. Longer sentences explain the mechanism & the check that proved it.

I use contractions in normal prose, vary sentence length, & keep headings literal. Repository prose has no emoji, em dash characters, filler, intensifiers, generic transitions, dramatic headings, repeated conclusions, or claims that end without a fact.

Examples use contextual angle-bracket placeholders such as `<YOUR_WAN_IP>`, `<YOUR_ADMIN_USERNAME>`, & `<YOUR_NETBIRD_DOMAIN>`. Markdown prose wraps each placeholder in backticks. Executable examples keep the raw placeholder when backticks would change the syntax.

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

Every material piece of work captures the date, scope, starting state, actions taken, decisions with their reasoning (why I chose the approach over the alternatives I considered), resulting configuration, verification, rollback points, & remaining work. A command by itself proves nothing. I record the output or state that shows the result.

## Evidence

Evidence stays with the service, infrastructure component, change, or incident that produced it. Every bounded project, job, change, or incident gets a dedicated folder beneath the owner's `Evidence/` directory. That job's `Screenshots/`, `Exports/`, `Logs/`, & `Evidence-Index.md` live inside its project folder; unrelated jobs never mix in shared artifact-type folders. I create only artifact-type subfolders that contain evidence.

The evidence directory is the durable source, not the only place where I present the evidence. I write the owning build log or change record as a chronological walkthrough & place each screenshot beside the result it demonstrates. An evidence index can catalog the complete set, but it doesn't replace the walkthrough. I link to the same evidence file instead of copying it into a second location.

Each material walkthrough step uses a `Step N: <action>` heading & records the action, the exact command or UI path when retained, the observed result, the verification, & the evidence. I display screenshots directly in the step instead of hiding them in collapsible blocks or collecting them in a gallery. When a step has no retained capture or transcript, I state why in that step. A walkthrough with an explicit evidence entry & direct artifact link for every step serves as its own step evidence index; a separate summary table is optional.

Historical work keeps the evidence filenames & transcript boundary that existed when I performed it. I don't invent commands, relabel old files, or publish a quarantined transcript to make an older record look compliant with a newer standard. The walkthrough maps each legacy artifact to its step & states whether the public record contains the exact command, text transcript, or capture. New work follows the current naming & transcript rules below.

Filenames are descriptive and carry ISO dates (`YYYY-MM-DD`) when the capture date matters. The associated documentation explains what the evidence demonstrates.

Raw `smartctl` output goes unchanged under `Operations/Diagnostics/SMART/`, following the existing lowercase, hyphenated naming convention.

### Step-Based Evidence

I treat material implementation, migration, repair, & troubleshooting work as the sequence of steps laid out in the project's plan. I collect evidence as each step completes, not after the project is done.

Plans number steps like a guide: `Step N` is a titled phase and `Step N.M` is a concrete instruction within it. Evidence filenames carry the step number as an `S` prefix: `S01`, `S03.2`, or `S05A` for work inserted between planned steps.

For a net-new deployment, I capture one screenshot after each material step has been validated. A fabricated before state adds no evidence & isn't required. For a modification to existing state, I retain paired before-and-after captures when both states are observable & useful.

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

The owning change record keeps evidence with each material walkthrough step, linking the screenshot, command transcript, or request export to its verification result. A separate step evidence table is optional when the walkthrough itself provides that mapping. If a capture is impossible or adds no information, I record the reason instead of silently omitting it.

When a public example requires a reader-supplied value, I use a contextual placeholder that names the value's role. I don't publish a live value or turn its omission into a separate explanation.

## Troubleshooting Records

Operational problems go chronologically in the owning `Documentation/Troubleshooting-Log.md`: the symptom, exact error, failed attempts, hypotheses and tests, root cause when known, corrective action, and verification.

## Incident Reports

Incident reports live under `Security/Incidents/`, even when the affected service keeps its records under `Platforms/`. They follow the existing TeamSpeak naming convention: `<Service>-Incident-Report-YYYY-MM-DD[-Short-Description].md`.

Each report includes metadata, executive summary, impact, affected assets, symptoms, timeline when available, findings, root cause or current hypothesis, corrective actions, validation, lessons learned, follow-ups, and closure status.

Routine troubleshooting belongs in the platform troubleshooting log. If it becomes an incident, I create the incident report and cross-link both records. When an incident has supporting files, it gets an incident-specific folder with `Evidence/` beneath it.

## Filename Dates and Update Metadata

Living documents that I maintain over time keep stable, undated filenames: indexes, TODOs, architecture overviews, runbooks, build logs, troubleshooting logs, and current configuration references.

Files that represent an event or captured state keep dates in their filenames: incident reports, bounded change records, migrations, audits, assessments, evidence reports, and inventory snapshots.

Every Markdown file carries both `**Created:** YYYY-MM-DD` and `**Last updated:** YYYY-MM-DD` near the top of the document. `Created` stays fixed; `Last updated` changes whenever the content changes. Original event, implementation, migration, and snapshot dates stay as separate metadata.
