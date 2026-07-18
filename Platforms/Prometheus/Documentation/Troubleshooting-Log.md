# Prometheus Troubleshooting Log

**Created:** 2026-07-13  
**Last updated:** 2026-07-13

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| 1 | 2026-07-13 | A validated host-side configuration replacement and SIGHUP left the running container on the old target set | Restarted the Prometheus container so its single-file bind mount attached to the replacement inode; all seven intended targets then reported `UP` | Resolved |

## 1. Single-file bind mount retained the old inode

The live Prometheus configuration is a single host file bind-mounted into the container. The candidate configuration passed `promtool`, replaced the host path, and Prometheus accepted a HUP signal, but the target API still returned the old jobs. Replacing the path had created a new inode while the existing container mount remained attached to the former inode.

A controlled `docker restart prometheus` rebound `/etc/prometheus/prometheus.yml` to the validated host file. The service returned ready, `promtool` passed inside the restarted container, and the automated target assertion found exactly the seven expected jobs, all `UP`. The temporary container validation file initially required root removal because the container normally runs unprivileged; it was removed with `docker exec --user 0`.

Evidence is retained in [S03-Prometheus-Target-Reconciliation-2026-07-13.md](../Evidence/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13/Logs/S03-Prometheus-Target-Reconciliation-2026-07-13.md).
