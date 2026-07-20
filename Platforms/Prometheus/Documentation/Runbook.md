# Prometheus Runbook

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

## Health Check

Connect to `security_01` through SSH Manager. Prometheus is healthy when the container is running, readiness succeeds, the configuration passes `promtool`, and the retained target assertion exits zero:

```bash
sudo docker ps --filter name=prometheus
curl -fsS http://127.0.0.1:9090/-/ready
sudo docker exec prometheus promtool check config /etc/prometheus/prometheus.yml
curl -fsS http://127.0.0.1:9090/api/v1/targets | python3 assert_targets.py
```

The versioned assertion is [assert_targets.py](../Tests/assert_targets.py). Upload it temporarily to `security-01` before the final command and remove the remote copy afterward.

## Change the Target Set

1. Edit [Configuration/prometheus.yml](../Configuration/prometheus.yml) first.
2. Upload it to a candidate path under `/home/<YOUR_ADMIN_USERNAME>/monitoring/`.
3. Copy the candidate into the container and run `promtool check config` against it.
4. Create a dated backup of `/home/<YOUR_ADMIN_USERNAME>/monitoring/prometheus.yml`.
5. Update the live host file.
6. Restart the `prometheus` container. The configuration is a single-file bind mount; replacing the host path requires a restart to bind the new inode.
7. Wait at least one 15-second scrape interval, run the target assertion, and remove candidate files.

Do not treat a successful file copy or HUP signal as proof of reload; verify the target API.

## Rollback

Restore the latest validated host-side backup to `/home/<YOUR_ADMIN_USERNAME>/monitoring/prometheus.yml`, restart the container, check readiness and `promtool`, then verify the intended target set. The 2026-07-13 rollback file is documented in the associated [change record](Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md#rollback-points).

## User Endpoints

- Prometheus: `http://192.168.72.2:9090/`
- Grafana: `http://192.168.72.2:3000/`
- Node metrics are backend endpoints and should be queried through Prometheus except during diagnostics.
