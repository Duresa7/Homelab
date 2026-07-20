# Wazuh Endpoint Re-enrollment - 2026-07-13

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

## Scope

I recorded & verified fresh Wazuh agent installations on `app-01` and `edge-01` after removing the old packages, client data, & manager identities. Verification required no manager, UniFi, or endpoint configuration change.

## Starting State

- Both endpoints were clean reinstall targets with no package, unit, process, or `/var/ossec` state.
- The Wazuh manager contained only its local ID `000` after the stale registrations were removed.
- Existing UniFi policies already targeted `192.168.72.2` with the `Wazuh Ports` group.

## Walkthrough

### Step 1: Install fresh endpoint agents

**UI path and action:** In Wazuh Dashboard > Agents management > Deploy new agent, I used the generated deployment workflow to install agent 4.14.5-1 on `app-01` and `edge-01` and create exact-name manager identities for both hosts.

**Observed result:** The workflow created manager IDs `004` & `005` with matching endpoint enrollment state. I didn't manually copy, import, or reuse an enrollment key.

**Verification:** Both endpoints had the supported package installed after the workflow completed.

**Evidence:** Step 1 has no command transcript or installation screenshot. Steps 2 & 3 independently verify the endpoint and manager state.

### Step 2: Verify the endpoint services, sessions, and policy path

**Action:** I used read-only SSH checks on both endpoints to inspect the Wazuh agent unit, enabled state, active session, & reachability to manager ports TCP 1514 and 1515. I also inspected the two existing Wazuh policies & their referenced port group through read-only UniFi checks.

**Observed result:** Both services were enabled & active, & each endpoint established its TCP 1514 session to the manager. Both UniFi policies were enabled, their destination remained `192.168.72.2`, & the `Wazuh Ports` group contained only TCP 1514 and 1515.

**Verification:** TCP 1514 and 1515 were reachable through the existing policy path, with no new endpoint, manager, or firewall configuration required and no new WAN exposure.

**Evidence:** The exact S02 text transcript remains in the local-only scrub quarantine & isn't linked from this public record. The resulting active sessions are corroborated by the manager dashboard in Step 3.

### Step 3: Confirm both endpoints in the manager dashboard

**UI path and action:** In Wazuh Dashboard > Endpoints, I refreshed the page after both agents completed their first check-in.

**Observed result:** The dashboard showed IDs `004` and `005` active on `node01`, with no disconnected, pending, or never-connected agents. The earlier `edge-01` never-connected state was a transient first-check-in delay.

**Verification:** `app-01` at `192.168.80.10` & `edge-01` at `192.168.90.10` both reported agent 4.14.5-1, cluster node `node01`, & state Active.

**Evidence:**

![Both fresh endpoints active](../../Evidence/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13/Screenshots/S03-Wazuh-Endpoints-Active-2026-07-13.png)

## Resulting State

| Endpoint | Manager identity | Address | Package | Service | Manager state |
|---|---|---|---|---|---|
| `app-01` | ID `004`, `app-01` | `192.168.80.10` | 4.14.5-1 | Enabled/active | Active on `node01` |
| `edge-01` | ID `005`, `edge-01` | `192.168.90.10` | 4.14.5-1 | Enabled/active | Active on `node01` |

No port forward or new firewall policy is required. TCP 1515 is used when an agent enrolls; TCP 1514 carries the ongoing agent session and events. Both are internal zone-to-Security-A paths, not WAN-exposed services.

## Retirement & Recovery

If either fresh identity must be retired, stop its endpoint service, remove that exact new manager ID, purge the endpoint state if a clean retry is desired, and repeat fresh enrollment. Do not restore IDs `002`/`003` or their former keys.

## Remaining Work

No Wazuh work remains for this change. `supabase-01` & `alpha-prod-01` aren't Wazuh endpoints; I removed both from the [Wazuh TODO](../TODO.md) on 2026-07-13.
