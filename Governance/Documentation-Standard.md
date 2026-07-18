# Documentation Standard

**Created:** 2026-07-09  
**Last updated:** 2026-07-18

## Purpose

This workspace models the responsibilities normally spread across enterprise knowledge bases, source repositories, CMDBs, ticketing systems, and evidence stores. Documentation depth scales with the system's maturity, complexity, and operational importance.

This standard holds the rules I write my records to: documentation depth, content, evidence, incidents, voice, and file metadata. Workspace routing, component and platform layout, and backlog handling live in the working notes I keep outside this repository. Work-hierarchy terminology (project, plan, step) is defined in the root [glossary](../CONTEXT.md).

## Voice and Authorship

Every document in this repository is written in my first person; I never refer to myself in the third person or hide behind a role title. No AI is credited as an author, preparer, or reviewer of any document, and no AI co-author trailer goes on any git commit. Repository files carry no emoji. Prose follows my no-slop writing rules: no em dashes, no intensifiers, no filler, headings that name their content, and every claim ends on a concrete fact.

## Documentation Tiers

### Tier 1: Small or Experimental

One deployment and operations document plus the scripts or configuration needed to reproduce the service.

### Tier 2: Established Service

An architecture or overview document, build/change log, runbook, troubleshooting log, TODO, relevant configuration, and evidence.

### Tier 3: Critical Infrastructure or Security Platform

Everything in Tier 2 plus dependencies, recovery procedures, rollback information, validation evidence, resource specifications, and dated change records.

Actual availability or security incidents get their own records under `Security/Incidents/` regardless of service tier.

## Change Records

Every material piece of work captures the date, scope, starting state, actions taken, decisions with their reasoning (why I chose the approach over the alternatives I considered), resulting configuration, verification, rollback points, and remaining work. A command being issued is not evidence of success; I record the observed result.

## Evidence

Evidence stays with the service, infrastructure component, change, or incident that produced it. Every bounded project, job, change, or incident gets a dedicated folder beneath the owner's `Evidence/` directory. That job's `Screenshots/`, `Exports/`, `Logs/`, and `Evidence-Index.md` live inside its project folder; unrelated jobs never mix in shared artifact-type folders. I create only the artifact-type subfolders that actually contain evidence.

Filenames are descriptive and carry ISO dates (`YYYY-MM-DD`) when the capture date matters. The associated documentation explains what the evidence demonstrates.

Raw `smartctl` output goes unchanged under `Operations/Diagnostics/SMART/`, following the existing lowercase, hyphenated naming convention.

### Step-Based Evidence

I treat material implementation, migration, repair, and troubleshooting work as the sequence of steps laid out in the project's plan, and I collect evidence as each step completes rather than after the project is done.

Plans number steps like a guide: `Step N` is a titled phase and `Step N.M` is a concrete instruction within it (see the [glossary](../CONTEXT.md)). Evidence filenames carry the step number as an `S` prefix: `S01`, `S03.2`, or `S05A` for work inserted between planned steps.

For a net-new deployment, I capture one screenshot after each material step has been validated. A fabricated before state adds no evidence and is not required. For a modification to existing state, I retain paired before-and-after captures when both states are observable and useful.

For each material step I:

1. Record the action exactly as performed.
2. Capture the immediate result, including failures or partial results.
3. Perform and record an explicit verification.
4. Capture the validated resulting state.

When a graphical interface is involved, step identifiers go in the filenames. `before` or `after` appears only for a meaningful existing-state pair. A single final screenshot is not a substitute for step-by-step evidence.

For terminal, CLI, SSH, API, or automation-driven work, I retain a text transcript that includes:

- capture timestamp and target system;
- execution mechanism, shell, and working directory when relevant;
- the exact command or request as issued;
- complete standard output and standard error;
- exit code or structured success/error result; and
- the follow-up verification command and its result.

Terminal screenshots may supplement a transcript but do not replace the exact command and textual output. Transcripts live under the project's `Evidence/<Project - YYYY-MM-DD>/Logs/` folder, linked from the applicable step in the change record.

The owning change record keeps a step evidence table linking each material step to its screenshot, command transcript or request export, and verification result. If a capture is impossible or adds no information, I record the reason instead of silently omitting it.

Passwords, API tokens, private keys, recovery codes, and other secrets never land in repository files, evidence transcripts, screenshots, or captured command output. I redact secret values while preserving the command or request structure, and I state that redaction occurred.

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
