# Inert Grafana WAL Setting Removal

**Created:** 2026-08-04  
**Last updated:** 2026-08-04

**Change date:** 2026-08-04  
**Scope:** Versioned Grafana Compose configuration only  
**Status:** Repository complete; host rollout pending

## What I changed

I removed only `GF_DATABASE_WAL=true` from the versioned Grafana service environment in `docker-compose.yml`. This is a no-op for database behavior. The running Grafana 13.1.1 database was never in WAL mode: SQLite header bytes 18 and 19 were `1 1`, and only `grafana.db` existed without a `-wal` or `-shm` sidecar.

I did not recreate the Grafana container or connect to `monitor-01`. The running container keeps the environment value until I next recreate it, which is the intended state for this repository-only change.

## What I verified

`git diff --numstat -- Platforms/Prometheus/Configuration/docker-compose.yml` reported `0` added lines and `1` removed line. The full diff showed only the `GF_DATABASE_WAL=true` environment entry leaving the file. None of the five existing image declarations or their tags changed.

Python and PyYAML parsed the resulting file successfully as a mapping with the top-level keys `services` and `volumes`.

`git grep` found no remaining `GF_DATABASE_WAL` reference in versioned configuration or the backlog. The remaining tracked Markdown references are records that preserve the measured state or explain why the running container and repository differ until the next recreate.

The repository-wide publication checks reported 897 tracked files, 488 tracked Markdown files, 1,747 relative file links, zero missing or untracked destinations, zero destinations containing a literal space, and zero tracked files beginning with a byte-order mark.

## What remains open

The host-side removal remains pending until I next recreate Grafana. No recreate is justified solely to remove an environment value that does not change the current journal mode.
