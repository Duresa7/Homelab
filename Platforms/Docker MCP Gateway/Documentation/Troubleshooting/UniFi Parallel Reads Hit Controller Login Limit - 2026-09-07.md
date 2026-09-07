# UniFi Parallel Reads Hit Controller Login Limit

**Created:** 2026-09-07  
**Last updated:** 2026-09-07

## Symptom

I listed all 16 Network Lists through Executor and UniFi MCP successfully, then requested six address-group detail records in parallel. Three returned `Not connected to controller`; an immediate sequential retry failed too. I stopped before changing any controller configuration.

## Diagnosis

I checked the gateway host through SSH Manager MCP. Executor and both gateway containers were healthy. I inspected the installed UniFi MCP image in temporary containers with networking disabled; both the list and detail methods call `ensure_connected()`, so the detail method was not missing initialization. Those temporary containers were removed automatically when the reads finished.

After waiting, I read each of the three previously failing groups sequentially through UniFi MCP. All three succeeded. At 10:21 AM Eastern I repeated the six parallel detail reads while collecting filtered logs from the managed UniFi MCP containers on `docker-blue`. Four calls succeeded and two failed. A failing container logged HTTP 429 with `You've reached the login attempt limit`, then blocked reconnects for 60 seconds. The firewall tool reduced that authentication error to `Not connected to controller`.

The gateway started separate short-lived UniFi MCP containers for the requests. Each initialized its own controller connection and logged in, so parallel reads became a burst of logins. The controller rejected that burst. I captured the diagnostic output in the working session; I did not retain a separate complete terminal transcript.

The installed source confirms the error path: `firewall_manager.py` calls `ensure_connected()` at lines 1405–1406 and replaces a false result with the generic error. `connection_manager.py` logs terminal authentication failures, blocks reconnects, and returns false from initialization. These paths are inside `/app/packages/unifi-core/src/unifi_core/network/managers/` in `homelab/unifi-network-mcp:0.29.3-full-access`.

## Recovery and Remaining Work

I let the login limit clear and use sequential UniFi calls with at least 30 seconds between requests. The three successful individual reads verified recovery before the controlled parallel reproduction. Closely spaced sequential reads subsequently hit the same limit, so serialization alone was insufficient. After another cooldown, all six name-only address-group updates succeeded with the pauses. This is an observed workaround, not a measured controller rate-limit threshold.

The subsequent Network List readback confirmed the six new names with unchanged IDs and memberships. The final policy check matched all 23 original referencing policies to their pre-rename configurations and group IDs. I recorded the rename and the separate additions seen later that day in [Policy features and Network Lists](../../../../Infrastructure/Network/UniFi/Configuration/objects.md).

A shared persistent UniFi MCP process would let requests reuse one authenticated connection. That change remains open; I did not change the gateway deployment, credentials, or controller configuration during diagnosis. The generic firewall-tool error also remains unchanged.
