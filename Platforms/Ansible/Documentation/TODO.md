# Ansible TODO

**Created:** 2026-07-14  
**Last updated:** 2026-07-31

## Open Items

- Watch the first real automatic reboot after the 2026-07-29 fix. I added a wait for the guest's SSH listener to drop before the reconnect, so the boot-ID check can't race the shutdown. The validator, both syntax checks, `--list-tasks`, and a two-host check-mode run all pass, but the reboot block is skipped under `--check` and no guest currently reports `reboot_required=True`, so the new wait itself is unexercised. The reasoning is in [Reboot action did not finish after the guest returned](Troubleshooting/Reboot%20action%20did%20not%20finish%20after%20the%20guest%20returned%20-%202026-07-29.md).

Future controller runtime, Semaphore, SSH identity, or fleet-update tasks start here before I move them into an active change record.

## Completed

- [x] 2026-07-30: [Semaphore & Ansible project parity](Change%20Records/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30.md). I added `Fleet-Updates` & `Monitoring-Exporters`, reconciled all 3 projects from versioned manifests, & verified the final API check at zero actions.
