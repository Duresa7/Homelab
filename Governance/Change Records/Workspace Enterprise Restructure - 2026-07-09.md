# Workspace Enterprise Restructure

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

**Date:** 2026-07-09  
**Status:** Complete  
**Scope:** Local `Homelab` workspace structure and documentation links

## Scope

I reorganized the repository into eight owner-based root categories for operational records & active development. Evidence moved beside the system, change, or incident that produced it.

## Decisions

- I used eight root categories: Governance, Architecture, Infrastructure, Platforms, Engineering, Operations, Security, & Archive.
- I kept deployed service documentation and source together under `Platforms/<Service>/`.
- I scaled documentation depth with three tiers rather than forcing every service into the same structure.
- I routed configuration to the system that owns or enforces it.
- I stored service-specific and incident-specific evidence beside its owner rather than in a global image folder.
- I preserved active application source layouts where an internal move could disrupt imports, tooling, or deployment paths.

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

- I gave Galaxy architecture, change records, Proxmox firewall configuration, network configuration, Corosync, storage, and evidence distinct ownership-based areas.
- I separated the UniFi VLANs, zones, firewall policies, objects, VPN and port-profile records, plans, and evidence under the UniFi infrastructure owner.
- Cloudflare DNS records moved under Cloudflare configuration.
- I moved the existing Splunk screenshots into service-local evidence folders with evidence indexes.
- Low-risk service documentation moved into `Documentation/` for Ansible, Immich, Portainer, Splunk, and TeamSpeak.
- TeamSpeak migration scripts moved into the platform's `Scripts/` area.
- I kept the active TNIO AI Bot and Windows Server working trees intact internally to avoid disrupting development or deployment behavior.

## Navigation and Documentation Rules

- Root workspace index and category purpose documents.
- Human-readable documentation standard under Governance.
- Routing, tiering, ownership, inventory, incident, & evidence rules in the Governance standard.
- Galaxy, UniFi, and Cloudflare indexes.

## Verification

- Before relocation: 183 files totaling 6,525,142 bytes.
- After all relocation operations and before adding indexes: 183 files totaling 6,525,142 bytes.
- No original files were lost during relocation.
- I removed three legacy directories only after verifying each was empty: `Virtualized Configurations/`, the root `Images/`, and the empty Splunk Enterprise `docs/` folder.
- I then added twenty navigation, standards, evidence-index, and structure documents, producing 203 files totaling 6,535,360 bytes before this change record was added.
- I updated the Markdown references affected by the move, including Galaxy inventory, Galaxy change records, and Splunk cross-product links.
- I changed no remote machine, UniFi controller, or deployed service configuration.

## Rollback

To roll back, I would reverse the migration table, return each record to its prior parent, & restore the old Markdown links. Application source trees moved intact and no original file was deleted, so rollback requires path changes rather than content reconstruction.

## Follow-Ups

- I completed the TNIO and Windows working-tree separation in [Platform Working Tree Reorganization - 2026-07-09.md](Platform%20Working%20Tree%20Reorganization%20-%202026-07-09.md).
- Add per-image context to the existing Splunk screenshot evidence.
- Generate a new dated Galaxy inventory set after the next material VM, LXC, or workload change.
- Add Architecture records when an environment-wide topology or dependency map is created.
