# qBittorrent Host Validation Blocked Arr Clients

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Symptom

Sonarr and Radarr reported that all download clients were unavailable after the 2026-07-22 internal HTTPS change. Both applications named `qBittorrent via Proton VPN` and returned the same connection failure.

## Exact Error

```text
Unable to communicate with qBittorrent via Proton VPN.
Failed to connect to qBittorrent. Check your settings and qBittorrent configuration.
```

Gluetun remained healthy, qBittorrent remained running, & both Arr containers resolved and opened TCP connections to `gluetun:8080`. The failure occurred after the HTTP connection reached qBittorrent.

## Reproduction

I called `/api/v2/app/version` three times from each Arr container. All six requests reached qBittorrent in 2 to 21 ms and returned HTTP `401`.

Changing only the HTTP `Host` header isolated the rejection:

| Request host | Result before correction |
|---|---|
| `gluetun:8080` | HTTP `401`, body `Unauthorized` |
| `192.168.40.42:8080` | HTTP `401` |
| `qbittorrent.<YOUR_BASE_DOMAIN>` | HTTP `200`, body `v5.2.3` |

The [diagnosis transcript](../../../../Security/Incidents/qBittorrent/Evidence/Host%20Validation%20Recovery%20-%202026-07-22/Logs/S01-Diagnosis-2026-07-22.md) retains the request commands and outputs, safe configuration readback, container network state, & the explicit boundary for the filtered Arr log lines that weren't copied into the local artifact.

## Hypotheses and Tests

| Rank | Hypothesis | Prediction | Result |
|---:|---|---|---|
| 1 | `WebUI\ServerDomains` excluded the Arr hostname | The request succeeds when only `Host` changes to the HTTPS name | Confirmed: `401` became `200` |
| 2 | The Docker subnet bypass no longer covered Sonarr and Radarr | The current container addresses fall outside the configured subnet | Rejected: both addresses were inside `172.18.0.0/16` |
| 3 | The saved qBittorrent credentials changed | Requests using the allowed host still fail authentication | Not directly tested: the enabled subnet bypass accepted the probe without evaluating credentials. I changed no Arr client setting; both saved-client tests passed after the Host-list repair. |
| 4 | Gluetun or Docker networking failed | TCP connection or name resolution fails before HTTP | Rejected: every request reached qBittorrent in 21 ms or less |

## Root Cause

I set `WebUI\ServerDomains` to only `qbittorrent.<YOUR_BASE_DOMAIN>` while adding NPM. qBittorrent performs Host-header validation before WebUI authentication, so it rejected the existing Arr requests carrying `Host: gluetun:8080` even though their Docker subnet and target port were correct. I didn't edit either saved client; both tests passed after the Host-list repair.

The Gluetun and qBittorrent recreation made the new value active at 13:31 EDT. The Arr path remained unavailable until 20:49 EDT, an observed window of about 7 hours 18 minutes. The NPM route test passed because NPM sent the one allowed hostname; that test didn't exercise the separate Docker hostname used by Sonarr and Radarr.

## Corrective Action

I kept Host-header validation enabled and changed the semicolon-separated server-domain list through qBittorrent's Web API:

```text
qbittorrent.<YOUR_BASE_DOMAIN>;gluetun;192.168.40.42
```

The direct hostname supports NPM, `gluetun` supports Sonarr and Radarr, & `192.168.40.42` preserves direct IP-and-port access. The qBittorrent [WebUI API reference](https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-%28qBittorrent-4.1%29) defines `web_ui_domain_list` as a semicolon-separated list.

I created no backup. The API serialized the corrected value to the existing qBittorrent configuration at 20:49:22 EDT.

## Verification

- The persistent configuration reads `WebUI\ServerDomains="qbittorrent.<YOUR_BASE_DOMAIN>;gluetun;192.168.40.42"`.
- The preferences API reports `web_ui_host_header_validation_enabled=true`.
- Three Radarr and three Sonarr calls through `gluetun:8080` returned HTTP `200` in 2.3 ms or less.
- Radarr and Sonarr `downloadclient/testall` each returned HTTP `200`.
- Both `/api/v3/health` responses were empty arrays.
- Direct `http://192.168.40.42:8080/` and NPM HTTPS access returned HTTP `200`; TLS verification returned `0`.
- Gluetun was healthy, qBittorrent shared Gluetun's exact container namespace, & forwarded port `51342` matched qBittorrent's listening port.
- Radarr and Sonarr logged zero qBittorrent connection errors after 20:49:22 EDT.

The [correction and verification transcript](../../../../Security/Incidents/qBittorrent/Evidence/Host%20Validation%20Recovery%20-%202026-07-22/Logs/S02-Correction-and-Verification-2026-07-22.md) records the API change and resulting checks.

## Failed Attempts

I had no failed corrective attempt. One combined verification command returned exit code 1 because its Docker template assumed qBittorrent had a health-check object and its first forwarded-port path was wrong. I reran those read-only checks with separate templates and the configured `/gluetun/forwarded_port` path; the service setting didn't change during that correction.

## Rollback

The previous single-domain value is known, but restoring it would reproduce the outage. If I must remove the direct IP path later, I can remove only `192.168.40.42`; `qbittorrent.<YOUR_BASE_DOMAIN>` and `gluetun` are required while NPM and the Arr clients use their current paths.

## Linked Records

- [qBittorrent Arr Client Outage Incident](../../../../Security/Incidents/qBittorrent/Arr Client Outage - 2026-07-22.md)
- [Internal HTTPS Service Onboarding - 2026-07-22](../../../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
- [Media Stack configuration reference](../../Configuration/README.md)
