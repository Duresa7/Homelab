# Living Document Naming and TODO Standard

**Created:** 2026-07-09  
**Last updated:** 2026-07-09

**Date:** 2026-07-09  
**Status:** Complete

## Objective

Create a central homelab backlog, distinguish living-document filenames from historical-record filenames, and require visible update metadata inside Markdown documents.

## Central Backlog

Created [TODO.md](../../TODO.md) at the workspace root. It serves as the intake list, high-level priority list, and index of owner-specific project backlogs. Detailed technical checklists remain with the infrastructure component or platform that owns the work.

## Filename Audit

The first pass renamed two clearly living Galaxy documents. A subsequent explicit audit reviewed all 22 dated filenames still present and is recorded in [Dated Markdown Filename Audit - 2026-07-09.md](../Audits/Dated%20Markdown%20Filename%20Audit%20-%202026-07-09.md).

Seventeen event or point-in-time records retain their dates. Five additional living inventories were renamed so they can be maintained in place.

Living documents renamed across both passes:

| Previous filename | Current filename |
|---|---|
| `Galaxy Cluster Setup Document - 2026-05-30.md` | `Galaxy Cluster Setup Document.md` |
| `Galaxy Data Center Firewall - 2026-05-30.md` | `Galaxy Data Center Firewall.md` |
| `Nodes - 2026-07-08.md` | `Nodes.md` |
| `Galaxy virtualized config - 2026-07-08.md` | `Galaxy Inventory.md` |
| `LXCs - 2026-07-08.md` | `LXCs.md` |
| `Services - 2026-07-08.md` | `Services.md` |
| `VMs - 2026-07-08.md` | `VMs.md` |

Original creation, historical, and verification dates remain inside those documents.

## Standard Adopted

- Living documents use stable filenames without dates.
- Historical and point-in-time records retain dates in their filenames.
- Every Markdown document must show both `**Created:** YYYY-MM-DD` and `**Last updated:** YYYY-MM-DD` near the top of the file itself.
- `Created` remains fixed. Original incident, implementation, migration, and snapshot dates remain separate from `Last updated`.
- Read-only inspection does not change the update date; content, instruction, fact, link, or filename changes do.

## Verification

- References to all seven renamed living documents were updated.
- The root README now links the central TODO.
- `AGENTS.md` and the Governance documentation standard contain the filename, update-metadata, and backlog-management rules.
- All Markdown documents were normalized with in-file `Created` and `Last updated` metadata.
- The remaining dated Markdown filenames are historical or point-in-time records.
