# Grafana Bootstrap Administrator Credential

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Symptom

I found `GF_SECURITY_ADMIN_PASSWORD` with a plaintext value in `/home/dkadi/monitoring/docker-compose.yml` during the 2026-07-22 internal HTTPS change. Grafana was healthy; this was a credential-handling problem rather than an availability failure.

## Exact Error

Grafana emitted no application error. The defect was the continued presence of a one-time bootstrap secret in a long-lived Compose definition after the Grafana database already existed.

## Failed Attempts

I didn't have a failed remediation attempt. I removed the variable, recreated Grafana, rotated the administrator credential, & validated the resulting state once.

## Hypotheses and Tests

| Hypothesis | Test | Result |
|---|---|---|
| The Compose file still exposed the old value | Search the live file for `GF_SECURITY_ADMIN_PASSWORD` after editing | Absent |
| Docker retained the value from the old container | Inspect the recreated container environment | Absent |
| The remediation broke Grafana | Query `http://127.0.0.1:3000/api/health` | Grafana 12.4.1 returned database `ok` |
| The rotated administrator login failed | Inspect the authenticated session result and Grafana log | Authenticated `/api/live/ws` request logged at 13:46:50 EDT |
| The value entered tracked documentation | Search tracked repository content | No credential value found |

## Root Cause

I left the bootstrap administrator value in Compose after the first Grafana database initialization. Docker therefore injected the plaintext value into every container created from that definition.

## Corrective Action

I removed the variable from Compose, recreated Grafana, rotated the administrator credential, & verified authenticated access. I didn't retain the credential or its storage location in repository documentation or evidence.

## Verification

The live Compose file and recreated container environment contain no `GF_SECURITY_ADMIN_PASSWORD` entry. Grafana reports database `ok`, & current-container logs contained zero failed-authentication matches in the inspected 12-hour window. Those logs begin after recreation, so they don't establish the pre-remediation access history.

The full security assessment and timeline are in [Grafana Plaintext Administrator Credential Incident](../../../../Security/Incidents/Grafana/Plaintext Administrator Credential - 2026-07-22.md).
