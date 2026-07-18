# Wazuh Endpoint Agent Removal - 2026-07-13

**Created:** 2026-07-13  
**Last updated:** 2026-07-17

## Scope

Completely remove the prepared Wazuh endpoint agents and retained client state from `app-01` and `edge-01` so the operator can perform clean installs and fresh enrollment. The Wazuh manager, indexer, dashboard, other endpoint candidates, and non-Wazuh services were out of scope.

## Starting State

- `app-01` had `wazuh-agent` 4.14.5-1 installed, disabled, and inactive with `/var/ossec` present.
- `edge-01` had `wazuh-agent` 4.10.3-1 installed, disabled, and inactive with `/var/ossec` present.
- The old manager registrations had already been removed; manager ID `000` was the only retained entry.

## Decision

The earlier stopped/key-cleared state supported re-enrollment in place, but the operator requested clean reinstalls. The packages were therefore purged and their residual `/var/ossec` trees removed. Each path was resolved and rejected if it was anything other than exactly `/var/ossec` or if it was a mount point before recursive removal. Package repositories were not deliberately removed because they are non-secret installation prerequisites; the live check found the repository retained on `app-01` and absent on `edge-01`.

## Actions and Results

1. Inspected both endpoints through SSH Manager and confirmed the installed versions, inactive service state, and exact residual path.
2. Disabled/stopped the service defensively, purged `wazuh-agent`, reloaded systemd, and removed the exact non-mounted `/var/ossec` path on each endpoint.
3. Re-ran verification after an inline process check matched its own command text. Exact daemon-name checks proved the package, unit, path, and Wazuh processes absent on both hosts.
4. Queried the manager with `agent_control -l`; it listed only local ID `000` and no endpoint identities.
5. Removed all protected temporary credential files from the operator workstation and manager host.

## Resulting State

| Host | Package | Unit | `/var/ossec` | Wazuh processes | Install repository |
|---|---|---|---|---|---|
| `app-01` | Absent | Absent | Absent | Absent | Present |
| `edge-01` | Absent | Absent | Absent | Absent | Absent |

The manager contains only its local server identity, ID `000`. SSH access remained available throughout the work.

## Verification and Evidence

| Step | Evidence | Verified result |
|---|---|---|
| S01 — Preflight | [Endpoint preflight](../../Evidence/Wazuh%20Endpoint%20Agent%20Removal%20-%202026-07-13/Logs/S01-Endpoint-Preflight-2026-07-13.md) | Expected packages were installed but inactive; `/var/ossec` existed on both hosts. |
| S02 — Removal | [Package and data removal](../../Evidence/Wazuh%20Endpoint%20Agent%20Removal%20-%202026-07-13/Logs/S02-Package-and-Data-Removal-2026-07-13.md) | APT/dpkg records show both packages reached `not-installed`; residual client data was removed. |
| S03 — Final verification | [Endpoint and manager verification](../../Evidence/Wazuh%20Endpoint%20Agent%20Removal%20-%202026-07-13/Logs/S03-Endpoint-and-Manager-Verification-2026-07-13.md) | Both endpoint checks returned exit 0 and the manager listed only ID `000`. |

## Rollback and Recovery

The removed endpoint client state is intentionally not recoverable from repository evidence because it contained enrollment material. Recovery is the requested clean path: install a current supported agent, enroll a new exact-name identity, enable/start the unit, and verify it active. Do not restore the removed 2026-07-13 keys or identities.

## Remaining Operator Work

- Install and freshly enroll `app-01` as `app-01` against manager `192.168.72.2`; its Wazuh APT repository is already present.
- Configure the Wazuh APT repository on `edge-01`, install the agent, and freshly enroll it as `edge-01` against `192.168.72.2`.
- Verify TCP 1515 enrollment, TCP 1514 event traffic, endpoint service state, and active manager status for each new identity.

These actions remain in the [Wazuh TODO](../TODO.md).

## Follow-up Completion

Later on 2026-07-13, the operator completed both fresh installations and enrollments. The validated outcome is recorded in [Wazuh Endpoint Re-enrollment - 2026-07-13](Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13.md); the remaining-work bullets above preserve this removal change's handoff state at the time it closed.
