# S03 Live Reconciliation

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Captured:** 2026-07-30 09:49 UTC  
**Target:** `ansible-01` Semaphore API on `127.0.0.1:3000`  
**Mechanism:** SSH Manager running `/opt/homelab/ansible-tools/reconcile_semaphore.py`  
**Shell:** POSIX `sh`  
**Working directory:** `/home/ansible`

## Preview Command

```bash
python3 /opt/homelab/ansible-tools/reconcile_semaphore.py \
  --token-file /root/semaphore-backups/ansible-parity-2026-07-30/api-token.tmp \
  /home/ansible/ssh-key-automation/semaphore/task-templates.yml \
  /home/ansible/fleet-updates/semaphore/task-templates.yml \
  /home/ansible/monitoring-exporters/semaphore/task-templates.yml
```

## Preview Result

```text
would reorder view Onboarding
would update template Onboard — New SSH Device
would delete view Termix
would create project Fleet-Updates
would populate project Fleet-Updates with 6 templates
would create project Monitoring-Exporters
would populate project Monitoring-Exporters with 6 templates
Semaphore reconciliation detected: 3 projects, 7 actions.
```

**Standard error:** empty  
**Exit code:** `0`

The 09:49 reconciler version pruned absent templates & views by default. The reviewed version now requires `--prune`.

## Apply Observation

I didn't retain the exact apply command, its complete stdout/stderr, or a separate API readback command. This is the action summary I kept, not a reconstructed transcript:

```text
reorder view Onboarding
update onboarding template
delete view Termix
create project Fleet-Updates
create credential ansible-key
create repository fleet-updates
create inventory homelab-fleet-update-hosts
create environment C UTF-8
create view OS Updates
create view Docker Compose
create 6 Fleet-Updates templates
create project Monitoring-Exporters
create credential ansible-key
create repository monitoring-exporters
create inventory homelab-monitoring-exporter-hosts
create environment C UTF-8
create view Node Exporter
create view cAdvisor
create 6 initial Monitoring-Exporters templates
Semaphore reconciliation applied: 3 projects, 29 actions.
Temporary API token expired.
```

After the check-mode test documented in S04, I removed the two monitoring dry-run templates. I didn't retain the exact command or complete output from that second applied pass; the working note recorded 2 deletions.

The complete reviewed reconciler command & final readback are retained in [S05 Final Verification](S05-Final-Verification-2026-07-30.md).
