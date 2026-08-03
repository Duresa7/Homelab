# qBittorrent Arr Client Outage

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Incident Metadata

| Field | Value |
|---|---|
| Incident ID | ASU-QBIT-20260722-001 |
| Start | 2026-07-22 13:31:43 EDT |
| Detected | 2026-07-22 by user report; exact minute not retained |
| Mitigated | 2026-07-22 20:49:22 EDT |
| Validated | 2026-07-22 20:53:48 EDT |
| Duration | About 7 hours 18 minutes |
| Status | Closed |
| Severity | SEV-3 |
| Impact type | Availability of automated download-client control |
| Affected services | Sonarr, Radarr, qBittorrent Web API path through `gluetun:8080` |

## Summary

Sonarr and Radarr lost access to their only download client after the internal HTTPS change set qBittorrent's accepted WebUI domains to the NPM hostname alone. Both applications continued to reach TCP 8080, but qBittorrent rejected their `Host: gluetun:8080` requests with HTTP `401` before evaluating the saved login.

I added the existing Docker hostname and direct media-host address to qBittorrent's semicolon-separated server-domain list at 20:49:22 EDT. Host-header validation remained enabled. Both saved-client tests returned HTTP `200` by 20:53:48 EDT.

## Impact

Sonarr and Radarr reported all download clients unavailable for about 7 hours 18 minutes. They couldn't send new grabs to qBittorrent or retrieve its queue and history through the configured client during that window.

Gluetun stayed healthy and qBittorrent stayed running in Gluetun's network namespace. The outage affected the Arr control path; I found no indication of public exposure or VPN bypass. I didn't run a file-integrity sweep because the reproduced failure ended at qBittorrent's HTTP Host-header check.

## Affected Assets

- Sonarr 4.0.19.2979 on `media-01`.
- Radarr 6.3.0.10514 on `media-01`.
- qBittorrent 5.2.3 Web API on `gluetun:8080`.
- The direct qBittorrent path at `192.168.40.42:8080`, which failed the same API Host-header check until mitigation.

Jellyfin, Seerr, Prowlarr, FlareSolverr, the Proton WireGuard tunnel, & qBittorrent's torrent engine remained running.

## Symptoms

Both Arr applications emitted:

```text
Unable to communicate with qBittorrent via Proton VPN.
Failed to connect to qBittorrent. Check your settings and qBittorrent configuration.
```

Six direct API probes from the two containers returned HTTP `401` in 2 to 21 ms. Changing only the Host header to `qbittorrent.<YOUR_BASE_DOMAIN>` returned HTTP `200` and qBittorrent version `v5.2.3`.

## Timeline

| Time | Event |
|---|---|
| 13:31:31 EDT | The HTTPS compatibility change recreated Gluetun. |
| 13:31:42 EDT | Docker started the recreated qBittorrent container in Gluetun's namespace. |
| 13:31:43 EDT | qBittorrent saved the single-domain value containing only its NPM hostname. |
| Exact minute not retained | The user reported both Arr download clients unavailable. |
| 20:49:22 EDT | I saved the three-entry domain list through qBittorrent's Web API. |
| 20:53:48 EDT | The final audit passed both saved-client tests, both health APIs, direct access, NPM TLS, & VPN port matching. |

## Findings

- Sonarr and Radarr resolved and connected to `gluetun:8080`; TCP and Docker DNS weren't the failure.
- `Host: gluetun:8080` and `Host: 192.168.40.42:8080` returned HTTP `401` before mitigation.
- `Host: qbittorrent.<YOUR_BASE_DOMAIN>` returned HTTP `200` from the same source and request path.
- The Arr addresses were inside qBittorrent's enabled `172.18.0.0/16` authentication-bypass subnet.
- Gluetun was healthy, qBittorrent shared Gluetun's exact container ID, & provider-forwarded port `51342` matched qBittorrent's listening port.
- The HTTPS route check passed during the original change because NPM sent the one allowed hostname. It didn't test the separate `gluetun` hostname used by both Arr applications.

## Root Cause

I replaced qBittorrent's effective server-domain allowance with only `qbittorrent.<YOUR_BASE_DOMAIN>` during the HTTPS compatibility change. qBittorrent validates the HTTP Host header before WebUI authentication, so the new value blocked the established Arr client path even though its DNS, TCP connection, subnet bypass, & VPN namespace were unchanged. I didn't edit either saved Arr client during mitigation; both saved-client tests passed after the Host-list repair.

The original verification tested the NPM route and qBittorrent WebUI response. It didn't include a saved-client test from Sonarr or Radarr after the server-domain change.

## Corrective Actions

1. I changed `web_ui_domain_list` to `qbittorrent.<YOUR_BASE_DOMAIN>;gluetun;192.168.40.42` through qBittorrent's Web API.
2. I confirmed `web_ui_host_header_validation_enabled=true` after the change.
3. I ran each Arr application's saved download-client test.
4. I verified direct qBittorrent access, NPM HTTPS with certificate validation, the Gluetun namespace, & Proton port matching.
5. I added the Arr-to-qBittorrent API probe to the documented compatibility verification boundary.

I created no backup or temporary configuration file.

## Validation

Radarr and Sonarr each returned HTTP `200` from `downloadclient/testall`, and both health endpoints returned `[]`. Three API calls from each container through `gluetun:8080` returned HTTP `200` in 2.3 ms or less.

Direct qBittorrent access and the NPM HTTPS root returned HTTP `200`; TLS verification returned `0`. Gluetun remained healthy, qBittorrent remained in Gluetun's exact namespace, & both port values were `51342`. Neither Arr log contained another qBittorrent connection error after mitigation.

## Lessons

A proxy-route test doesn't validate an application's separate backend hostname. qBittorrent's Host-header list needs every intentional entry path, while its authentication rules still decide who may use each path.

The regression test is two seconds long. Calling `/api/v2/app/version` from both Arr containers through `gluetun:8080` would have caught this before the HTTPS change was accepted.

## Follow-Ups

| Action | Status |
|---|---|
| Preserve the NPM hostname, `gluetun`, & direct media-host address in `WebUI\ServerDomains` | Complete |
| Run saved-client tests after future qBittorrent Host-header changes | Complete; added to the troubleshooting and configuration records |
| Verify Host-header validation remains enabled after correction | Complete |
| Confirm no post-mitigation connection errors | Complete |

## Closure Status

I closed ASU-QBIT-20260722-001 after the 20:53:48 EDT final audit. No open corrective action remains for this incident.

## Linked Records

- [qBittorrent Host Validation Blocked Arr Clients](../../../Platforms/Media%20Stack/Documentation/Troubleshooting/qBittorrent%20Host%20Validation%20Blocked%20Arr%20Clients%20-%202026-07-22.md)
- [Internal HTTPS Service Onboarding - 2026-07-22](../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
- [Step 1 diagnosis](Evidence/qBittorrent%20Host%20Validation%20Recovery%20-%202026-07-22/Logs/S01-Diagnosis-2026-07-22.md)
- [Step 2 correction and verification](Evidence/qBittorrent%20Host%20Validation%20Recovery%20-%202026-07-22/Logs/S02-Correction-and-Verification-2026-07-22.md)
