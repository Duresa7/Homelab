# Platform Working Tree Reorganization

**Created:** 2026-07-09  
**Last updated:** 2026-07-16

**Date:** 2026-07-09  
**Status:** Complete  
**Scope:** TNIO AI Bot and `REDACTED_INTERNAL_DOMAIN_003` Windows platform working trees

## Objective

Finish the enterprise workspace migration by separating the previously mixed TNIO and Windows working trees into documentation, source, configuration, scripts, tests, evidence, and retained artifacts. Path compatibility with the former local working-tree layout was explicitly not required.

## TNIO AI Bot

The TNIO platform previously held source, duplicate implementations, scratch work, tests, documentation, audits, caches, logs, agent worktrees, service configuration, and a deployment bundle at the platform root.

The resulting layout is:

- `Source/lore-rag/` — primary source snapshot
- `Source/lore-rag-remote/` — remote source snapshot
- `Source/Experimental/lore-rag/` — experimental implementation
- `Source/Legacy/` — former root-level implementations
- `Tests/` — legacy evaluation and remote accuracy tests
- `Documentation/` — product, reference, and dated change records
- `Configuration/` — systemd and remote-state configuration snapshots
- `Evidence/` — corpus audits, remote snapshots, and logs
- `Artifacts/` — deployment bundles, caches, and retained agent worktrees/state

References to the deployed path `/home/REDACTED_DEPLOYMENT_USER/lore-rag` were preserved because they describe the Linux runtime rather than the local Windows workspace.

## Windows REDACTED_INTERNAL_DOMAIN_003

The Windows platform previously mixed architecture, policy inventories, reports, runbooks, evidence ZIP files, implementation scripts, logs, domain-join material, and temporary agent files at one level.

The resulting layout is:

- `Documentation/Architecture/` — AD and lab architecture references
- `Documentation/Change Records/` — hardening and workstation policy changes
- `Documentation/Runbooks/` — Windows Admin Center and WinRM procedures
- `Documentation/Reference/` — supporting policy reference material
- `Configuration/Group Policy/` — current Group Policy inventory
- `Scripts/PowerShell/` and `Scripts/Command/` — implementation automation
- `Evidence/Archives/` and `Evidence/Logs/` — retained evidence packages and logs
- `Artifacts/` — domain-join material and retained agent state

The former `.codex-tmp`, `REDACTED_NAME_002`, and `.codex-tmp/ssh` directories were removed only after they were verified empty following the artifact moves.

## Agent Guidance

`AGENTS.md` now includes:

- A decision sequence for completely new work.
- A category routing table with concrete examples.
- A file-placement table covering documentation, source, configuration, scripts, tests, evidence, and artifacts.
- A minimum workflow for introducing a new deployed platform.
- An explicit example routing NetBird to `Platforms/Netbird/` while linking its infrastructure dependencies.

The human-readable Governance documentation standard was updated with the same ownership and artifact-placement model.

## Verification

- TNIO before reorganization: 95 files totaling 3,609,355 bytes.
- Windows Servers before reorganization: 36 files totaling 1,120,642 bytes.
- Original content was moved rather than recreated or deleted.
- Three navigation and context documents were added to TNIO, producing 98 files in that platform.
- Three navigation and context documents were added to Windows Servers, producing 39 files in that platform.
- No stale references to the former local TNIO or Windows temporary paths remain in the inspected source and records.
- All workspace-local Markdown links resolve.
- No remote machine, Group Policy, deployed TNIO service, or UniFi configuration was changed.

## Development Impact

The local directory paths changed substantially. Tools or commands that assumed files were directly beneath the TNIO or `Windows REDACTED_INTERNAL_DOMAIN_003` roots must use the new paths. Source contents were not rewritten, and executable validation was not claimed as part of this documentation-only migration. TNIO tests that assumed execution from `/home/REDACTED_DEPLOYMENT_USER/lore-rag` may require the deployed module path or an adjusted Python import path when run locally.

