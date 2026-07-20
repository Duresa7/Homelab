# Platform Working Tree Reorganization

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

**Date:** 2026-07-09  
**Status:** Complete  
**Scope:** TNIO AI Bot and `<YOUR_WINDOWS_DOMAIN>` Windows platform working trees

## Objective

Finish the enterprise workspace migration by separating the previously mixed TNIO and Windows working trees into documentation, source, configuration, scripts, tests, evidence, and retained artifacts. I chose not to preserve path compatibility with the former local working-tree layout.

## TNIO AI Bot

The TNIO platform previously held source, duplicate implementations, scratch work, tests, documentation, audits, caches, logs, worktrees, service configuration, and a deployment bundle all at the platform root.

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

The Windows platform previously mixed architecture, policy inventories, reports, runbooks, evidence ZIP files, implementation scripts, logs, domain-join material, and temporary scratch files at one level.

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

I recorded the placement model in the Governance documentation standard and in the working notes I keep outside the repository:

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

The local directory paths changed. Tools or commands that assumed files sat directly beneath the TNIO or `Windows <YOUR_WINDOWS_DOMAIN>` roots must use the new paths. This was a file-move migration only: I did not rewrite source contents, and I did not validate the code by running it. TNIO tests that assumed execution from `/home/<YOUR_DEPLOYMENT_USER>/lore-rag` may need the deployed module path or an adjusted Python import path when run locally.
