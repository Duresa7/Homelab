# Grafana SQLite Locks Under Its Own Housekeeping

**Created:** 2026-07-26  
**Last updated:** 2026-07-26

**Issue date:** 2026-07-26  
**Status:** Mitigated, verification pending 2026-07-27  
**Affected systems:** `security-01`, Grafana 12.4.1

I moved Grafana to `monitor-01` with a fresh database later on 2026-07-26 and deleted the affected database from `security-01`. `GF_DATABASE_WAL=true` remains in the versioned Compose file. The 2026-07-27 verification now runs against Grafana 13.1.1 on `monitor-01`; it cannot prove the deleted database was repaired, but it can prove the mitigation remains clean on the replacement.

## Symptom

Grafana logged 25 `level=error` lines in 10 hours, every one of them ending in `database is locked`. It kept happening with nobody using Grafana, so it isn't load.

The failures are spread across unrelated background jobs, which is the tell:

| Count | Job |
|---|---|
| 6 | `failed to walk provisioned dashboards` |
| 4 | `Failed to update alert rules` |
| 4 | `cleaning up inactive secure values` |
| 1 each | remote-cache garbage collect, SSO settings fetch, expired auth token cleanup, old login attempt cleanup, anonymous device cleanup, expired snapshot deletion, Alertmanager org sync, admin config sync, plus two request-level errors downstream of the above |

Nothing user-visible broke. The dashboard renders, queries run, and a skipped provisioning pass gets picked up by the next one 30 seconds later.

## How I Nearly Missed It

I reported "zero Grafana errors" earlier the same day and it was wrong. The command was:

```bash
sudo docker logs grafana 2>&1 | grep -c "level=error"
```

`sudo` needs a password on this host and failed. Because `2>&1` was on the `docker logs` side of the pipe, sudo's own complaint went into `grep` instead of to the terminal, matched nothing, and printed `0`. A clean zero from a command that never ran.

`<YOUR_ADMIN_USERNAME>` is in the `docker` group, so `sudo` was never needed here at all. Dropping it returned the real count. Worth remembering: `2>&1 | grep -c` converts a failed command into a confident zero.

## Root Cause

SQLite in its default rollback-journal mode allows one writer, and a reader blocks that writer. Grafana runs a spread of periodic background jobs on independent timers, and enough of them touch the database concurrently that they collide on their own, without a single user logged in. When a job waits past the retry budget it gives up and logs `[sqlstore.max-retries-reached] retry 1: database is locked`.

This is not a symptom of the fleet metrics work. The bursts predate it and continued after it, most recently at `15:01:33Z` while nothing was being changed.

## Mitigation

Write-ahead logging, added to the Grafana service in [docker-compose.yml](../../Configuration/docker-compose.yml):

```yaml
      - GF_DATABASE_WAL=true
```

In WAL mode a reader no longer blocks the writer, so the housekeeping jobs stop queueing behind each other. It needs a container recreate, not a restart, because it is an environment variable.

Confirmed active by the files SQLite only creates in WAL mode:

```
grafana.db       3665920
grafana.db-shm     32768
grafana.db-wal     94792
```

Before the change there was no `-wal` file. `api/health` reports `"database": "ok"`, the provisioned dashboard came back at version 8 with all 12 rows, and 44 Prometheus targets stayed up through the recreate.

## Verification Still Owed

**The error count proves nothing yet.** The recreate reset the container log, so the current zero covers about one minute of runtime, and the original bursts were hours apart. The honest test is the same count over a full day:

```bash
docker logs --since 24h grafana 2>&1 | grep -c "level=error"
```

Baseline to beat: 25 in 10 hours. Run it on `monitor-01` on 2026-07-27. If it is at or near zero, this is closed. If it is not, the diagnosis was wrong and the next step is an external database rather than more tuning.

## Why Not Postgres

Considered and rejected for now. The contention is Grafana's own housekeeping on a single-user install, which is exactly what WAL addresses, and an external database would add a container, a volume, a backup job and a startup dependency to the one service you look at when everything else is broken. Right now Grafana's database is a file on the same VM as Grafana, so if that VM is up, monitoring is up.

Postgres becomes correct on any of three triggers: a second Grafana instance for high availability, which SQLite cannot support at all because it is a local file; hundreds of alert rules evaluating on tight intervals, which is a genuine SQLite bottleneck and nothing like homelab scale; or these errors surviving WAL.

## Consequence For Alerting

Worth knowing before the alerting work starts: `Failed to update alert rules` was one of the failing jobs. Rules are stored in this database, so writing alerting on top of a store that intermittently rejects writes is a good way to end up with a rule that silently does not exist. Confirm the 24-hour count is clean first.
