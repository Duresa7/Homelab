# Fresh edge-01 identity initially showed never connected

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

My first screenshot after install showed `app-01` ID `004` active and the newly created `edge-01` ID `005` never connected. Read-only SSH verification then proved `edge-01` agent 4.14.5-1 was enabled and active with an established session from `192.168.90.10` to `192.168.72.2:1514`; TCP 1515 was also reachable. UniFi showed the DMZ-to-Wazuh allow policy enabled with the exact internal destination and port group.

A refreshed dashboard screenshot showed both identities active on `node01`, so no corrective change was required. This was the normal delay between creating the manager identity and the endpoint's first successful check-in. The full record is in [Wazuh Endpoint Re-enrollment - 2026-07-13](../Change%20Records/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13.md).
