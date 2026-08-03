# Wazuh

**Created:** 2026-07-13  
**Last updated:** 2026-08-03

Wazuh provides endpoint detection and security monitoring for the homelab. The manager, indexer, & dashboard packages are version 4.14.6-1. Those services and the API run on `security-01` / `wazuh-01` at `192.168.72.2` on Security-A/VLAN 72.

**Owner:** Homelab security monitoring

## Layout

- `Configuration/`: reader-editable reference to the live endpoints, paths, & agent state.
- `Source/agent-deployment/`: idempotent Ansible deployment for the expanded Linux fleet.
- `Documentation/Runbook.md`: routine health checks and enrollment workflow.
- `Documentation/Change Records/`: dated endpoint and manager changes.
- `Documentation/Dependencies.md`: network, host, and service dependencies.
- `Documentation/Recovery.md`: manager and agent recovery procedures.
- `Documentation/Resources.md`: verified VM and package specifications.
- `Documentation/Troubleshooting/`: issue index and one dated record per operational problem.
- `Documentation/TODO.md`: agent enrollment backlog.
- `Evidence/`: step-based verification transcripts for bounded changes.

## Service Endpoints

| Service | Endpoint | Use |
|---|---|---|
| Wazuh dashboard | `https://wazuh.alphasecunited.com/`; direct fallback `https://192.168.72.2/` | Human web interface through internal NPM |
| Wazuh API | `https://192.168.72.2:55000/` | Authenticated API |
| Agent events | `192.168.72.2:1514/tcp` | Enrolled agent traffic |
| Agent enrollment | `192.168.72.2:1515/tcp` | New agent registration |

NPM presents the Let's Encrypt wildcard certificate to internal dashboard clients and connects to Wazuh's existing HTTPS 443 listener. The direct dashboard still uses its current self-signed certificate. An HTTP `302` from the dashboard and HTTP `401` from the unauthenticated API root are expected healthy responses. The API and agent ports aren't published through NPM. See [Internal HTTPS Service Onboarding - 2026-07-22](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

## Current Agent State

- `app-01` is enrolled as manager ID `004` from `192.168.80.10`; agent 4.14.6-1 is enabled, active, & connected.
- `edge-01` is enrolled as manager ID `005` from `192.168.90.10`; agent 4.14.5-1 is enabled, active, & connected.
- `alpha-prod-01`, `docker-blue`, `media-01`, & `ansible-01` are enrolled as IDs `006` through `009`. Each runs held package 4.14.6-1, has an established TCP 1514 session, & reports synchronized.
- `monitor-01`, `docker-network`, `kasm-01`, `grey-server`, `purple-server`, `blue-server`, & `red-server` are enrolled as IDs `010` through `016`. Each runs held package 4.14.6-1, has an established TCP 1514 session, & reports synchronized.
- `green-server` is enrolled as ID `017` with held package 4.14.6-1, an established TCP 1514 session, & synchronized status.
- Grey, Purple, Blue, Red, & Green also belong to `proxmox`. The Wazuh dashboard returned all five as active when filtered on that group.

The shared `default` policy monitors `/etc/ssh` & `/etc/cron.d`. The `edge` policy adds `/etc/cloudflared` only for `edge-01`. I removed the unused custom WordPress volume policy and its rollback copy on 2026-08-03.

The completed expansion is recorded in [Wazuh Agent Fleet Deployment - 2026-08-03](Documentation/Change%20Records/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03.md). The [configuration reference](Configuration/README.md) records all 14 live identities and policy fragments.

The completed reinstall is documented in [Wazuh Endpoint Re-enrollment - 2026-07-13](Documentation/Change%20Records/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13.md). The preceding clean removal is in [Wazuh Endpoint Agent Removal - 2026-07-13](Documentation/Change%20Records/Wazuh%20Endpoint%20Agent%20Removal%20-%202026-07-13.md).
