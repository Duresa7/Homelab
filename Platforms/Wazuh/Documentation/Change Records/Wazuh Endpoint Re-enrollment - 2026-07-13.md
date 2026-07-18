# Wazuh Endpoint Re-enrollment - 2026-07-13

**Created:** 2026-07-13  
**Last updated:** 2026-07-17

## Scope

Record and verify the operator-performed clean installation and fresh enrollment of Wazuh agents on `app-01` and `edge-01` after the old packages, client data, and manager identities were removed. No manager, UniFi, or endpoint configuration mutation was needed during verification.

## Starting State

- Both endpoints were clean reinstall targets with no package, unit, process, or `/var/ossec` state.
- The Wazuh manager contained only its local ID `000` after the stale registrations were removed.
- Existing UniFi policies already targeted `192.168.72.2` with the `Wazuh Ports` group.

## Actions and Decisions

1. The operator used the Wazuh deployment workflow to install agent 4.14.5-1 and create exact-name identities `app-01` and `edge-01`.
2. The deployment workflow created fresh manager IDs `004` and `005` and their matching endpoint enrollment state. Because the resulting agents are active, no manual key copy, import, or reuse is required.
3. Read-only SSH checks verified both units enabled/active, established TCP 1514 sessions, and TCP 1514/1515 reachability.
4. Read-only UniFi checks verified the two Wazuh policies enabled, the destination fixed to `192.168.72.2`, and the referenced `Wazuh Ports` group containing only 1514 and 1515.
5. A refreshed dashboard capture verified both new identities active. The earlier `edge-01` never-connected state was a transient first-check-in delay.

## Resulting State

| Endpoint | Manager identity | Address | Package | Service | Manager state |
|---|---|---|---|---|---|
| `app-01` | ID `004`, `app-01` | `192.168.80.10` | 4.14.5-1 | Enabled/active | Active on `node01` |
| `edge-01` | ID `005`, `edge-01` | `192.168.90.10` | 4.14.5-1 | Enabled/active | Active on `node01` |

No port forward or new firewall policy is required. TCP 1515 is used when an agent enrolls; TCP 1514 carries the ongoing agent session and events. Both are internal zone-to-Security-A paths, not WAN-exposed services.

## Verification and Evidence

| Step | Evidence | Result |
|---|---|---|
| S01 — Operator installation | No command transcript was available because the operator performed the dashboard-guided installation outside this task. Result independently verified in S02 and S03. | Fresh supported packages and exact-name manager identities exist. |
| S02 — Live endpoint and network verification | [Endpoint and UniFi verification](../../Evidence/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13/Logs/S02-Endpoint-and-UniFi-Verification-2026-07-13.md) | Both agents enabled/active and connected through existing policies. |
| S03 — Manager dashboard | [Both fresh endpoints active](../../Evidence/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13/Screenshots/S03-Wazuh-Endpoints-Active-2026-07-13.png) | Dashboard shows IDs `004` and `005` active, with no disconnected, pending, or never-connected agents. |

## Rollback and Recovery

If either fresh identity must be retired, stop its endpoint service, remove that exact new manager ID, purge the endpoint state if a clean retry is desired, and repeat fresh enrollment. Do not restore IDs `002`/`003` or their former keys.

## Remaining Work

None. `supabase-01` and `alpha-prod-01` were subsequently confirmed out of scope — they were never intended as Wazuh endpoints — and removed from the [Wazuh TODO](../TODO.md) on 2026-07-13.
