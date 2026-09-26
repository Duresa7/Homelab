# Prometheus Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-09-25

## What This Guide Covers

I installed the missing node exporters, removed stale scrape jobs, validated the replacement configuration, and asserted the exact target set against the live API. The steps are the 2026-07-13 baseline cleanup. The guide also covers the Docker bind-mount behavior that forced a restart.

## Current Status and Verified Versions

Verified on 2026-09-24 from the target and rules APIs. Prometheus 3.14.0 runs in Docker on CT 104 `monitor-01` at `192.168.73.2:9090` with a 15-second default scrape interval. It scrapes 57 targets, all `UP`, in seven jobs:

| Job | Targets |
|---|---|
| `node` | 17 |
| `cadvisor` | 8 |
| `wud` (What's Up Docker) | 6 |
| `blackbox` | 23 |
| `proxmox` | 1 |
| `nut` | 1 |
| `prometheus` (self) | 1 |

Prometheus itself holds no alert rules and there is no Alertmanager. Alerting lives in Grafana 13.2.2 on the same host: 24 file-provisioned rules in `alphasec-united-alerts.yaml` route to one contact point, the [Discord Alert Bot](../Platforms/Discord%20Alert%20Bot/README.md), which posts to one Discord channel.

`ubuntu-dev` (`192.168.40.179`) is in the `node` job as `role=workstation` and stays out of the `cadvisor` job, because its containers are throwaway builds. The NUT job has one target since `UPS-01` lost its data cable on 2026-08-28.

## What You Need

- A running Prometheus server and access to its configuration.
- TCP 9100 reachability from Prometheus to each node exporter.
- `promtool` for candidate validation.
- A console or SSH session on every host receiving an exporter.

## How the Pieces Fit Together

![Prometheus on monitor-01 scraping seven jobs: node, cAdvisor, What's Up Docker, blackbox, Proxmox, NUT, and itself](../Assets/Diagrams/prometheus.svg)

## Walkthrough

### Step 1: Record the Existing Target Set

I queried the Prometheus target API and noted each job, address, health state, and last error. On 2026-07-13 the starting set held three working jobs and three stale or down ones. Prometheus ran on `security-01` then; it moved to `monitor-01` on 2026-07-26.

### Step 2: Install the Missing Exporters

I installed `prometheus-node-exporter` 1.9.0-1+b4 on purple, blue, and red through APT, then enabled the service.

```sh
sudo apt update
sudo apt install prometheus-node-exporter
sudo systemctl enable --now prometheus-node-exporter
curl -fsS http://127.0.0.1:9100/metrics | grep node_uname_info
```

I repeated the HTTP check from `security-01` to prove the network path as well as the local service.

### Step 3: Reconcile the Configuration

I added one job for each Galaxy node, corrected `security-01` to `192.168.72.2`, kept the `edge-01` and Proxmox jobs, and removed the retired address and the unavailable application hosts.

### Step 4: Validate Before Applying

I checked the candidate with `promtool` before it replaced the live file.

```sh
promtool check config prometheus.yml
```

### Step 5: Apply the File and Restart When Needed

My first host-path replacement and SIGHUP left the container attached to the old single-file bind-mount inode. I restarted Prometheus so Docker rebound the current file, then checked readiness and ran `promtool` against the in-container path.

### Step 6: Assert the Exact Result

I ran the repository assertion script against the live API. On 2026-07-13 it required the exact 49-target set of that day, required every target to be `UP`, checked the expected job and host labels, and rejected stale addresses. The script is edited forward as targets change.

```sh
cd <YOUR_HOMELAB_REPO>/Platforms/Prometheus
python3 Tests/assert_targets.py
```

## What I Checked After Each Step

- All four node-exporter endpoints returned HTTP 200 with `node_uname_info`.
- The candidate and in-container configurations passed `promtool`.
- Prometheus returned ready after restart.
- All 49 targets across six jobs reported `UP` on 2026-07-13.
- The retired `.70.20`, `app-01`, and `supabase-01` targets were absent.

## Troubleshooting and Recovery

If a valid host-side file doesn't change the running target set after SIGHUP, check that the Compose volume still mounts the `prometheus-config` directory rather than the file inside it. A single-file mount pins the inode and swallows the reload without an error; that cost me three reloads before I changed it on 2026-08-06. If one target stays down, test its `/metrics` endpoint from the Prometheus host before changing the scrape job.

## Known Limits

The steps and the 49-target figure are the 2026-07-13 baseline. The current target list, dashboards, and recovery procedure are in the platform README and runbook. A scrape target that stays down raises an alert only through Grafana; Prometheus has nothing to fire on its own.

## Source Records

- [Prometheus overview](../Platforms/Prometheus/README.md)
- [Grafana alert rules](../Platforms/Prometheus/Documentation/Change%20Records/Grafana%20Alert%20Rules%20-%202026-09-01.md)
- [Baseline cleanup](../Platforms/Prometheus/Documentation/Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md)
- [Relocation to monitor-01](../Platforms/Prometheus/Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md)
- [Versioned configuration](../Platforms/Prometheus/Configuration/prometheus-config/prometheus.yml)
- [Runbook](../Platforms/Prometheus/Documentation/Runbook.md)
- [Troubleshooting index](../Platforms/Prometheus/Documentation/Troubleshooting/README.md)
