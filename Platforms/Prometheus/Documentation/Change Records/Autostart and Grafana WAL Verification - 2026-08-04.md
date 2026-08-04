# Autostart and Grafana WAL Verification

**Created:** 2026-08-04  
**Last updated:** 2026-08-04

**Change date:** 2026-08-04  
**Scope:** Prometheus boot behavior and Grafana SQLite journal state  
**Status:** Complete

## What I changed

I closed the Prometheus auto-start backlog item after the controlled 2026-08-01 restart supplied the check it was waiting for. I also replaced the assumption that `GF_DATABASE_WAL=true` was inactive with a measured database-state finding. This was a documentation correction. I did not recreate a container, remove the environment variable, or change a live deployment.

## Prometheus auto-start verification

CT 104 `monitor-01` booted at 11:11:33 EDT on 2026-08-01. Prometheus started at 11:11:37 EDT, four seconds after the host, and reported `RestartCount=0`. Grafana started at the same time. Docker was enabled and active, and all seven containers were running with restart policy `unless-stopped`.

The zero restart count is part of the proof: Prometheus entered its running state on the boot path and did not need a later container restart. `blue-server`, which hosts CT 104, reported `pvestatd` entering active at 11:11:21 EDT during the same node restart, twelve seconds before the LXC finished booting. The node and guest clocks independently agree on the restart sequence.

## Grafana WAL measurement

Inside the running Grafana 13.1.1 container on 2026-08-04:

- `GF_DATABASE_WAL` was `true` in the container environment.
- SQLite header bytes 18 and 19 were `1 1`, which is rollback-journal mode. WAL mode would read `2 2`.
- `/var/lib/grafana/` contained `grafana.db` without `grafana.db-wal` or `grafana.db-shm`.

Grafana was running and holding the database open, so the absent sidecars were not the result of a clean shutdown. The environment setting is present and the database is not in WAL mode. I did not establish why the setting has no effect.

## What remains open

Removing `GF_DATABASE_WAL=true` remains open for the next Grafana recreate. This change measured and documented the setting; it did not recreate the container. Alert routing and rules, plus UniFi infrastructure metrics, also remain in the Prometheus backlog.

I used the measurements already taken on 2026-08-04 and made no live-system connection for this documentation change.
