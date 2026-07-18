# Documentation Standard

**Created:** 2026-07-09  
**Last updated:** 2026-07-17

## Purpose

The workspace models the responsibilities normally spread across enterprise knowledge bases, source repositories, CMDBs, ticketing systems, and evidence stores. Documentation depth scales with the system's maturity, complexity, and operational importance.

This standard owns the rules for documentation depth, content, evidence, incidents, and file metadata. Workspace routing, component and platform layout, and backlog handling are owned by local agent instructions maintained outside this repository. Work-hierarchy terminology — project, plan, step — is defined in the root [glossary](../CONTEXT.md).

## Documentation Tiers

### Tier 1 — Small or Experimental

Use one deployment and operations document plus the scripts or configuration needed to reproduce the service.

### Tier 2 — Established Service

Maintain an architecture or overview document, build/change log, runbook, troubleshooting log, TODO, relevant configuration, and evidence.

### Tier 3 — Critical Infrastructure or Security Platform

Include Tier 2 records plus dependencies, recovery procedures, rollback information, validation evidence, resource specifications, and dated change records.

Actual availability or security incidents are recorded separately under `Security/Incidents/` regardless of service tier.

## Change Records

Material work should capture the date, scope, starting state, actions taken, decisions with their reasoning — why the chosen approach was taken over the alternatives considered — resulting configuration, verification, rollback points, and remaining work. A command being issued is not evidence of success; record the observed result.

## Evidence

Evidence stays with the service, infrastructure component, change, or incident that produced it. Every bounded project, job, change, or incident gets a dedicated folder beneath the owner's `Evidence/` directory. Store that job's `Screenshots/`, `Exports/`, `Logs/`, and `Evidence-Index.md` inside its project folder; do not mix unrelated jobs directly in shared artifact-type folders. Create only the artifact-type subfolders that actually contain evidence.

Use descriptive filenames with ISO dates (`YYYY-MM-DD`) when the capture date matters. The associated documentation should explain what the evidence demonstrates.

Store raw `smartctl` output unchanged under `Operations/Diagnostics/SMART/`, following the existing lowercase, hyphenated naming convention.

### Step-Based Evidence

Treat material implementation, migration, repair, and troubleshooting work as the sequence of steps laid out in the project's plan. Collect evidence as each step completes; do not wait until the project is done.

Plans number steps like a guide: `Step N` is a titled phase and `Step N.M` is a concrete instruction within it (see the [glossary](../CONTEXT.md)). Evidence filenames carry the step number as an `S` prefix — `S01`, `S03.2`, or `S05A` for work inserted between planned steps.

For a net-new deployment, capture one screenshot after each material step has been validated. A fabricated before state adds no evidence and is not required. For a modification to existing state, retain paired before-and-after captures when both states are observable and useful.

For each material step:

1. Record the action exactly as performed.
2. Capture the immediate result, including failures or partial results.
3. Perform and record an explicit verification.
4. Capture the validated resulting state.

When a graphical interface is involved, use step identifiers in filenames. Add `before` or `after` only for a meaningful existing-state pair. A single final screenshot is not a substitute for step-by-step evidence.

For terminal, CLI, SSH, API, or automation-driven work, retain a text transcript that includes:

- capture timestamp and target system;
- execution mechanism, shell, and working directory when relevant;
- the exact command or request as issued;
- complete standard output and standard error;
- exit code or structured success/error result; and
- the follow-up verification command and its result.

Terminal screenshots may supplement a transcript but do not replace the exact command and textual output. Store transcripts under the project's `Evidence/<Project - YYYY-MM-DD>/Logs/` folder and link them from the applicable step in the change record.

Maintain a step evidence table in the owning change record that links each material step to its screenshot, command transcript or request export, and verification result. If a capture is impossible or adds no information, record the reason instead of silently omitting it.

Never retain passwords, API tokens, private keys, recovery codes, or other secrets in repository files, evidence transcripts, screenshots, or captured command output. Redact secret values while preserving the command or request structure and state that redaction occurred.

## Troubleshooting Records

Document operational problems chronologically in the owning `Documentation/Troubleshooting-Log.md`. Record the symptom, exact error, failed attempts, hypotheses and tests, root cause when known, corrective action, and verification.

## Incident Reports

Store incident reports under `Security/Incidents/`, even when the affected service keeps its records under `Platforms/`. Follow the existing TeamSpeak naming convention: `<Service>-Incident-Report-YYYY-MM-DD[-Short-Description].md`.

Include metadata, executive summary, impact, affected assets, symptoms, timeline when available, findings, root cause or current hypothesis, corrective actions, validation, lessons learned, follow-ups, and closure status.

Routine troubleshooting belongs in the platform troubleshooting log. If it becomes an incident, create the incident report and cross-link both records. When an incident has supporting files, give it an incident-specific folder with `Evidence/` beneath it.

## Filename Dates and Update Metadata

Use stable, undated filenames for living documents that are expected to be maintained over time: indexes, TODOs, architecture overviews, runbooks, build logs, troubleshooting logs, and current configuration references.

Keep dates in filenames when the file represents an event or captured state: incident reports, bounded change records, migrations, audits, assessments, evidence reports, and inventory snapshots.

Every Markdown file must include both `**Created:** YYYY-MM-DD` and `**Last updated:** YYYY-MM-DD` near the top of the document. `Created` remains fixed; `Last updated` changes whenever the document content changes. Preserve any original event, implementation, migration, or snapshot date as separate metadata.
