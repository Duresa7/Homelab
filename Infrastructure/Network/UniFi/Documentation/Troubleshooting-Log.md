# UniFi Network Troubleshooting Log

**Created:** 2026-07-12  
**Last updated:** 2026-07-17

Chronological problems encountered while operating the UniFi network configuration. Durable change narratives and evidence remain in their owning change records.

## 2026-07-12 — Enabling `create_allow_respond` after policy creation did not create a return rule

**Context:** Security-A migration cross-zone Wazuh and monitoring policies.

**Symptom:** New forward policies existed and showed `create_allow_respond=true` after an update, but traffic from `security-01` to Proxmox and DMZ endpoints still timed out. The controller had not created the expected hidden `(Return)` companion.

**Failed attempt:** Updating an already-created policy from `create_allow_respond=false` to `true` changed the visible policy data but did not materialize the controller-maintained reverse policy.

**Root cause:** On this controller, the return companion is created only when the policy is initially created with automatic response enabled. Toggling the flag later is not equivalent.

**Corrective action:** Re-created the four required cross-zone policies with automatic response enabled at creation, validated the return path, and removed the superseded forward-only policies. A single-port Proxmox test policy was used to isolate the behavior and was removed after the final combined policy worked.

**Verification:** From `security-01`, `192.168.90.10:9100`, `192.168.70.10:9100`, and `192.168.70.10:8006` each returned HTTP 200. The live controller showed the intended four custom policies with automatic response enabled and no superseded/test policies.

## 2026-07-12 — MCP policy deletion disabled

**Symptom:** The UniFi MCP rejected firewall-policy deletion with: `Delete is disabled by policy for firewall_policies. Set UNIFI_POLICY_NETWORK_FIREWALL_POLICIES_DELETE=true`.

**Corrective action:** Used the authenticated UniFi web interface to remove only the exact old, superseded, and test policy names authorized by the migration plan.

**Verification:** A fresh controller API listing returned 32 enabled user-defined policies, including all seven Security-A policies and none of the three old MGMT-A policies or temporary/superseded entries.
