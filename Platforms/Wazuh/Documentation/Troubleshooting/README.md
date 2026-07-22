# Wazuh Troubleshooting

**Created:** 2026-07-13  
**Last updated:** 2026-07-22

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-incorrect-and-stale-endpoint-identities"></a>[1](Incorrect%20and%20stale%20endpoint%20identities%20-%202026-07-13.md) | 2026-07-13 | `app-01` was using the old `wp-01` identity and both existing agents targeted retired manager address `192.168.70.20` | I stopped/disabled `app-01` and `edge-01`, repointed both to `192.168.72.2`, cleared stale keys, and removed manager IDs 002/003 | Resolved; fresh IDs 004/005 active |
| <a id="2-post-purge-process-check-self-match"></a>[2](Post-purge%20process-check%20self-match%20-%202026-07-13.md) | 2026-07-13 | The inline post-purge process assertion returned exit 33 after matching the purge command's own `/var/ossec` and `wazuh-agent` arguments | I re-ran verification after the command exited, using exact daemon names instead of argument substring matching | Resolved; no Wazuh processes present |
| <a id="3-fresh-edge-01-identity-initially-showed-never-connected"></a>[3](Fresh%20edge-01%20identity%20initially%20showed%20never%20connected%20-%202026-07-13.md) | 2026-07-13 | The first post-install screenshot showed fresh `edge-01` ID `005` as never connected | Endpoint checks found an active service and an established TCP 1514 session; a refreshed dashboard capture showed both IDs `004` and `005` active | Resolved; transient first-check-in delay |

