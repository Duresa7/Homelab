# Security

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

My incident reports and security assessments for the AlphaSec United homelab. Each incident lives under `Incidents/<Service>/` even when the service keeps its records under `Platforms/` or `Infrastructure/`.

| Item | Count, 2026-09-25 |
| --- | --- |
| Incident reports | 13 across 11 service folders |
| Assessments | 3 |
| Archived incidents | 1 ([Kasm Workspaces](../Archive/Security/Incidents/Kasm%20Workspaces/Thin%20Pool%20Exhaustion%20-%202026-07-29.md)) |

## Incidents

| Date | Service | Report | Severity | Status |
| --- | --- | --- | --- | --- |
| 2026-09-25 | Nginx Proxy Manager | [Scheduled update stranded the proxy](Incidents/Nginx%20Proxy%20Manager/Scheduled%20Update%20Stranded%20the%20Proxy%20-%202026-09-25.md): a Dockhand auto-update stopped NPM and cut its own Hawser path, leaving NPM down about 3 hours | SEV-2 | Resolved |
| 2026-09-18 | Active Directory | [ObiPC wiped from the recovery menu](Incidents/Active%20Directory/ObiPC%20Wiped%20from%20the%20Recovery%20Menu%20-%202026-09-18.md): a standard user reset the domain workstation through WinRE | SEV-4 | Closed |
| 2026-09-12 | UniFi | [Action1 remote service control alert](Incidents/UniFi/Action1%20Remote%20Service%20Control%20Alert%20-%202026-09-12.md): IPS blocked authorized Action1 Deployer RPC from HQ-MGT01 to ObiPC | Not assigned | Closed |
| 2026-09-11 | Wazuh | [Manager processes terminated by hash refresh](Incidents/Wazuh/Manager%20Processes%20Terminated%20by%20Hash%20Refresh%20-%202026-09-11.md): the weekly refresh killed the manager for five days while systemd reported active | Not assigned | Closed |
| 2026-08-29 | Splunk | [Administrator credential printed to an agent session](Incidents/Splunk/Administrator%20Credential%20Printed%20to%20an%20Agent%20Session%20-%202026-08-29.md): a netrc read printed the Splunk admin password into my MCP client's context | SEV-5 | Closed |
| 2026-07-30 | Galaxy | [Blue-server duplicate VG](Incidents/Galaxy/Blue%20Server%20Duplicate%20VG%20-%202026-07-30.md): a second `pve` volume group left `local-lvm` inactive and three LXCs down | SEV-2 | Resolved |
| 2026-07-25 | Preview Server | [LAN-exposed repository root](Incidents/Preview%20Server/LAN-Exposed%20Repository%20Root%20-%202026-07-25.md): the local preview server answered the LAN and served the whole working tree | SEV-3 | Closed |
| 2026-07-22 | Grafana | [Plaintext administrator credential](Incidents/Grafana/Plaintext%20Administrator%20Credential%20-%202026-07-22.md): the Grafana admin credential sat in Compose and the container environment | SEV-4 | Closed |
| 2026-07-22 | qBittorrent | [Arr client outage](Incidents/qBittorrent/Arr%20Client%20Outage%20-%202026-07-22.md): Host-header validation blocked Sonarr and Radarr after the HTTPS hostname change | SEV-3 | Closed |
| 2026-07-20 | Galaxy | [HA local-storage stranding](Incidents/Galaxy/HA%20Local%20Storage%20Stranding%20-%202026-07-20.md): HA moved CT 107 and CT 108 configs off blue without their node-local disks | SEV-2 | Resolved |
| 2026-04-24 | TeamSpeak | [UDP relay outage](Incidents/Teamspeak/UDP%20Relay%20Outage%20-%202026-04-24.md): Docker's UDP proxy broke the TeamSpeak handshake through Playit | SEV-2 | Mitigated |
| 2026-04-24 | TeamSpeak | [DNS and ServerQuery](Incidents/Teamspeak/DNS%20and%20ServerQuery%20-%202026-04-24.md): an SRV record targeted a CNAME and TS3 Manager tripped flood protection | SEV-3 | Resolved / Monitoring |
| 2026-04-19 | Vercel | [Credential rotation after vendor bulletin](Incidents/Vercel/Credential%20Rotation%20After%20Vendor%20Bulletin%20-%202026-04-19.md): precautionary Supabase and GitHub rotation after Vercel's April 2026 bulletin | Not assigned | Complete, F-1 open |

## Assessments

| Date | Assessment | Result |
| --- | --- | --- |
| 2026-09-24 | [ObiPC sign-in review](Assessments/ObiPC%20Sign-In%20Review%20-%202026-09-24.md) | ObiPC unreachable over SSH; domain controllers logged only its computer account |
| 2026-09-23 | [ObiPC event review](Assessments/ObiPC%20Event%20Review%20-%202026-09-23.md) | Read-only review of ObiPC's Windows event logs for 2026-09-23 |
| 2026-07-27 | [UniFi firewall audit](Assessments/UniFi%20Firewall%20Audit%20-%202026-07-27.md) | 62/100, `needs_attention` |

## Hardening

The Linux Host Baseline Standard in `Hardening/` is not published: it describes the privilege model on each host. The public walkthrough is the [Linux Host Baseline](../Guides/Linux-Host-Baseline.md) guide.

## Evidence

Evidence sits beside the record it supports: `Incidents/<Service>/Evidence/<Job - YYYY-MM-DD>/` and `Assessments/Evidence/<Job - YYYY-MM-DD>/`, each with `Logs/`, `Screenshots/` or `Exports/` and an `Evidence-Index.md` where the job has one. Most evidence stays on local disk; only allow-listed files are published.
