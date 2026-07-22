# Post-purge process-check self-match

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

My package purge and residual-data removal reported `PACKAGE_ABSENT`, `UNIT_ABSENT`, and `OSSEC_PATH_ABSENT` on both endpoints. Its final `pgrep -af '/var/ossec|wazuh-agent'` check still returned exit 33 because it matched the running shell command text itself.

After that shell exited, I ran a detached check against the exact Wazuh and OSSEC daemon process names. Both hosts returned exit 0 with package, unit, `/var/ossec`, and all named processes absent. This was a verification-command defect, not a failed removal. The full record is in [Wazuh Endpoint Agent Removal - 2026-07-13](../Change%20Records/Wazuh%20Endpoint%20Agent%20Removal%20-%202026-07-13.md).
