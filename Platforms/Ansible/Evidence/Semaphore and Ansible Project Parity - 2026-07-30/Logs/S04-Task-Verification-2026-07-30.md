# S04 Task Verification

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Captured:** 2026-07-30 09:51 through 09:53 UTC  
**Target:** Semaphore projects 2 & 3  
**Mechanism:** authenticated `POST /api/project/{project_id}/tasks` through SSH Manager  
**Shell & working directory:** POSIX `sh`; `/home/ansible`

I didn't retain the exact JSON request bodies, raw API responses, complete task output, or separate API verification requests. The two sections below are the observed failure lines & final recap I kept; they aren't complete API transcripts.

## Monitoring-Exporters Task 16

I launched the initial node_exporter dry-run template. Semaphore reached all 9 hosts with `unreachable=0`; the project repository, inventory, environment, & SSH credential worked. The task then exited 2 because Ansible check mode didn't create the predicted staging archive & skipped live verification.

```text
fatal: [docker-main]: FAILED! => Source '/tmp/node_exporter-1.9.0.linux-amd64.tar.gz' does not exist
fatal: [splunk-siem]: FAILED! => Source '/tmp/node_exporter-1.9.0.linux-amd64.tar.gz' does not exist
fatal: [kasm-01]: FAILED! => Source '/tmp/node_exporter-1.9.0.linux-amd64.tar.gz' does not exist
docker-network reports node_exporter unknown, expected 1.9.0.
docker-blue reports node_exporter unknown, expected 1.9.0.
media-01 reports node_exporter unknown, expected 1.9.0.
alpha-prod-01 reports node_exporter unknown, expected 1.9.0.
ansible-01 reports node_exporter unknown, expected 1.9.0.
monitor-01 reports node_exporter unknown, expected 1.9.0.
Failed to run task: exit status 2
```

I removed both monitoring dry-run templates. Deleting the failed template removed task 16 from Semaphore's task table, so this record retains the observed failure.

## Fleet-Updates Task 17

I launched `OS Update: Whole Fleet (dry run)`. The complete recap was:

```text
alpha-prod-01 : ok=6 changed=0 unreachable=0 failed=0 skipped=14
ansible-01    : ok=7 changed=0 unreachable=0 failed=0 skipped=13
app-01        : ok=6 changed=0 unreachable=0 failed=0 skipped=14
docker-blue   : ok=6 changed=0 unreachable=0 failed=0 skipped=14
docker-main   : ok=6 changed=0 unreachable=0 failed=0 skipped=14
docker-network: ok=6 changed=0 unreachable=0 failed=0 skipped=14
edge-01       : ok=6 changed=0 unreachable=0 failed=0 skipped=14
media-01      : ok=6 changed=0 unreachable=0 failed=0 skipped=14
monitor-01    : ok=6 changed=0 unreachable=0 failed=0 skipped=14
security-01   : ok=6 changed=1 unreachable=0 failed=0 skipped=14
splunk-siem   : ok=6 changed=1 unreachable=0 failed=0 skipped=14
status=success
```

The two `changed=1` results are check-mode predictions. I ran no live package task.
