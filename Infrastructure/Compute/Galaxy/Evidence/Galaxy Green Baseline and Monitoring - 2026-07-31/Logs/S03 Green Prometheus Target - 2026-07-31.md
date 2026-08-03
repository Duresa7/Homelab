# S03 Green Prometheus Target

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture time:** 2026-07-31 10:02 to 10:06 EDT  
**Target:** `monitor-01`  
**Mechanism:** SSH Manager, POSIX shell, Docker CLI, Prometheus API

## Candidate and Rollback Checks

I built `/home/dkadi/monitoring/.prometheus.green-node.candidate.yml` from the current live file and inserted Green after Red. I validated it before the live write:

```bash
docker cp /home/dkadi/monitoring/.prometheus.green-node.candidate.yml prometheus:/tmp/prometheus-green-node.yml
docker exec prometheus promtool check config /tmp/prometheus-green-node.yml
```

```text
Checking /tmp/prometheus-green-node.yml
SUCCESS: /tmp/prometheus-green-node.yml is valid prometheus config file syntax
Exit code: 0
```

The first guarded acceptance run rolled back because the target assertion omitted the existing Kasm blackbox probe. The second rolled back because the 60-second blackbox scrape cycle had not completed and nine existing probes were still `unknown`. I confirmed Green was absent and Prometheus healthy after each rollback before continuing.

## Final Deployment

The final run copied the validated candidate over the live file, preserving the bind-mounted inode, restarted Prometheus, waited for Green, and then waited through a complete scrape cycle. The immediate checks returned:

```text
backup=/home/dkadi/monitoring/prometheus.yml.bak.20260731T140158Z
inode_preserved=393283
hash_match=becd6552c7618a7e4b3be03f47027b70bba5e6fb4e1ba6315274475a3a429228
green_target=up last_error=none
Exit code: 0
```

## Final Verification

I uploaded the versioned assertion scripts temporarily, ran them against the live API and dashboard, checked the host and container configuration hashes, then removed the temporary copies.

```bash
set -eu
set -o pipefail
curl -fsS http://127.0.0.1:9090/api/v1/targets | python3 /home/dkadi/assert_targets.py | tail -2
python3 /home/dkadi/assert_dashboard_queries.py /home/dkadi/monitoring/grafana/dashboards/homelab-overview.json | tail -1
host_hash=$(sha256sum /home/dkadi/monitoring/prometheus.yml | awk '{print $1}')
container_hash=$(docker exec prometheus sha256sum /etc/prometheus/prometheus.yml | awk '{print $1}')
test "$host_hash" = "$container_hash"
printf 'host_container_sha256=%s\ngreen_target_entries=%s\n' "$host_hash" "$(grep -Fc '192.168.70.14:9100' /home/dkadi/monitoring/prometheus.yml)"
```

```text
ASSERTION: 49 expected targets present and all UP (29 scraped exporters, 20 blackbox services)
ASSERTION: stale addresses absent
65 queries: 65 returned data, 0 allowed empty, 0 unexpectedly empty, 0 errored
host_container_sha256=becd6552c7618a7e4b3be03f47027b70bba5e6fb4e1ba6315274475a3a429228
green_target_entries=1
Exit code: 0
```

Prometheus also returned `up=1`, node_exporter version 1.9.0, and 88 metric families whose names contain `smart` or `nvme` for `host="green-server"`.

