# Cloud Apps and Usage Telemetry Disabled

**Created:** 2026-11-12  
**Last updated:** 2026-11-12  
**Implementation and verification:** 2026-11-12

I disabled the four apps on `splunk-siem` that only do anything with a Splunk cloud service, and turned off the two optional usage-telemetry feeds. None of the four had ever been set up. Splunk restarted once, at 7:16 AM, and came back with every input listening and the Wazuh forwarder reconnected.

## What was there

Read before the change, from each app's merged `app.conf` and its `local/` directory:

| App | Label | State before | Local configuration |
|---|---|---|---|
| `Splunk_AI_Assistant_Cloud` | Splunk AI Assistant | enabled | `is_configured = 0` and an empty `[cloud_connected_configurations]` stanza, so it was never connected. It still ran `saia_async_jobs.py` as a modular input and held a generated key pair in `passwords.conf` |
| `splunk_cloud_connect` | Splunk Cloud Connect | enabled, hidden | none. Only `Splunk_AI_Assistant_Cloud` references it, from its `restmap.conf` |
| `splunk_app_for_splunk_o11y_cloud` | Discover Splunk Observability Cloud | enabled | none |
| `splunk_secure_gateway` | Splunk Secure Gateway | enabled | none, so no mobile device was ever registered |

`dlx-app` (Detection Studio) also runs background Python, but its manifest depends only on `SplunkEnterpriseSecuritySuite` 8.3.0 or later. It is part of Enterprise Security, so I left it alone, along with `missioncontrol` and `exposure-analytics`. `splunk-ai-canvas` was already disabled.

Telemetry, from `btool telemetry list general`: `sendAnonymizedUsage`, `sendAnonymizedWebAnalytics` and `sendLicenseUsage` were `true`, `sendSupportUsage` was `false`.

Wazuh has no equivalent to turn off. `/var/ossec/etc/ossec.conf` on `security-01` carries no `aws-s3`, `azure-logs`, `gcp-pubsub`, `gcp-bucket`, `office365`, `github` or `ms-graph` module. Its only outbound calls are `<update_check>` and the vulnerability-detection feed download, and the feed is what the Vulnerabilities view runs on.

## Change

As root on `splunk-siem`, I added `[install] state = disabled` to each app's `local/app.conf`. For `Splunk_AI_Assistant_Cloud` the line went under the existing `[install]` stanza; the other three got a new file, owned `splunk:splunk`, mode 600. Each app's `default/` stays untouched, so re-enabling one means removing that line and restarting.

In `splunk_instrumentation/local/telemetry.conf` I set `sendAnonymizedUsage = false` and `sendAnonymizedWebAnalytics = false` under `[general]`. I left `sendLicenseUsage` on, because license usage reporting can be a license condition and turning it off is not worth that risk on the donation license.

`systemctl restart Splunkd` ran detached at 7:16:21 AM. Shutdown took about 40 seconds and `splunkd started (build f798d4d49089)` was logged at 7:17:05 AM.

## Verification

| Check | Time | Result |
|---|---|---|
| `systemctl is-active Splunkd unifi-flow-collector` | 7:17 AM | both `active`; `ActiveEnterTimestamp` 7:17:03 AM |
| Listeners | 7:17 AM | 1514, 8000, 8088, 8089, 8191 and 9997 all listening |
| Splunk Web, `https://127.0.0.1:8000/en-US/account/login` | 7:17 AM | HTTP 200 |
| HEC health, `https://127.0.0.1:8088/services/collector/health` | 7:17 AM | `HEC is healthy` |
| App state, `btool app list --app=<app>` | 7:17 AM | `state = disabled` on all four |
| Processes | 7:17 AM | no process from any of the four apps; `saia_async_jobs.py` gone |
| Telemetry, `btool telemetry list general` | 7:17 AM | `sendAnonymizedUsage = false`, `sendAnonymizedWebAnalytics = false`, `sendLicenseUsage = true`, `sendSupportUsage = false` |
| Wazuh forwarder | 7:17 AM | established connection from `192.168.72.2` on 9997 |
| Ingestion, `per_index_thruput` in `metrics.log` | 7:17:59 AM | first interval after the restart: `netfw` 63 events, `netops` 1, `wazuh` 9 |

## Open items

Things this review found that I left for their own changes, listed in the [Enterprise TODO](../TODO.md#housekeeping):

- `_audit` keeps 188,697,600 seconds (six years) with a 500,000 MB cap. It held 11 GB on 2026-11-12, growing about 2.4 GB a month since 2026-06-29, and is the largest index on the host.
- `_introspection` (14 days, 9.9 GB) and `_internal` (30 days, 8.8 GB) delete by age but have no size cap below 500,000 MB on a 92 GB disk.
- 22 data models are accelerated, and nine of them have nothing feeding them: Certificates, Domain_Analysis, Email, Network_Resolution, Performance, Ticket_Management, Updates, Vulnerabilities and Web. That comes from the CIM tags in `unifi_insights` and `wazuh_insights`; I have not yet confirmed each is empty with `tstats`.
- 218 scheduled searches are enabled, most of them Enterprise Security content for data I do not collect.
