# Grafana SQLite Locks Under Its Own Housekeeping

**Created:** 2026-07-26  
**Last updated:** 2026-08-04

**Issue date:** 2026-07-26  
**Status:** Monitoring. The 24-hour baseline found one successful retry and no terminal error lines on Grafana 13.1.1  
**Affected systems:** `security-01` Grafana 12.4.1, retired; `monitor-01` Grafana 13.1.1

I moved Grafana to `monitor-01` with a fresh database later on 2026-07-26 and deleted the affected database from `security-01`. `GF_DATABASE_WAL=true` came across in the Compose file but stopped taking effect. See [The Mitigation Did Not Survive the Version Change](#the-mitigation-did-not-survive-the-version-change) for the measured state.

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

`dkadi` is in the `docker` group, so `sudo` was never needed here at all. Dropping it returned the real count. Worth remembering: `2>&1 | grep -c` converts a failed command into a confident zero.

## Root Cause

SQLite in its default rollback-journal mode allows one writer, and a reader blocks that writer. Grafana runs a spread of periodic background jobs on independent timers, and enough of them touch the database concurrently that they collide on their own, without a single user logged in. When a job waits past the retry budget it gives up and logs `[sqlstore.max-retries-reached] retry 1: database is locked`.

This is not a symptom of the fleet metrics work. The bursts predate it and continued after it, most recently at `15:01:33Z` while nothing was being changed.

## Mitigation

Write-ahead logging, added to the Grafana service in [docker-compose.yml](../../Configuration/docker-compose.yml):

```yaml
      - GF_DATABASE_WAL=true
```

In WAL mode a reader no longer blocks the writer, so the housekeeping jobs stop queueing behind each other. It needs a container recreate, not a restart, because it is an environment variable.

On Grafana 12.4.1 this worked. SQLite created the two files it only creates in WAL mode:

```
grafana.db       3665920
grafana.db-shm     32768
grafana.db-wal     94792
```

`api/health` reported `"database": "ok"`, the provisioned dashboard came back at version 8 with all 12 rows, and 44 Prometheus targets stayed up through the recreate.

## The Mitigation Did Not Survive the Version Change

The relocation put Grafana 13.1.1 on `monitor-01`, and the setting stopped doing anything. I found this on 2026-07-26 while reviewing the completed relocation, not from a failure.

Grafana still reads the variable. It logs `Config overridden from Environment variable var="GF_DATABASE_WAL=true"` at container start, and `docker exec grafana env` shows it. The running service also reports this SQLite driver:

```
logger=sqlstore level=info msg="Using SQLite driver" driver=modernc.org/sqlite
```

12.4.1 produced `-wal` & `-shm` files; 13.1.1 doesn't. Three checks on the running container:

- `/var/lib/grafana/` holds `grafana.db` alone. No `-wal`, no `-shm`. SQLite creates both the moment a WAL database is opened, and Grafana holds four descriptors on the file.
- Bytes 18 and 19 of the file header read `1 1`. That's the rollback journal. A WAL database reads `2 2`, & the value is written into the file, so it isn't a timing artifact.
- `SQLITE_BUSY` came back at `19:29:06Z`, sixteen minutes after start: `Database locked, sleeping then retrying ... retry=0 sleep=9.963223ms`.

I did not establish why Grafana reads the variable without changing the database journal mode. The environment value, file header, and sidecar files establish the resulting state without relying on a theory about Grafana's internals.

## Follow-up measurement, 2026-08-04

I repeated the state check inside the running Grafana 13.1.1 container. `GF_DATABASE_WAL` was `true`. SQLite header bytes 18 and 19 were `1 1`, which is rollback-journal mode; WAL mode would read `2 2`. `/var/lib/grafana/` contained `grafana.db` and no `grafana.db-wal` or `grafana.db-shm` sidecar.

Grafana was running and holding the database open, so the missing sidecars were not a clean-shutdown artifact. The setting is present and the database is not in WAL mode. This measurement establishes that the setting has no effect without asserting why.

## 24-Hour Baseline

I captured the 24-hour window on `monitor-01` at 2026-07-27 12:37:59 UTC. Grafana 13.1.1 was running. The original planned command returned zero:

```bash
docker logs --since 24h grafana 2>&1 | grep -c "level=error"
```

That zero isn't the lock count. The one SQLite lock line uses `level=info`, so the exact `level=error` filter misses it:

```text
logger=sqlstore.transactions t=2026-07-26T19:29:06.909342016Z level=info msg="Database locked, sleeping then retrying" error="database is locked (5) (SQLITE_BUSY)" retry=0 sleep=9.963223ms
```

The corrected result is one `database is locked` event, one `SQLITE_BUSY` event, and zero `level=error` lines. Grafana retried after 9.963223 milliseconds. No job exhausted its retry budget.

This measures a fresh database with one dashboard, no alert rules, and one user, against the old 12.4.1 baseline of 25 failed jobs in 10 hours. It does not prove WAL works. The database remains in rollback-journal mode.

## Next Action

I will remove `GF_DATABASE_WAL=true` at the next Grafana recreate because 13.1.1 reads the variable without changing the journal mode. One successful 9.963223-millisecond retry does not justify a manual `PRAGMA journal_mode=WAL` cutover or a PostgreSQL deployment.

I left the running container alone. Recreating it to remove an inactive variable would reset the log for no current service benefit. I will repeat the corrected `database is locked` count after alert rules add database writes.

## Why Not Postgres

Considered and rejected for now. The contention is Grafana's own housekeeping on a single-user install, which is exactly what WAL addresses, and an external database would add a container, a volume, a backup job and a startup dependency to the one service you look at when everything else is broken. Right now Grafana's database is a file on the same VM as Grafana, so if that VM is up, monitoring is up.

Postgres becomes correct on any of three triggers: a second Grafana instance for high availability, which SQLite cannot support at all because it is a local file; hundreds of alert rules evaluating on tight intervals, which is a genuine SQLite bottleneck and nothing like homelab scale; or these errors surviving WAL.

## Consequence For Alerting

Worth knowing before the alerting work starts: `Failed to update alert rules` was one of the failing jobs. Rules are stored in this database, so writing alerting on top of a store that intermittently rejects writes is a good way to end up with a rule that silently does not exist. Confirm the 24-hour count is clean first.
