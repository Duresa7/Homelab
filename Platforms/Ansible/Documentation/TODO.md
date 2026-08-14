# Ansible TODO

**Created:** 2026-07-14  
**Last updated:** 2026-08-14

## Open Items

- Register the `ubuntu-dev` SSH identity in `ssh-key-automation`, now that it has replaced `debian-dev` as the machine I develop on. The equivalent item for `debian-dev` closed on its own when I decommissioned that VM on 2026-08-14 without ever writing `identities/debian-dev.yml`; the project never knew that identity existed. I also corrected two defects in `inventory/hosts.yml` that would have made any run fail or skip a node: `edge-01` still carried `192.168.90.10` after it moved to `192.168.30.10` on 2026-08-07, and `green-server` had never been added although it joined the cluster on 2026-07-31. Both are fixed and the file now lists all five nodes.
- Tidy `/etc/pve/priv/authorized_keys`. It holds `jedi-pc`, `mac-air3-dkadi`, and `ansible-control` five times each, one copy per node join, plus an `no comment` Ed25519 entry I have not identified. Nothing is broken by this, but the duplication makes the file hard to audit by eye.
- Watch the first real automatic reboot after the 2026-07-29 fix. I added a wait for the guest's SSH listener to drop before the reconnect, so the boot-ID check can't race the shutdown. The validator, both syntax checks, `--list-tasks`, and a two-host check-mode run all pass, but the reboot block is skipped under `--check` and no guest currently reports `reboot_required=True`, so the new wait itself is unexercised. The reasoning is in [Reboot action did not finish after the guest returned](Troubleshooting/Reboot%20action%20did%20not%20finish%20after%20the%20guest%20returned%20-%202026-07-29.md).

Future controller runtime, Semaphore, SSH identity, or fleet-update tasks start here before I move them into an active change record.

## Completed

- [x] 2026-08-08: Removed four stale `.bak` copies from `wazuh-agent-deployment` on the controller: one `inventory/hosts.yml.bak.20260803_180246` and three `playbooks/deploy.yml.bak.*` from 2026-08-03. A config copy belongs in the repository's `Backups/` folder and not on the host, and the current version of both files is versioned under `Platforms/Wazuh/Source/`, so git already holds the history these copies duplicated. `hosts.yml` and `deploy.yml` are the only files left in those two directories.
- [x] 2026-07-30: [Semaphore & Ansible project parity](Change%20Records/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30.md). I added `Fleet-Updates` & `Monitoring-Exporters`, reconciled all 3 projects from versioned manifests, & verified the final API check at zero actions.
