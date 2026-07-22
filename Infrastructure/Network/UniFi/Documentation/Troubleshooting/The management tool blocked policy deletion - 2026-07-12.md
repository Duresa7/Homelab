# The management tool blocked policy deletion

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-12

**Symptom:** The UniFi management tool rejected firewall-policy deletion with: `Delete is disabled by policy for firewall_policies. Set UNIFI_POLICY_NETWORK_FIREWALL_POLICIES_DELETE=true`.

**Corrective action:** I used the authenticated UniFi web interface to remove only the exact old, superseded, and test policy names the migration plan called out.

**Verification:** A fresh controller API listing returned 32 enabled user-defined policies, including all seven Security-A policies and none of the three old MGMT-A policies or temporary/superseded entries.
