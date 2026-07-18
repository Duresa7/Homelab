# Dated Markdown Filename Audit

**Created:** 2026-07-09  
**Last updated:** 2026-07-18

## Decision Rule

I keep the date when it identifies an event, bounded body of work, audit, migration, incident, evidence report, or immutable snapshot. I remove it when the file is a living source of truth that I update in place.

## Dated Filenames Reviewed

| File | Decision | Reason |
|---|---|---|
| `Governance/Change Records/Living Document Naming and TODO Standard - 2026-07-09.md` | Keep | Bounded governance change record |
| `Governance/Change Records/Platform Working Tree Reorganization - 2026-07-09.md` | Keep | Bounded workspace change record |
| `Governance/Change Records/Workspace Enterprise Restructure - 2026-07-09.md` | Keep | Bounded workspace change record |
| `Infrastructure/Compute/Galaxy/Documentation/Change Records/Galaxy Cluster Red Server Expansion - 2026-07-07.md` | Keep | Historical node-expansion event |
| `Infrastructure/Compute/Galaxy/Documentation/Change Records/Galaxy-Cluster-Expansion-Node-Preparation-2026-05-27.md` | Keep | Historical preparation project |
| `Infrastructure/Hardware/Nodes - 2026-07-08.md` | Remove (renamed to `Nodes.md`) | Living current node and storage inventory |
| `Operations/Inventory/Galaxy/Galaxy virtualized config - 2026-07-08.md` | Remove (renamed to `Galaxy Inventory.md`) | Living index of the current Galaxy inventory |
| `Operations/Inventory/Galaxy/LXCs - 2026-07-08.md` | Remove (renamed to `LXCs.md`) | Living current LXC inventory |
| `Operations/Inventory/Galaxy/Services - 2026-07-08.md` | Remove (renamed to `Services.md`) | Living current workload inventory |
| `Operations/Inventory/Galaxy/VMs - 2026-07-08.md` | Remove (renamed to `VMs.md`) | Living current VM inventory |
| `Platforms/Immich/Documentation/Immich-Storage-Migration-WD-to-Toshiba-2026-05-28.md` | Keep | Completed migration event |
| `Platforms/Openclaw/Documentation/OpenClaw-Change-Record-2026-04-27.md` | Keep | Bounded change record |
| `Platforms/TNIO AI Bot/Documentation/Change Records/tnio-bot-accuracy-policy-report-2026-05-12.md` | Keep | Dated implementation report |
| `Platforms/TNIO AI Bot/Documentation/Change Records/tnio-bot-fixes-report-2026-05-11.md` | Keep | Dated implementation report |
| `Platforms/TNIO AI Bot/Documentation/Change Records/tnio-bot-full-accuracy-upgrade-report-2026-05-13.md` | Keep | Dated upgrade report |
| `Platforms/TNIO AI Bot/Documentation/Change Records/tnio-bot-full-corpus-audit-report-2026-05-12.md` | Keep | Dated audit and upgrade report |
| `Platforms/TNIO AI Bot/Documentation/Change Records/tnio-bot-secondary-deep-corpus-audit-report-2026-05-12.md` | Keep | Dated audit report |
| `Platforms/Windows Servers/Windows REDACTED_INTERNAL_DOMAIN_003/Documentation/Change Records/REDACTED_NAME_003-GPO-Hardening-Report-20260425-145131.md` | Keep | Timestamped implementation and evidence report |
| `Platforms/Windows Servers/Windows REDACTED_INTERNAL_DOMAIN_003/Documentation/Change Records/REDACTED_NAME_003-LAPTOP-REDACTED_NAME_002-Policy-Update-20260511.md` | Keep | Bounded policy-change report |
| `Security/Incidents/security-incident-response-2026-04-19.md` | Keep | Incident-response record |
| `Security/Incidents/TeamSpeak-Incident-Report-2026-04-24-UDP-Relay-Outage.md` | Keep | Incident record |
| `Security/Incidents/TeamSpeak-Incident-Report-2026-04-24.md` | Keep | Incident record |

## Outcome

Seventeen filenames keep their dates; each one marks an event, incident, or point-in-time record. I renamed the five living inventories to stable undated names: `Nodes.md`, `Galaxy Inventory.md`, `LXCs.md`, `Services.md`, and `VMs.md`. The two Galaxy living documents from the earlier pass, `Galaxy Cluster Setup Document.md` and `Galaxy Data Center Firewall.md`, stay undated. The renames and the reference updates that followed are recorded in [Living Document Naming and TODO Standard - 2026-07-09.md](../Change%20Records/Living%20Document%20Naming%20and%20TODO%20Standard%20-%202026-07-09.md).
