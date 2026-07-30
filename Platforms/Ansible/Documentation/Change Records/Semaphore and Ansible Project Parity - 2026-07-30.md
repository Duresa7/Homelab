# Semaphore & Ansible Project Parity

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Implementation date:** 2026-07-30  
**Status:** Complete  
**Primary owner:** `Platforms/Ansible`  
**Affected systems:** `ansible-01`; Semaphore 2.18.27; `ssh-key-automation`; `fleet-updates`; `monitoring-exporters`

## Scope

I reconciled Semaphore with all three Ansible projects deployed on `ansible-01`. Semaphore now exposes 23 templates from the versioned project manifests: 13 for SSH identities, 6 for fleet updates, & 4 for monitoring exporters.

I launched no live package, Compose, node_exporter, or cAdvisor change. One Fleet-Updates task ran under Ansible check mode. A monitoring check-mode attempt reached all 9 hosts but exposed a playbook limitation, so I removed the two monitoring dry-run templates instead of leaving buttons that always report an error.

## Starting State

- `/home/ansible` held three valid projects: `ssh-key-automation`, `fleet-updates`, & `monitoring-exporters`.
- Semaphore held only `Server-SSH`, with 13 templates, 6 views, one repository, one inventory, one locale environment, & one SSH credential.
- The sixth `Server-SSH` view was an empty `Termix` view left after the 2026-07-28 decommission.
- `fleet-updates` already had a six-template manifest. `monitoring-exporters` had two playbooks but no Semaphore manifest.
- SQLite integrity returned `ok`; Semaphore 2.18.27 was enabled, active, & returning HTTP `200`.

## Decisions

- I kept each Ansible project separate in Semaphore. The inventories & target boundaries differ, so one project would hide the same separation the repository enforces.
- I used Semaphore's authenticated API rather than editing `/root/database.sqlite` while the service was running.
- I gave each new project its own `ansible-key` record because Semaphore credentials are project-scoped. Each record contains the existing `/home/ansible/.ssh/id_ed25519` key; no private key or API token entered this repository.
- I left schedules empty. I wanted parity with available Ansible work, not a new unattended execution policy.
- I removed monitoring dry-run templates after task 16 proved that Ansible check mode can't complete those playbooks. The direct command remains a preview of predicted changes, but it isn't a health check.

## Step 1: Audit Ansible & Semaphore

I validated all three deployed projects & read secret-safe Semaphore metadata from the live SQLite database. The validators reported 14 SSH targets & 13 templates, 11 OS hosts & 22 Compose projects, 9 node_exporter hosts, & 8 cAdvisor hosts. Semaphore had one project.

The validator transcript & retained database observation are in [S01 Initial Audit](../../Evidence/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30/Logs/S01-Initial-Audit-2026-07-30.md). I didn't retain the exact initial SQLite query; Step 5 has the complete final query.

## Step 2: Back Up & Build the Reconciler

I created `/root/semaphore-backups/ansible-parity-2026-07-30` with mode `0700`. It holds an online SQLite backup, `/root/config.json`, the `Server-SSH` project export, & `SHA256SUMS`; every retained file is mode `0600`, & the backup database returned `integrity=ok`.

I added `monitoring-exporters/semaphore/task-templates.yml` & `/opt/homelab/ansible-tools/reconcile_semaphore.py`. The reconciler reads all three manifests, compares every managed template field, reports unmanaged project objects, & writes only with `--apply`. It retains absent templates & views unless I add `--prune`; project-scoped SSH credentials come from a supplied private-key path. Eight unit tests cover duplicate templates, locale serialization, template ID mapping, API readback normalization, complete template drift detection, opt-in pruning, duplicate-object detection, & unmanaged projects.

The retained creation command & historical four-test run are in [S02 Backup & Reconciler](../../Evidence/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30/Logs/S02-Backup-and-Reconciler-2026-07-30.md). The complete final checksum run is in Step 5.

## Step 3: Reconcile the Live Projects

The first read-only API pass found 7 intended actions: update the stale onboarding survey, reorder its view, remove `Termix`, create `Fleet-Updates`, & create `Monitoring-Exporters`. The applied run created both projects, their repositories, inventories, locale environments, project-scoped SSH credentials, views, & templates. It also corrected `Server-SSH`.

I created every API token with a 10- or 20-minute TTL, stored it in a root-only temporary file, expired it through the API, & removed the file. The final database query found 0 active tokens.

The exact preview command & retained apply observation are in [S03 Live Reconciliation](../../Evidence/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30/Logs/S03-Live-Reconciliation-2026-07-30.md). I didn't retain the exact initial apply command; Step 5 contains a complete read-only API pass against the resulting state.

## Step 4: Exercise the New Projects

Fleet-Updates task 17 ran `OS Update: Whole Fleet (dry run)` from the new Semaphore project. All 11 hosts returned `unreachable=0` & `failed=0`; nine reported `changed=0`, while `security-01` & `splunk-siem` predicted one check-mode change each. Check mode wrote no package change.

Monitoring-Exporters task 16 reached all 9 hosts with `unreachable=0`, which proved the new repository, inventory, locale, & SSH credential. It then failed inside `node-exporter.yml`: `get_url` predicted an archive download without creating the file, `unarchive` & `copy` couldn't read it, & skipped verification commands produced `version=unknown`. I removed both monitoring dry-run templates & documented the cause in [Monitoring exporter check mode cannot complete](../Troubleshooting/Monitoring%20exporter%20check%20mode%20cannot%20complete%20-%202026-07-30.md). Deleting the failed template also removed task 16 from Semaphore's task table, so the retained evidence record is the durable account of that failed attempt.

The retained failure lines & complete fleet recap are in [S04 Task Verification](../../Evidence/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30/Logs/S04-Task-Verification-2026-07-30.md). I didn't retain the exact API request bodies or complete task output, so the evidence states that boundary.

## Step 5: Verify the Final State

The reviewed reconciler pass compared all managed template fields & reported `3 projects, 0 actions`. SQLite integrity returned `ok`; Semaphore remained enabled & active; its direct UI returned HTTP `200`; all 3 project validators passed; all 3 projects held one repository, inventory, environment, & SSH credential; schedules remained at `0`.

I didn't launch the 4 retained Monitoring-Exporters templates because they perform live reconciliation. Task 16 proved the project could load its repository, inventory, environment, SSH credential, & node_exporter playbook across 9 hosts. The final read-only pass proved all 4 retained template definitions match the manifest; it didn't execute cAdvisor or a single-host survey.

| Project | Templates | Views | Repository | Inventory | Environment |
|---|---:|---:|---:|---:|---:|
| `Server-SSH` | 13 | 5 | 1 | 1 | 1 |
| `Fleet-Updates` | 6 | 3 | 1 | 1 | 1 |
| `Monitoring-Exporters` | 4 | 3 | 1 | 1 | 1 |
| **Total** | **23** | **11** | **3** | **3** | **3** |

The exact token, reconciliation, database, validator, runtime, cleanup, & checksum commands are in [S05 Final Verification](../../Evidence/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30/Logs/S05-Final-Verification-2026-07-30.md).

## Step 6: Review & Validate the Repository

The final review found 3 reconciler gaps. Template comparison omitted 7 payload fields, absent templates plus views were deleted by default, & extra or duplicate objects could hide behind matching names. I expanded comparison to every managed template field, made pruning opt-in with `--prune`, switched unmanaged detection to object IDs, included the top-level project collection, & added 4 regression tests.

Eight unit tests, Python compilation, all 3 project validators, 1,175 Mission Control checks, & `git diff --check` passed. I first ran `node harness.js` from the wrong directory; it returned `MODULE_NOT_FOUND`, then passed from `Mission Control`. The exact failure & corrected validation are in [S06 Repository Validation](../../Evidence/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30/Logs/S06-Repository-Validation-2026-07-30.md).

## Rollback

The root-only recovery set is `/root/semaphore-backups/ansible-parity-2026-07-30`. To restore the exact pre-change state, I stop `semaphore.service`, restore `database.sqlite` & `config.json`, verify `SHA256SUMS` plus SQLite integrity, start Semaphore, & confirm HTTP `200`.

The source change is additive except for the corrected `Server-SSH` survey & removed empty `Termix` view. Reverting the repository commit removes the new manifest & reconciler but doesn't change the live database by itself.

## Remaining Work

No Semaphore parity work remains. The Ansible TODO still carries the separate first-real-reboot observation from the 2026-07-29 reconnect fix.
