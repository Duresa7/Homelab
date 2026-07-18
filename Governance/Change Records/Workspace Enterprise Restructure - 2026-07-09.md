# Workspace Enterprise Restructure

**Created:** 2026-07-09  
**Last updated:** 2026-07-09

**Date:** 2026-07-09  
**Status:** Complete  
**Scope:** Local `Homelab` workspace structure and documentation links

## Objective

Reorganize the homelab into an enterprise-style workspace that supports both operational documentation and active development while keeping records routed by ownership and evidence close to the system or incident it supports.

## Decisions

- Use generic enterprise categories: Governance, Architecture, Infrastructure, Platforms, Engineering, Operations, Security, and Archive.
- Keep deployed service documentation and source together under `Platforms/<Service>/`.
- Scale documentation depth using three tiers rather than forcing every service into the same structure.
- Route configuration according to the system that owns or enforces it.
- Store service-specific and incident-specific evidence beside its owner rather than in a global image folder.
- Preserve active application source layouts when an internal move could disrupt imports, tooling, or deployment paths.

## Primary Migration

| Previous location | New location |
|---|---|
| `Network/` | `Infrastructure/Network/` |
| `Galaxy Server Cluster/` | `Infrastructure/Compute/Galaxy/` |
| `Hardware/` | `Infrastructure/Hardware/` |
| `Incident Reports/` | `Security/Incidents/` |
| `smart-test-results/` | `Operations/Diagnostics/SMART/` |
| Root virtualization inventories | `Operations/Inventory/Galaxy/` |
| Service folders under `Virtualized Configurations/` | `Platforms/<Service>/` |
| `automation/` | `Engineering/Automation/` |

## Internal Organization

- Galaxy architecture, change records, Proxmox firewall configuration, network configuration, Corosync, storage, and evidence received distinct ownership-based areas.
- UniFi VLANs, zones, firewall policies, objects, VPN/port-profile records, plans, and evidence were separated under the UniFi infrastructure owner.
- Cloudflare DNS records moved under Cloudflare configuration.
- Existing Splunk screenshots moved into service-local evidence folders with evidence indexes.
- Low-risk service documentation was moved into `Documentation/` for Ansible, Immich, Portainer, Splunk, and TeamSpeak.
- TeamSpeak migration scripts moved into the platform's `Scripts/` area.
- Active TNIO AI Bot and Windows Server working trees were preserved internally to avoid disrupting development or deployment behavior.

## Navigation and Standards Added

- Root workspace index and category purpose documents.
- Human-readable documentation standard under Governance.
- Updated `AGENTS.md` routing, tiering, ownership, inventory, incident, and evidence instructions.
- Galaxy, UniFi, and Cloudflare indexes.

## Verification

- Before relocation: 183 files totaling 6,525,142 bytes.
- After all relocation operations and before adding indexes: 183 files totaling 6,525,142 bytes.
- No original files were lost during relocation.
- Three legacy directories were removed only after each was verified empty: `Virtualized Configurations/`, root `Images/`, and the empty Splunk Enterprise `docs/` folder.
- Twenty navigation, standards, evidence-index, and structure documents were then added, producing 203 files totaling 6,535,360 bytes before this change record was added.
- Markdown references affected by the move were updated, including Galaxy inventory, Galaxy change records, and Splunk cross-product links.
- No remote machine, UniFi controller, or deployed service configuration was changed.

## Rollback

Rollback consists of reversing the primary migration table, returning internally organized records to their previous parent folders, and reverting the associated Markdown links. Because application source trees moved intact and no original files were deleted, rollback is a path operation rather than a content reconstruction.

## Follow-Up Opportunities

- TNIO and Windows working-tree separation was completed in [Platform Working Tree Reorganization - 2026-07-09.md](Platform%20Working%20Tree%20Reorganization%20-%202026-07-09.md).
- Add per-image context to the existing Splunk screenshot evidence.
- Generate a new dated Galaxy inventory set after the next material VM, LXC, or workload change.
- Add Architecture records when an environment-wide topology or dependency map is created.
