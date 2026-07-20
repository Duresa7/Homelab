# Wazuh Recovery

**Created:** 2026-07-13  
**Last updated:** 2026-07-18

## Service Recovery Order

1. Verify VM 200 is running with VLAN 72 and address `192.168.72.2`.
2. Verify `wazuh-indexer`, then `wazuh-manager`, then `wazuh-dashboard` are active.
3. Verify TCP listeners 1514, 1515, 443, and 55000.
4. Verify dashboard/API responses locally before testing from another zone.
5. List manager agents without extracting keys and confirm expected endpoint state.

Do not weaken firewall policy to compensate for a failed local service.

## 2026-07-13 Agent Removal Recovery

My 2026-07-13 clean-removal change intentionally deleted `/var/ossec` from `app-01` and `edge-01`. Their former configuration backups and client keys no longer exist, so they can't serve as rollback points.

- Manager rollback point: `/var/ossec/etc/client.keys.bak.security-monitoring-cleanup-20260713` on `security-01`.
- Endpoint recovery: install a current supported agent, enroll a new exact-name identity against `192.168.72.2`, then enable/start and verify it active.

The manager backup preserves the pre-reset registry only. Restoring it would reintroduce obsolete identities without corresponding endpoint state, so it isn't a valid rollback for the endpoint removal. Use fresh installation and enrollment instead.

## VM Network Rollback

The Security-A migration's VM/network rollback procedure remains in the [Security-A migration change record](../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md#rollback-points). Use it only for a network-level rollback, not routine agent recovery.
