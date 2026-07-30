# Monitoring Exporter Check Mode Cannot Complete

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Investigated:** 2026-07-30  
**Status:** Resolved

## Symptom

Semaphore task 16 launched `node-exporter.yml --check` from the new `Monitoring-Exporters` project. It reached all 9 inventory hosts with `unreachable=0`, then exited with status `error`.

The binary-managed hosts reported:

```text
Source '/tmp/node_exporter-1.9.0.linux-amd64.tar.gz' does not exist
```

The package-managed hosts later reported:

```text
reports node_exporter unknown, expected 1.9.0
```

## Failed Attempt

I exposed whole-fleet dry-run templates for node_exporter & cAdvisor because the direct runbook already listed `--check` as a preview. The node_exporter task failed even though every exporter was already installed.

## Hypotheses

- Semaphore may have loaded the wrong repository, inventory, environment, or SSH credential.
- Ansible check mode may have skipped a prerequisite that the playbook's later verification expected.
- One or more hosts may have had a broken exporter before the task started.

## Tests

- All 9 hosts completed SSH setup with `unreachable=0`, so the new Semaphore credential & inventory worked.
- Semaphore loaded `/home/ansible/monitoring-exporters/playbooks/node-exporter.yml`, so the repository path worked.
- `get_url` reported the predicted download in check mode but didn't create the archive.
- `unarchive` & `copy` then read the nonexistent staging path on `docker-main`, `splunk-siem`, & `kasm-01`.
- Ansible skipped the `uri` & shell verification modules on the package-managed hosts, leaving `reported_version` at `unknown`.

## Root Cause

These playbooks combine file creation with post-change live verification. Ansible check mode predicts the download & install steps without creating their intermediate files, then skips modules that would probe the running exporters. The resulting error is a limit of the playbook's check-mode path, not a Semaphore repository, inventory, environment, or credential failure.

## Corrective Action

I removed the 2 monitoring dry-run templates. `Monitoring-Exporters` now exposes whole-scope & single-host live reconciliation for node_exporter & cAdvisor. The command-line `--check` example remains documented as a preview of package decisions, not a pass/fail gate.

## Verification

The final manifest reconciliation reported 3 projects & 0 actions. `Monitoring-Exporters` holds 4 templates across 3 views, its project validator passes with 9 node_exporter & 8 cAdvisor hosts, & SQLite integrity returns `ok`.
