# Living Document Naming and TODO Standard

**Created:** 2026-07-09  
**Last updated:** 2026-07-19

**Date:** 2026-07-09  
**Status:** Complete

## Objective

Create a central homelab backlog, distinguish living-document filenames from historical-record filenames, and require visible update metadata inside Markdown documents.

## Central Backlog

I created [TODO.md](../../TODO.md) at the workspace root as the intake list, high-level priority list, and index of the per-owner project backlogs. Detailed technical checklists stay with the infrastructure component or platform that owns the work.

## Filename Audit

My first pass renamed two clearly living Galaxy documents. I then reviewed all 22 dated filenames still present.

Seventeen event or point-in-time records kept their dates. I renamed five more living inventories so I can maintain them in place.

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
- Historical and point-in-time records keep dates in their filenames.
- Every Markdown document shows both `**Created:** YYYY-MM-DD` and `**Last updated:** YYYY-MM-DD` near the top of the file itself.
- `Created` stays fixed. Original incident, implementation, migration, and snapshot dates stay separate from `Last updated`.
- Read-only inspection does not change the update date; content, instruction, fact, link, or filename changes do.

## Verification

- I updated the references to all seven renamed living documents.
- The root README links the central TODO.
- The Governance documentation standard and the working notes I keep outside the repository carry the filename, update-metadata, and backlog rules.
- I normalized every Markdown document with in-file `Created` and `Last updated` metadata.
- The remaining dated Markdown filenames are historical or point-in-time records.
