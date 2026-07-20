# Prometheus

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

Prometheus provides infrastructure metrics for the homelab. The deployed server runs in Docker on `security-01` (`192.168.72.2`) and scrapes the security host, the DMZ edge host, all four Galaxy Proxmox nodes, and the Proxmox API exporter.

**Owner:** Homelab infrastructure monitoring

## Layout

- `Configuration/`: versioned reference configuration matching the live deployment.
- `Documentation/Change Records/`: dated implementation and repair records.
- `Documentation/Runbook.md`: routine health checks, configuration changes, and rollback.
- `Documentation/TODO.md`: current Prometheus backlog.
- `Documentation/Troubleshooting-Log.md`: chronological operational problems and resolutions.
- `Evidence/`: step evidence for bounded monitoring changes.
- `Tests/`: reusable validation scripts for the live target set.

## Deployed Service

| Item | Value |
|---|---|
| Prometheus UI | `http://192.168.72.2:9090/` |
| Live host configuration | `/home/<YOUR_ADMIN_USERNAME>/monitoring/prometheus.yml` on `security-01` |
| Container configuration | `/etc/prometheus/prometheus.yml` |
| Versioned configuration | [prometheus.yml](Configuration/prometheus.yml) |
| Scrape interval | 15 seconds |
| Current targets | `security-01`, `edge-01`, four Galaxy Proxmox nodes, Proxmox API exporter |

In the 2026-07-13 baseline cleanup I installed the three missing Proxmox exporters, removed stale scrape jobs, and confirmed all seven retained jobs `UP`. See [Security Monitoring Baseline Cleanup - 2026-07-13](Documentation/Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md).
