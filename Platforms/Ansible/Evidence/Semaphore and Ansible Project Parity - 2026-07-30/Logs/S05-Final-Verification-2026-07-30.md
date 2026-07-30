# S05 Final Verification

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Captured:** 2026-07-30 10:19 through 10:20 UTC  
**Target:** `ansible-01`  
**Mechanism:** SSH Manager, Semaphore API, & SQLite read-only URI  
**Shell:** POSIX `sh`  
**Working directory:** `/home/ansible` unless the command changes it

## Temporary Token Command

```bash
sudo sh -c 'umask 077; semaphore --config /root/config.json users token create --login dkadi --name ansible-parity-final-2026-07-30 --ttl 15m > /root/semaphore-api-token-final.tmp' && sudo stat -c 'token_file_mode=%a' /root/semaphore-api-token-final.tmp
```

## Temporary Token Result

```text
token_file_mode=600
```

**Standard error:** empty  
**Exit code:** `0`

## Reconciler Command

```bash
sudo python3 /opt/homelab/ansible-tools/reconcile_semaphore.py --token-file /root/semaphore-api-token-final.tmp --expire-token /home/ansible/ssh-key-automation/semaphore/task-templates.yml /home/ansible/fleet-updates/semaphore/task-templates.yml /home/ansible/monitoring-exporters/semaphore/task-templates.yml
```

## Reconciler Result

```text
Semaphore reconciliation detected: 3 projects, 0 actions.
Temporary API token expired.
```

**Standard error:** empty  
**Exit code:** `0`

## Follow-Up Verification Command

```bash
sudo rm -f /root/semaphore-api-token-final.tmp
sudo test ! -e /root/semaphore-api-token-final.tmp && echo token_file_exists=false
semaphore version
systemctl is-active semaphore.service
systemctl is-enabled semaphore.service
curl --silent --output /dev/null --write-out 'http=%{http_code}\n' http://127.0.0.1:3000/
sudo stat -c 'reconciler_mode=%a owner=%U:%G' /opt/homelab/ansible-tools/reconcile_semaphore.py
sudo python3 - <<'PY'
import sqlite3
connection = sqlite3.connect('file:/root/database.sqlite?mode=ro', uri=True)
print(f'integrity={connection.execute("PRAGMA integrity_check").fetchone()[0]}')
query = '''
SELECT p.name,
       (SELECT count(*) FROM project__template t WHERE t.project_id = p.id),
       (SELECT count(*) FROM project__view v WHERE v.project_id = p.id),
       (SELECT count(*) FROM project__repository r WHERE r.project_id = p.id),
       (SELECT count(*) FROM project__inventory i WHERE i.project_id = p.id),
       (SELECT count(*) FROM project__environment e WHERE e.project_id = p.id),
       (SELECT count(*) FROM access_key k WHERE k.project_id = p.id AND k.type <> 'none'),
       (SELECT count(*) FROM project__schedule s WHERE s.project_id = p.id)
FROM project p
ORDER BY p.id
'''
for row in connection.execute(query):
    print(f'{row[0]}: templates={row[1]} views={row[2]} repositories={row[3]} inventories={row[4]} environments={row[5]} credentials={row[6]} schedules={row[7]}')
active_tokens = connection.execute("SELECT count(*) FROM user__token WHERE expired = 0 AND (expires_at IS NULL OR expires_at > datetime('now'))").fetchone()[0]
print(f'active_tokens={active_tokens}')
PY
for project in /home/ansible/ssh-key-automation /home/ansible/fleet-updates /home/ansible/monitoring-exporters; do
  (cd "$project" && python3 tests/validate_project.py) || exit $?
done
sudo sh -c 'cd /root/semaphore-backups/ansible-parity-2026-07-30 && sha256sum -c SHA256SUMS'
date -u '+captured=%Y-%m-%d %H:%M:%S UTC'
```

## Follow-Up Verification Result

```text
token_file_exists=false
2.18.27-240e595-1783925315
active
enabled
http=200
reconciler_mode=755 owner=root:root
integrity=ok
Server-SSH: templates=13 views=5 repositories=1 inventories=1 environments=1 credentials=1 schedules=0
Fleet-Updates: templates=6 views=3 repositories=1 inventories=1 environments=1 credentials=1 schedules=0
Monitoring-Exporters: templates=4 views=3 repositories=1 inventories=1 environments=1 credentials=1 schedules=0
active_tokens=0
Validation passed: 3 identities, 14 supported hosts, 0 unknown hosts, 13 Semaphore templates.
Validation passed: 11 OS-update hosts, 6 compose hosts, 22 projects.
Validation passed: 9 node_exporter hosts, 8 cAdvisor hosts.
database.sqlite: OK
config.json: OK
server-ssh.json: OK
captured=2026-07-30 10:20:06 UTC
```

**Standard error:** empty  
**Exit code:** `0`
