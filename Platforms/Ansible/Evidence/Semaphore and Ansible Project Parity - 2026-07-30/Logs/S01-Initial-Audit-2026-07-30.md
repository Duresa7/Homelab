# S01 Initial Audit

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Captured:** 2026-07-30 09:39 UTC  
**Target:** `ansible-01`  
**Mechanism:** SSH Manager  
**Shell:** POSIX `sh`  
**Working directories:** the three project paths named in the command

## Command

```bash
for project in \
  /home/ansible/ssh-key-automation \
  /home/ansible/fleet-updates \
  /home/ansible/monitoring-exporters
do
  cd "$project"
  python3 tests/validate_project.py
done
```

## Observed Result

```text
ssh-key-automation: Validation passed: 3 identities, 14 supported hosts, 0 unknown hosts, 13 Semaphore templates.
fleet-updates: Validation passed: 11 OS-update hosts, 6 compose hosts, 22 projects.
monitoring-exporters: Validation passed: 9 node_exporter hosts, 8 cAdvisor hosts.
```

**Standard error:** empty  
**Exit code:** `0`

## Database Observation

The secret-safe SQLite query returned one project. I didn't retain the exact query, complete stdout/stderr boundary, or a separate follow-up command, so this block is an observation summary rather than a terminal transcript:

```text
Server-SSH
repositories=1
inventories=1
environments=1
views=6
templates=13
access_keys=1
schedules=0
integrity=ok
```

The views were `All`, `Mac`, `Ansible Control`, `Jedi PC`, `Termix`, & `Onboarding`. `Termix` held no template.

The complete 2026-07-30 final database query is retained in [S05 Final Verification](S05-Final-Verification-2026-07-30.md).
