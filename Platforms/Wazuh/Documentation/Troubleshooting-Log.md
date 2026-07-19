# Wazuh Troubleshooting Log

**Created:** 2026-07-13  
**Last updated:** 2026-07-18

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| 1 | 2026-07-13 | `app-01` was using the old `wp-01` identity and both existing agents targeted retired manager address `192.168.70.20` | I stopped/disabled `app-01` and `edge-01`, repointed both to `192.168.72.2`, cleared stale keys, and removed manager IDs 002/003 | Resolved; fresh IDs 004/005 active |
| 2 | 2026-07-13 | The inline post-purge process assertion returned exit 33 after matching the purge command's own `/var/ossec` and `wazuh-agent` arguments | I re-ran verification after the command exited, using exact daemon names instead of argument substring matching | Resolved; no Wazuh processes present |
| 3 | 2026-07-13 | The first local protected credential-file cleanup could neither overwrite nor remove the file because its intentionally read-only ACL denied write/delete access | I granted my own account full control, overwrote the file with random bytes, removed it, and verified absence | Resolved; no local or remote staging file remains |
| 4 | 2026-07-13 | The first post-install screenshot showed fresh `edge-01` ID `005` as never connected | Endpoint checks found an active service and an established TCP 1514 session; a refreshed dashboard capture showed both IDs `004` and `005` active | Resolved; transient first-check-in delay |

## 1. Incorrect and stale endpoint identities

My live audit found manager ID `002` `edge-01` and ID `003` `wp-01`, both disconnected. Endpoint inspection proved `app-01` carried the `wp-01` key while `edge-01` carried its matching old key; both configurations still used the manager's retired MGMT-A address.

I stopped and disabled the old endpoint services before clearing their keys. I wrote the new manager address into each configuration, removed the two manager registrations by exact ID, and confirmed the manager then held only local ID `000`. `supabase-01` and `alpha-prod-01` had no installed agent, so I left them unchanged.

## 2. Post-purge process-check self-match

My package purge and residual-data removal reported `PACKAGE_ABSENT`, `UNIT_ABSENT`, and `OSSEC_PATH_ABSENT` on both endpoints. Its final `pgrep -af '/var/ossec|wazuh-agent'` check still returned exit 33 because it matched the running shell command text itself.

After that shell exited, I ran a detached check against the exact Wazuh and OSSEC daemon process names. Both hosts returned exit 0 with package, unit, `/var/ossec`, and all named processes absent. This was a verification-command defect, not a failed removal. The full record is in [Wazuh Endpoint Agent Removal - 2026-07-13](Change%20Records/Wazuh%20Endpoint%20Agent%20Removal%20-%202026-07-13.md).

## 3. Protected local credential-file ACL cleanup

I intentionally restricted the temporary sudo-password file to read-only access for my own account before upload. My first cleanup attempt tried to overwrite and remove it without first restoring write/delete permission, producing two `Access denied` errors and leaving the local file present. The remote trap cleanup had already succeeded.

My corrective command granted full control only to my account, overwrote the 15-byte file with cryptographically random bytes, removed it, and returned `LocalSecretAbsent=true`. A separate SSH check returned `REMOTE_SECRET_ABSENT`.

## 4. Fresh edge-01 identity initially showed never connected

My first screenshot after install showed `app-01` ID `004` active and the newly created `edge-01` ID `005` never connected. Read-only SSH verification then proved `edge-01` agent 4.14.5-1 was enabled and active with an established session from `192.168.90.10` to `192.168.72.2:1514`; TCP 1515 was also reachable. UniFi showed the DMZ-to-Wazuh allow policy enabled with the exact internal destination and port group.

A refreshed dashboard screenshot showed both identities active on `node01`, so no corrective change was required. This was the normal delay between creating the manager identity and the endpoint's first successful check-in. The full record is in [Wazuh Endpoint Re-enrollment - 2026-07-13](Change%20Records/Wazuh%20Endpoint%20Re-enrollment%20-%202026-07-13.md).
