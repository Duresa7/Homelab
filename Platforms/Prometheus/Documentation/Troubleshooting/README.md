# Prometheus Troubleshooting

**Created:** 2026-07-13  
**Last updated:** 2026-08-04

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-single-file-bind-mount-retained-the-old-inode"></a>[1](Single-File%20Bind%20Mount%20Retained%20the%20Old%20Inode%20-%202026-07-13.md) | 2026-07-13; recurred 2026-07-28 | A host-side path replacement and SIGHUP left the running container on the old target set | I first restarted the container in 2026-07; on recurrence I wrote the validated host file through the existing mounted inode, matched both SHA-256 digests, & confirmed 20 active probes with `probe_success=1` | Resolved |
| <a id="2-grafana-bootstrap-administrator-credential"></a>[2](Grafana%20Bootstrap%20Administrator%20Credential%20-%202026-07-22.md) | 2026-07-22 | Grafana's one-time bootstrap administrator value remained in the live Compose file | I removed the variable, recreated Grafana, rotated the credential, & verified health and authenticated access | Resolved; [incident](../../../../Security/Incidents/Grafana/Plaintext%20Administrator%20Credential%20-%202026-07-22.md) closed |
| <a id="3-cadvisor-registers-no-containers-under-the-docker-29-overlayfs-driver"></a>[3](cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md) | 2026-07-25 | cAdvisor answered on 9101 and emitted ~600 series on six of seven Docker hosts, all of it the root cgroup, reporting zero named containers | Docker 29's `overlayfs` driver moves layer metadata into containerd, so cAdvisor v0.52.1 can't resolve a read-write layer ID and abandons registration. Fixed on 2026-07-26 by moving to v0.60.5 from `ghcr.io/google/cadvisor`, which handles the containerd snapshotter. I had wrongly concluded v0.52.1 was the newest release, because the three tags I probed were never published | Resolved 2026-07-26 |
| <a id="4-grafana-sqlite-locks-under-its-own-housekeeping"></a>[4](Grafana%20SQLite%20Locks%20Under%20Its%20Own%20Housekeeping%20-%202026-07-26.md) | 2026-07-26 | 25 `database is locked` errors in 10 hours across unrelated Grafana background jobs, with nobody using Grafana | SQLite's default journal mode lets a reader block the writer, and Grafana's own periodic jobs collide on their own. `GF_DATABASE_WAL=true` fixed it on Grafana 12.4.1. On 13.1.1 the environment still contains the setting, but the 2026-08-04 header read `1 1` and only `grafana.db` existed, proving rollback-journal mode. A `sudo` failure piped into `grep -c` had earlier reported this as zero errors | Monitoring; removal of the inert setting remains open for the next recreate |
