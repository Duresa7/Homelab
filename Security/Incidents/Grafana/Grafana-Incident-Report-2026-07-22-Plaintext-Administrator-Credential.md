# Grafana Plaintext Administrator Credential Incident

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Incident Metadata

| Field | Value |
|---|---|
| Incident ID | ASU-GRAFANA-20260722-001 |
| Detected | 2026-07-22 during the internal HTTPS compatibility review; exact minute not retained |
| Mitigated | 2026-07-22; secret-free container started at 13:31:45 EDT and authenticated validation completed by 13:46:50 EDT |
| Status | Closed |
| Severity | SEV-4 |
| Impact type | Potential credential disclosure; no confirmed unauthorized use |
| Affected service | Grafana 12.4.1 on `security-01` |
| Affected asset | Grafana administrator credential |

## Summary

I found a Grafana bootstrap administrator password value in `/home/<YOUR_ADMIN_USERNAME>/monitoring/docker-compose.yml` while adding the internal HTTPS name on 2026-07-22. Grafana only needs that bootstrap value when it initializes its database, but the Compose definition continued to inject the plaintext value into each recreated container.

I removed the variable, recreated Grafana, rotated the administrator credential, & verified an authenticated Grafana request. Neither the credential nor its storage location is retained in this repository, evidence, or incident record.

## Impact

The plaintext value was readable to the `<YOUR_ADMIN_USERNAME>` account and root on `security-01`. The Compose file had mode `0664`, but the administrator's home directory had mode `0750` and its private group had no supplementary members, which blocked traversal by other local users.

I found no copy in tracked repository content. Grafana also had no public DNS record or WAN port forward; access remained on internal network paths. A compromise of the administrator account or root while the old file existed could still have disclosed the value.

## Affected Assets

- Grafana 12.4.1 container on `security-01` at `192.168.72.2`.
- `/home/<YOUR_ADMIN_USERNAME>/monitoring/docker-compose.yml` before the 2026-07-22 recreation.
- The Grafana administrator account.

Prometheus configuration, Grafana dashboards, data sources, & the SQLite database showed no availability or integrity impact during remediation.

## Symptoms

Grafana remained healthy. The incident was a configuration finding, not an outage: the live Compose file contained `GF_SECURITY_ADMIN_PASSWORD` with a plaintext value after Grafana had already initialized its database.

## Timeline

| Time | Event |
|---|---|
| 2026-07-22, exact minute not retained | I found the bootstrap administrator value during the internal HTTPS compatibility review. |
| 2026-07-22 13:31:44 EDT | I saved the Compose definition without `GF_SECURITY_ADMIN_PASSWORD`. |
| 2026-07-22 13:31:45 EDT | Docker started the recreated Grafana container without the variable. |
| 2026-07-22, exact minute not retained | I rotated the Grafana administrator credential. |
| 2026-07-22 13:46:50 EDT | Grafana logged an authenticated request for `/api/live/ws` from the Internal-zone client. |
| 2026-07-22, later verification | Compose and container environment checks both reported the administrator password variable absent; `/api/health` returned database `ok`. |

## Findings

- The Compose file was owned by the administrator account and its private group with mode `0664`.
- The administrator's home directory was `0750`; its private group had no listed supplementary members.
- The current Compose file contains no `GF_SECURITY_ADMIN_PASSWORD` entry.
- The current Grafana container environment contains no `GF_SECURITY_ADMIN_PASSWORD` entry.
- Grafana 12.4.1 reports database `ok` from `/api/health`.
- Current-container logs contained zero matches for invalid username, failed authentication, unauthorized, or login-failed events during the inspected 12-hour window.
- The current logs begin with the recreated container. They can't prove whether the credential was used before 13:31:45 EDT.

## Root Cause

I left a one-time bootstrap secret in the long-lived Compose definition after Grafana initialized its database. That converted an installation input into a persistent plaintext configuration value and caused Docker to place it in the container environment on every recreation.

## Corrective Actions

1. I removed `GF_SECURITY_ADMIN_PASSWORD` from the live Compose definition.
2. I recreated the Grafana container and confirmed the variable was absent from its environment.
3. I rotated the Grafana administrator credential so the removed value no longer authenticated.
4. I verified Grafana health and an authenticated request to `/api/live/ws`.
5. I checked tracked repository content and retained evidence for the variable and found no credential value.

## Validation

The current container is running Grafana 12.4.1. `/api/health` returned database `ok`, the Compose and container checks both returned `compose_admin_password_variable=absent` and `container_admin_password_variable=absent`, & Grafana logged the authenticated `/api/live/ws` request at 13:46:50 EDT.

I found no evidence of unauthorized administrative use in the retained current-container logs. Because Docker recreation replaced the prior container log boundary, I classify this as potential disclosure with no confirmed compromise, not proof that the old credential was never used.

## Lessons

A bootstrap password doesn't belong in Compose after the application database exists. Removing it from the file isn't enough; I also need to recreate the container, rotate the credential, & inspect the resulting environment.

File mode `0664` wasn't the primary boundary because the administrator's `0750` home directory blocked other-user traversal. The safer rule is still to keep reusable credentials out of Compose rather than rely on parent-directory permissions.

## Follow-Ups

| Action | Status |
|---|---|
| Remove the bootstrap value from Compose and container environment | Complete |
| Rotate the administrator credential | Complete |
| Verify Grafana health and authenticated access | Complete |
| Confirm tracked documentation and evidence retain no credential value | Complete |

## Linked Records

- [Grafana bootstrap administrator credential troubleshooting](../../../Platforms/Prometheus/Documentation/Troubleshooting/Grafana%20Bootstrap%20Administrator%20Credential%20-%202026-07-22.md)
- [Internal HTTPS Service Onboarding - 2026-07-22](../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
