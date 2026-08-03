# Wazuh Troubleshooting

**Created:** 2026-07-13  
**Last updated:** 2026-08-03

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-incorrect-and-stale-endpoint-identities"></a>[1](Incorrect%20and%20stale%20endpoint%20identities%20-%202026-07-13.md) | 2026-07-13 | `app-01` was using the old `wp-01` identity and both existing agents targeted retired manager address `192.168.70.20` | I stopped/disabled `app-01` and `edge-01`, repointed both to `192.168.72.2`, cleared stale keys, and removed manager IDs 002/003 | Resolved; fresh IDs 004/005 active |
| <a id="2-post-purge-process-check-self-match"></a>[2](Post-purge%20process-check%20self-match%20-%202026-07-13.md) | 2026-07-13 | The inline post-purge process assertion returned exit 33 after matching the purge command's own `/var/ossec` and `wazuh-agent` arguments | I re-ran verification after the command exited, using exact daemon names instead of argument substring matching | Resolved; no Wazuh processes present |
| <a id="3-fresh-edge-01-identity-initially-showed-never-connected"></a>[3](Fresh%20edge-01%20identity%20initially%20showed%20never%20connected%20-%202026-07-13.md) | 2026-07-13; recurred 2026-08-03 | A fresh identity briefly showed never connected after enrollment | Endpoint checks found the service active; the session and manager state converged without repair | Resolved; transient first-check-in delay |
| <a id="4-package-hold-task-failed-before-wazuh-agent-installation"></a>[4](Package%20hold%20task%20failed%20before%20Wazuh%20agent%20installation%20-%202026-08-03.md) | 2026-08-03 | The new fleet play tried to clear a package hold before dpkg knew the package | I removed the unnecessary pre-install selection task and kept the post-install hold | Resolved; four installs and zero-change rerun passed |
| <a id="5-immediate-service-fact-assertion-raced-wazuh-agent-startup"></a>[5](Immediate%20service%20fact%20assertion%20raced%20Wazuh%20agent%20startup%20-%202026-08-03.md) | 2026-08-03 | The first three new agents had keys & TCP sessions, but an immediate `service_facts` assertion reported the units stopped | I added a bounded `systemctl is-active` poll before the final assertion | Resolved; all five Proxmox first starts & zero-change reruns passed |
