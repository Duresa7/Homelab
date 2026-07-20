# Wazuh Endpoint Agent Removal - 2026-07-13

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

## Scope

I removed the prepared Wazuh endpoint agents and their retained client state from `app-01` and `edge-01` so I could perform clean installs and fresh enrollment. The Wazuh manager, indexer, dashboard, other endpoint candidates, and non-Wazuh services were out of scope.

## Starting State

- `app-01` had `wazuh-agent` 4.14.5-1 installed, disabled, and inactive with `/var/ossec` present.
- `edge-01` had `wazuh-agent` 4.10.3-1 installed, disabled, and inactive with `/var/ossec` present.
- The old manager registrations had already been removed; manager ID `000` was the only retained entry.

## Decision

The earlier stopped state supported re-enrollment in place, but I wanted clean reinstalls. I purged the packages and removed their residual `/var/ossec` trees. My live check found the package repository retained on `app-01` and absent on `edge-01`.

## Actions and Results

1. I inspected both endpoints through SSH Manager and confirmed the installed versions, inactive service state, and exact residual path.
2. I disabled and stopped the service defensively, purged `wazuh-agent`, reloaded systemd, and removed the exact non-mounted `/var/ossec` path on each endpoint.
3. I re-ran verification after an inline process check matched its own command text. Exact daemon-name checks proved the package, unit, path, and Wazuh processes absent on both hosts.
4. I queried the manager with `agent_control -l`; it listed only local ID `000` and no endpoint identities.

## Resulting State

| Host | Package | Unit | `/var/ossec` | Wazuh processes | Install repository |
|---|---|---|---|---|---|
| `app-01` | Absent | Absent | Absent | Absent | Present |
| `edge-01` | Absent | Absent | Absent | Absent | Absent |

The manager contains only its local server identity, ID `000`. SSH access remained available throughout the work.

## Verification

| Step | Verified result |
|---|---|
| S01: Preflight | Expected packages were installed but inactive; `/var/ossec` existed on both hosts. |
| S02: Removal | APT/dpkg records show both packages reached `not-installed`; residual client data was removed. |
| S03: Final verification | Both endpoint checks returned exit 0 and the manager listed only ID `000`. |

## Rollback and Recovery

The removed endpoint state isn't a usable rollback point. Recovery follows the clean path I chose: install a current supported agent, enroll a new exact-name identity, enable and start the unit, and verify it active. Don't restore the removed 2026-07-13 identities.

## Remaining Work

- Install and freshly enroll `app-01` as `app-01` against manager `192.168.72.2`; its Wazuh APT repository is already present.
- Configure the Wazuh APT repository on `edge-01`, install the agent, and freshly enroll it as `edge-01` against `192.168.72.2`.
- Verify TCP 1515 enrollment, TCP 1514 event traffic, endpoint service state, and active manager status for each new identity.

These actions remain in the [Wazuh TODO](../TODO.md).

## Follow-up Completion

Later on 2026-07-13 I completed both fresh installations and enrollments. The validated outcome is recorded in [Wazuh Endpoint Re-enrollment - 2026-07-13](Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13.md); the remaining-work bullets above preserve this removal change's handoff state at the time it closed.
