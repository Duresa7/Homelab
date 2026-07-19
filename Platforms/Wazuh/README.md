# Wazuh

**Created:** 2026-07-13  
**Last updated:** 2026-07-18

Wazuh provides endpoint detection and security monitoring for the homelab. The manager, indexer, dashboard, and API run on `security-01` / `wazuh-01` at `192.168.72.2` on Security-A/VLAN 72.

**Owner:** Homelab security monitoring

## Layout

- `Configuration/`: secret-free reference to the live endpoints, paths, and agent state.
- `Documentation/Runbook.md`: routine health checks and enrollment workflow.
- `Documentation/Change Records/`: dated endpoint and manager changes.
- `Documentation/Dependencies.md`: network, host, and service dependencies.
- `Documentation/Recovery.md`: manager and agent recovery procedures.
- `Documentation/Resources.md`: verified VM and package specifications.
- `Documentation/Troubleshooting-Log.md`: chronological operational problems and fixes.
- `Documentation/TODO.md`: agent enrollment backlog.
- `Evidence/`: step-based verification transcripts for bounded changes.

## Service Endpoints

| Service | Endpoint | Use |
|---|---|---|
| Wazuh dashboard | `https://192.168.72.2/` | Human web interface |
| Wazuh API | `https://192.168.72.2:55000/` | Authenticated API |
| Agent events | `192.168.72.2:1514/tcp` | Enrolled agent traffic |
| Agent enrollment | `192.168.72.2:1515/tcp` | New agent registration |

The dashboard uses its current self-signed certificate. An HTTP `302` from the dashboard and HTTP `401` from the unauthenticated API root are expected healthy responses.

## Current Agent State

- `app-01` is freshly enrolled as manager ID `004` from `192.168.80.10`; agent 4.14.5-1 is enabled, active, and connected.
- `edge-01` is freshly enrolled as manager ID `005` from `192.168.90.10`; agent 4.14.5-1 is enabled, active, and connected.
- I created both endpoint identities and their enrollment keys through my fresh deployment workflow. No manual key reuse or transfer remains.
- `app-01` and `edge-01` are the only intended Wazuh endpoints; no further agent enrollment is planned.

The completed reinstall is documented in [Wazuh Endpoint Re-enrollment - 2026-07-13](Documentation/Change%20Records/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13.md). The preceding clean removal is in [Wazuh Endpoint Agent Removal - 2026-07-13](Documentation/Change%20Records/Wazuh%20Endpoint%20Agent%20Removal%20-%202026-07-13.md).
