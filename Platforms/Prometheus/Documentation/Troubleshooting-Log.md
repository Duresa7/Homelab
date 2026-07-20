# Prometheus Troubleshooting Log

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

| # | Date | Symptom | Resolution | Status |
|---:|---|---|---|---|
| 1 | 2026-07-13 | A validated host-side configuration replacement and SIGHUP left the running container on the old target set | I restarted the Prometheus container so its single-file bind mount attached to the replacement inode; all seven intended targets then reported `UP` | Resolved |

## 1. Single-File Bind Mount Retained the Old Inode

The live Prometheus configuration is a single host file bind-mounted into the container. My candidate configuration passed `promtool` and replaced the host path, and Prometheus accepted a HUP signal, but the target API still returned the old jobs. Replacing the path had created a new inode while the existing container mount stayed attached to the former inode.

I ran a controlled `docker restart prometheus`, which rebound `/etc/prometheus/prometheus.yml` to the validated host file. The service returned ready, `promtool` passed inside the restarted container, and the automated target assertion found exactly the seven expected jobs, all `UP`. The temporary container validation file needed root removal because the container normally runs unprivileged, so I removed it with `docker exec --user 0`.
