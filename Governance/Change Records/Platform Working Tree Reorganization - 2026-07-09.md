# Platform Working Tree Reorganization

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

**Date:** 2026-07-09  
**Status:** Complete  
**Scope:** TNIO AI Bot and `<YOUR_WINDOWS_DOMAIN>` Windows platform working trees

## Scope

I separated the mixed TNIO and Windows working trees into documentation, source, configuration, scripts, tests, evidence, & artifacts. The local paths changed; I didn't preserve compatibility with the former layout.

## TNIO AI Bot

The TNIO platform root held source, duplicate implementations, scratch work, tests, documentation, audits, caches, logs, worktrees, service configuration, & a deployment bundle.

I reorganized it into:

- `Source/lore-rag/`: primary source snapshot
- `Source/lore-rag-remote/`: remote source snapshot
- `Source/Experimental/lore-rag/`: experimental implementation
- `Source/Legacy/`: former root-level implementations
- `Tests/`: legacy evaluation and remote accuracy tests
- `Documentation/`: product, reference, and dated change records
- `Configuration/`: systemd and remote-state configuration snapshots
- `Evidence/`: corpus audits, remote snapshots, and logs
- `Artifacts/`: deployment bundles, caches, and retained worktrees and state

I preserved references to the deployed path `/home/<YOUR_DEPLOYMENT_USER>/lore-rag` because they describe the Linux runtime rather than the local Windows workspace.

## Windows `<YOUR_WINDOWS_DOMAIN>`

The Windows platform kept architecture, policy inventories, reports, runbooks, evidence ZIP files, scripts, logs, domain-join material, & scratch files at one level.

I reorganized it into:

- `Documentation/Architecture/`: AD and lab architecture references
- `Documentation/Change Records/`: hardening and workstation policy changes
- `Documentation/Runbooks/`: Windows Admin Center and WinRM procedures
- `Documentation/Reference/`: supporting policy reference material
- `Configuration/Group Policy/`: current Group Policy inventory
- `Scripts/PowerShell/` and `Scripts/Command/`: implementation automation
- `Evidence/Archives/` and `Evidence/Logs/`: retained evidence packages and logs
- `Artifacts/`: domain-join material and retained working state

I removed the leftover temporary directories, including `<YOUR_TEMP_DIRECTORY>`, only after verifying each was empty following the artifact moves.

## Placement Rules Recorded

I recorded the placement model in the Governance documentation standard:

- A decision sequence for completely new work.
- A category routing table with concrete examples.
- A file-placement table covering documentation, source, configuration, scripts, tests, evidence, and artifacts.
- A minimum workflow for introducing a new deployed platform.
- A worked example routing NetBird to `Platforms/Netbird/` while linking its infrastructure dependencies.

## Verification

- TNIO before reorganization: 95 files totaling 3,609,355 bytes.
- Windows Servers before reorganization: 36 files totaling 1,120,642 bytes.
- I moved original content rather than recreating or deleting it.
- I added three navigation and context documents to TNIO, bringing that platform to 98 files.
- I added three navigation and context documents to Windows Servers, bringing that platform to 39 files.
- No stale references to the former local TNIO or Windows temporary paths remain in the source and records I inspected.
- All workspace-local Markdown links resolve.
- I changed no remote machine, Group Policy, deployed TNIO service, or UniFi configuration.

## Development Impact

The local paths changed. Tools that assumed files sat directly beneath the TNIO or `Windows <YOUR_WINDOWS_DOMAIN>` roots must use the new directories. I moved files without rewriting source or running code validation. TNIO tests written for `/home/<YOUR_DEPLOYMENT_USER>/lore-rag` still need that module path, or an adjusted Python import path, when run from Windows.
