# Semaphore & Ansible Project Parity Evidence

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

| Step | Evidence | What it proves |
|---|---|---|
| 1 | [Initial audit](Logs/S01-Initial-Audit-2026-07-30.md) | 3 valid Ansible projects existed while Semaphore held only `Server-SSH`; the exact initial SQLite query wasn't retained. |
| 2 | [Backup & reconciler](Logs/S02-Backup-and-Reconciler-2026-07-30.md) | The recovery set was created & the initial 4-test reconciler run passed; the full creation transcript wasn't retained. |
| 3 | [Live reconciliation](Logs/S03-Live-Reconciliation-2026-07-30.md) | The exact preview & retained apply observation record the missing project objects plus stale managed state. |
| 4 | [Task verification](Logs/S04-Task-Verification-2026-07-30.md) | Fleet check mode passed on 11 hosts; the retained monitoring failure lines isolate the playbook limitation. |
| 5 | [Final verification](Logs/S05-Final-Verification-2026-07-30.md) | Exact commands prove 3 projects, 23 templates, 0 reconciler actions, HTTP `200`, SQLite integrity `ok`, 0 active tokens, & valid backup checksums. |
| 6 | [Repository validation](Logs/S06-Repository-Validation-2026-07-30.md) | 8 unit tests, 3 project validators, Python compilation, 1,175 dashboard checks, & `git diff --check` passed. |
