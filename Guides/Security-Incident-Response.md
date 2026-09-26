# Security Incident Response Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-09-25

## What This Guide Covers

I use this sequence for a service-impacting or security incident. It has six steps, below. The last one closes the incident only after the old path fails.

## Current Status and Verified Versions

`Security/Incidents/` holds thirteen reports across eleven service folders, counted on 2026-09-25. Retired-platform incidents stay under `Archive/Security/Incidents/`.

| Date | Folder | Report |
|---|---|---|
| 2026-04-19 | Vercel | [Credential Rotation After Vendor Bulletin](../Security/Incidents/Vercel/Credential%20Rotation%20After%20Vendor%20Bulletin%20-%202026-04-19.md) |
| 2026-04-24 | Teamspeak | [DNS and ServerQuery](../Security/Incidents/Teamspeak/DNS%20and%20ServerQuery%20-%202026-04-24.md) |
| 2026-04-24 | Teamspeak | [UDP Relay Outage](../Security/Incidents/Teamspeak/UDP%20Relay%20Outage%20-%202026-04-24.md) |
| 2026-07-20 | Galaxy | [HA Local Storage Stranding](../Security/Incidents/Galaxy/HA%20Local%20Storage%20Stranding%20-%202026-07-20.md) |
| 2026-07-22 | Grafana | [Plaintext Administrator Credential](../Security/Incidents/Grafana/Plaintext%20Administrator%20Credential%20-%202026-07-22.md) |
| 2026-07-22 | qBittorrent | [Arr Client Outage](../Security/Incidents/qBittorrent/Arr%20Client%20Outage%20-%202026-07-22.md) |
| 2026-07-25 | Preview Server | [LAN-Exposed Repository Root](../Security/Incidents/Preview%20Server/LAN-Exposed%20Repository%20Root%20-%202026-07-25.md) |
| 2026-07-30 | Galaxy | [Blue Server Duplicate VG](../Security/Incidents/Galaxy/Blue%20Server%20Duplicate%20VG%20-%202026-07-30.md) |
| 2026-08-29 | Splunk | [Administrator Credential Printed to an Agent Session](../Security/Incidents/Splunk/Administrator%20Credential%20Printed%20to%20an%20Agent%20Session%20-%202026-08-29.md) |
| 2026-09-11 | Wazuh | [Manager Processes Terminated by Hash Refresh](../Security/Incidents/Wazuh/Manager%20Processes%20Terminated%20by%20Hash%20Refresh%20-%202026-09-11.md) |
| 2026-09-12 | UniFi | [Action1 Remote Service Control Alert](../Security/Incidents/UniFi/Action1%20Remote%20Service%20Control%20Alert%20-%202026-09-12.md) |
| 2026-09-18 | Active Directory | [ObiPC Wiped from the Recovery Menu](../Security/Incidents/Active%20Directory/ObiPC%20Wiped%20from%20the%20Recovery%20Menu%20-%202026-09-18.md) |
| 2026-09-25 | Nginx Proxy Manager | [Scheduled Update Stranded the Proxy](../Security/Incidents/Nginx%20Proxy%20Manager/Scheduled%20Update%20Stranded%20the%20Proxy%20-%202026-09-25.md) |

## What You Need

- The first observed time, affected service, user-visible symptom, and reporter.
- Current provider dashboards, service logs, DNS, firewall, and authentication records.
- A list of every system that can reach or trust the affected component.
- A copy of each configuration file I plan to edit, taken before the edit. I keep no snapshots or backups, so a rebuild from the baseline is the fallback beyond that.

## How the Pieces Fit Together

![Security incident response phases: scope, preserve, contain, correct, verify, close](../Assets/Diagrams/incident-response.svg)

## Walkthrough

### Step 1: Define Scope and Impact

Write the affected assets, start time, symptom, and known user impact before changing state. Separate confirmed facts from working hypotheses.

### Step 2: Preserve the Timeline

Record provider events, service logs, DNS changes, firewall changes, authentication events, and my own actions in timestamp order. Keep the original time zone beside the timeline.

### Step 3: Contain the Active Path

Disable the exposed integration, route, account, tunnel, or key that creates current risk. Pick the narrowest action that stops the path without erasing the data needed for the root-cause check.

### Step 4: Correct the Configuration

Rotate affected access, remove legacy entries, repair the tunnel or DNS target, and update each dependent service. One successful save isn't enough; the old value or route must fail after the new one works.

### Step 5: Verify Service and Security State

Repeat the user path, backend path, authentication check, DNS lookup, and provider status that define recovery. For the TeamSpeak relay outage, this meant the SRV chain, Playit tunnel, UDP voice path, local container, and TS3 Manager view.

### Step 6: Record Residual Risk and Close

List each follow-up with the condition that closes it. Close the incident only when the service is stable, the exposed path is disabled, the verification results are recorded, and any residual risk has a bounded next action.

## What the Report Contains

Step 6 produces the report. I keep it under `Security/Incidents/`, separate from the affected service's own records, so an incident stays findable whether I go looking by service or by date. Each report carries:

- Metadata: the date, the affected service, and the closure status.
- A summary a reader can take in without the detail below it.
- Impact, in terms of what stopped working and for whom.
- Affected assets: the hosts, guests, networks, and accounts in scope.
- Symptoms, including the exact error text where I captured it.
- A timeline, where I have the timestamps to build one.
- Findings, then the root cause, or the current hypothesis when I never proved one.
- Corrective action, and the validation that shows it worked.
- Residual risk and follow-ups, with the closure status saying whether this is finished.

Routine troubleshooting isn't an incident. Those records live with the platform that owns them. When a problem turns into an incident, I write the report and cross-link both records so neither is a dead end.

## What I Checked After Each Step

- Corrective actions had an observed result, not just a successful command submission.
- Old access failed where rotation was part of containment.
- User-facing traffic and backend health both passed.
- Incident reports link the platform records that own the final configuration.

## Troubleshooting and Recovery

If a containment change increases impact, restore the last known-good service route while keeping the exposed identity disabled. Split availability recovery from the security correction when one rollback can't safely restore both.

## Known Limits

This guide doesn't replace provider-specific incident procedures. A disclosure involving billing, legal notice, or third-party user data needs the applicable external response path in addition to the technical record.

## Source Records

- [Application-stack incident response](../Security/Incidents/Vercel/Credential%20Rotation%20After%20Vendor%20Bulletin%20-%202026-04-19.md)
- [TeamSpeak service incident](../Security/Incidents/Teamspeak/DNS%20and%20ServerQuery%20-%202026-04-24.md)
- [TeamSpeak UDP relay outage](../Security/Incidents/Teamspeak/UDP%20Relay%20Outage%20-%202026-04-24.md)
- [Security records index](../Security/README.md)
