# Dated Markdown Filename Audit

**Created:** 2026-07-09  
**Last updated:** 2026-07-15

## Decision Rule

Keep the date when it identifies an event, bounded body of work, audit, migration, incident, evidence report, or immutable snapshot. Remove the date when the file is a living source of truth that should be updated in place.

## Current Dated-Filename Audit

| File | Decision | Reason |
|---|---|---|
| `Governance/Change Records/Living Document Naming and TODO Standard - 2026-07-09.md` | Keep | Bounded governance change record |
| `Governance/Change Records/Platform Working Tree Reorganization - 2026-07-09.md` | Keep | Bounded workspace change record |
| `Governance/Change Records/Workspace Enterprise Restructure - 2026-07-09.md` | Keep | Bounded workspace change record |
| `Infrastructure/Compute/Galaxy/Documentation/Change Records/Galaxy Cluster Red Server Expansion - 2026-07-07.md` | Keep | Historical node-expansion event |
| `Infrastructure/Compute/Galaxy/Documentation/Change Records/Galaxy-Cluster-Expansion-Node-Preparation-2026-05-27.md` | Keep | Historical preparation project |
| `Infrastructure/Hardware/Nodes - 2026-07-08.md` | Remove | Living current node and storage inventory |
| `Operations/Inventory/Galaxy/Galaxy virtualized config - 2026-07-08.md` | Remove | Living index of the current Galaxy inventory |
| `Operations/Inventory/Galaxy/LXCs - 2026-07-08.md` | Remove | Living current LXC inventory |
| `Operations/Inventory/Galaxy/Services - 2026-07-08.md` | Remove | Living current workload inventory |
| `Operations/Inventory/Galaxy/VMs - 2026-07-08.md` | Remove | Living current VM inventory |
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

## Result

Seventeen current filenames retain their dates. Five living inventory filenames should become stable and undated. The two Galaxy living documents renamed during the earlier pass—`Galaxy Cluster Setup Document.md` and `Galaxy Data Center Firewall.md`—remain correctly undated.

