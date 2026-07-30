# S02 Backup & Reconciler

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Captured:** 2026-07-30 09:45 UTC  
**Target:** `ansible-01` & local workspace  
**Mechanism:** SSH Manager & local Python unit tests  
**Remote shell & working directory:** POSIX `sh`; `/home/ansible` with absolute backup paths  
**Local shell & working directory:** PowerShell; `D:\Documents\Homelab`

## Backup Command

```bash
install -d -m 0700 /root/semaphore-backups/ansible-parity-2026-07-30
python3 /opt/homelab/ansible-tools/backup_semaphore_sqlite.py \
  /root/database.sqlite \
  /root/semaphore-backups/ansible-parity-2026-07-30/database.sqlite
install -m 0600 /root/config.json \
  /root/semaphore-backups/ansible-parity-2026-07-30/config.json
semaphore --config /root/config.json projects export \
  --project-id 1 \
  --file /root/semaphore-backups/ansible-parity-2026-07-30/server-ssh.json
```

## Retained Backup Observation

The exact creation command is retained above. I didn't retain its complete stdout/stderr boundary or the immediate follow-up commands, so this block is a working observation rather than a terminal transcript:

```text
backup-created=/root/semaphore-backups/ansible-parity-2026-07-30/database.sqlite
sqlite-integrity=ok
database.sqlite mode=600 bytes=659456
config.json mode=600 bytes=395
server-ssh.json mode=600 bytes=11378
SHA256SUMS mode=600 bytes=242
```

The complete checksum verification is retained in [S05 Final Verification](S05-Final-Verification-2026-07-30.md).

## Local Unit Test Command

```powershell
python -m unittest Platforms.Ansible.Tests.test_reconcile_semaphore
```

## Unit Test Result

```text
....
Ran 4 tests in 0.055s
OK
```

**Standard error:** empty  
**Exit code:** `0`
