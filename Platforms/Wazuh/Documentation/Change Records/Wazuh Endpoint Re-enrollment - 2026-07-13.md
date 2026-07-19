# Wazuh Endpoint Re-enrollment - 2026-07-13

**Created:** 2026-07-13  
**Last updated:** 2026-07-18

## Scope

I recorded and verified the clean installation and fresh enrollment of Wazuh agents on `app-01` and `edge-01` that I performed after removing the old packages, client data, and manager identities. No manager, UniFi, or endpoint configuration mutation was needed during verification.

## Starting State

- Both endpoints were clean reinstall targets with no package, unit, process, or `/var/ossec` state.
- The Wazuh manager contained only its local ID `000` after the stale registrations were removed.
- Existing UniFi policies already targeted `192.168.72.2` with the `Wazuh Ports` group.

## Actions and Decisions

1. I used the Wazuh deployment workflow to install agent 4.14.5-1 and create the exact-name identities `app-01` and `edge-01`.
2. The deployment workflow created fresh manager IDs `004` and `005` and their matching endpoint enrollment state. Because the resulting agents are active, no manual key copy, import, or reuse was required.
3. My read-only SSH checks verified both units enabled and active, established TCP 1514 sessions, and TCP 1514/1515 reachability.
4. My read-only UniFi checks verified the two Wazuh policies enabled, the destination fixed to `192.168.72.2`, and the referenced `Wazuh Ports` group containing only 1514 and 1515.
5. A refreshed dashboard capture confirmed both new identities active. The earlier `edge-01` never-connected state was a transient first-check-in delay.

## Resulting State

| Endpoint | Manager identity | Address | Package | Service | Manager state |
|---|---|---|---|---|---|
| `app-01` | ID `004`, `app-01` | `192.168.80.10` | 4.14.5-1 | Enabled/active | Active on `node01` |
| `edge-01` | ID `005`, `edge-01` | `192.168.90.10` | 4.14.5-1 | Enabled/active | Active on `node01` |

No port forward or new firewall policy is required. TCP 1515 is used when an agent enrolls; TCP 1514 carries the ongoing agent session and events. Both are internal zone-to-Security-A paths, not WAN-exposed services.

## Verification

| Step | Result |
|---|---|
| S01: Installation | Fresh supported packages and exact-name manager identities exist. I ran the dashboard-guided installation outside this task, so there is no command transcript; I verified the outcome independently in S02 and S03. |
| S02: Live endpoint and network verification | Both agents enabled and active and connected through existing policies. |
| S03: Manager dashboard | The dashboard shows IDs `004` and `005` active, with no disconnected, pending, or never-connected agents. |

The manager dashboard confirmed both fresh endpoints active:

![Both fresh endpoints active](../../Evidence/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13/Screenshots/S03-Wazuh-Endpoints-Active-2026-07-13.png)

## Rollback and Recovery

If either fresh identity must be retired, stop its endpoint service, remove that exact new manager ID, purge the endpoint state if a clean retry is desired, and repeat fresh enrollment. Do not restore IDs `002`/`003` or their former keys.

## Remaining Work

None remain. I later confirmed `supabase-01` and `alpha-prod-01` out of scope; they were never intended as Wazuh endpoints, so I removed them from the [Wazuh TODO](../TODO.md) on 2026-07-13.
