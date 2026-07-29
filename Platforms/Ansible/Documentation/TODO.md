# Ansible TODO

**Created:** 2026-07-14  
**Last updated:** 2026-07-29

## Open Items

- [ ] Reboot `security-01` in a maintenance window to clear the `libc6` reboot requirement, then verify `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard`, & Docker.
- [ ] Reboot `splunk-siem` in a maintenance window to load kernel `6.12.0-211.39.1.el10_2.x86_64`, then verify `Splunkd.service`, `sc4s.service`, & the SC4S container.

Future controller runtime, Semaphore, SSH identity, or fleet-update tasks start here before I move them into an active change record.
