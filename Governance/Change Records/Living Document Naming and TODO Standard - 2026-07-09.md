# Living Document Naming and TODO Standard

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

**Date:** 2026-07-09  
**Status:** Complete

## Scope

I created one root backlog, separated living filenames from dated historical records, & added visible creation and update dates to every Markdown file.

## Central Backlog

I created [TODO.md](../../TODO.md) as the intake list, priority list, & index of the owner-specific backlogs. Detailed checklists stay with the infrastructure component or platform that owns the work.

## Filename Audit

My first pass renamed two living Galaxy documents. I then checked the 22 dated filenames that remained.

Seventeen event or point-in-time records kept their dates. Five living inventories lost their filename dates so I can update them in place.

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
- The Governance documentation standard carries the filename, update-metadata, & backlog rules.
- I normalized every Markdown document with in-file `Created` and `Last updated` metadata.
- The remaining dated Markdown filenames are historical or point-in-time records.
