# Prometheus Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-08-03

## What This Guide Covers

I installed the missing node exporters, removed stale scrape jobs, validated the replacement configuration, & expanded the same test pattern to the current six-job target set. This guide also covers the Docker bind-mount behavior that required a restart.

## Current Status and Verified Versions

Prometheus 3.13.1 runs on CT 104 `monitor-01` at `192.168.73.2:9090` with a 15-second default scrape interval. All 52 targets were `UP` on 2026-08-08 across six jobs: node 19, cAdvisor 9, Proxmox 1, blackbox 20, NUT 2, & self-scrape 1. The node job took its nineteenth member that day, when `debian-dev` picked up the same 1.9.0 exporter every other host runs & Prometheus started scraping it under the label `role=workstation`. It stays out of the cAdvisor job on purpose: the containers on a workstation are throwaway builds, so per-container history there is noise. The blackbox job dropped from 20 to 19 when I retired Syncthing on 2026-08-06, then returned to 20 when `game-01` arrived the next day. Purple, blue, red, & green run Debian package `prometheus-node-exporter` 1.9.0-1+b4; grey runs manual node_exporter 1.9.0.

## What You Need

- A running Prometheus server and access to its configuration.
- TCP 9100 reachability from Prometheus to each node exporter.
- `promtool` for candidate validation.
- A console or SSH session on every host receiving an exporter.

## How the Pieces Fit Together

![Prometheus scrape flow from six jobs: node, cAdvisor, Proxmox, blackbox, NUT, and the self-scrape](../Assets/Diagrams/prometheus.svg)

## Walkthrough

### Step 1: Record the Existing Target Set

I queried the Prometheus target API and noted each job, address, health state, & last error. The starting set contained three working jobs and three stale or down jobs.

### Step 2: Install the Missing Exporters

I installed `prometheus-node-exporter` 1.9.0-1+b4 on purple, blue, & red through APT, then enabled the service.

```sh
sudo apt update
sudo apt install prometheus-node-exporter
sudo systemctl enable --now prometheus-node-exporter
curl -fsS http://127.0.0.1:9100/metrics | grep node_uname_info
```

I repeated the HTTP check from `security-01` to prove the network path as well as the local service.

### Step 3: Reconcile the Configuration

I added one job for each Galaxy node, corrected `security-01` to `192.168.72.2`, kept the `edge-01` and Proxmox jobs, & removed the retired address plus unavailable application hosts.

### Step 4: Validate Before Applying

I checked the candidate with `promtool` before it replaced the live file.

```sh
promtool check config prometheus.yml
```

### Step 5: Apply the File and Restart When Needed

My first host-path replacement and SIGHUP left the container attached to the old single-file bind-mount inode. I restarted Prometheus so Docker rebound the current file, then checked readiness and ran `promtool` against the in-container path.

### Step 6: Assert the Exact Result

I ran the repository assertion script against the live API. It requires the exact 49-target set, requires every target to be `UP`, checks the expected job and host labels, & rejects stale addresses.

```sh
cd <YOUR_HOMELAB_REPO>/Platforms/Prometheus
python3 Tests/assert_targets.py
```

## What I Checked After Each Step

- All four node-exporter endpoints returned HTTP 200 with `node_uname_info`.
- The candidate and in-container configurations passed `promtool`.
- Prometheus returned ready after restart.
- All 49 targets across six jobs reported `UP`.
- The retired `.70.20`, `app-01`, & `supabase-01` targets were absent.

## Troubleshooting and Recovery

If a valid host-side file doesn't change the running target set after SIGHUP, check that the Compose volume still mounts the `prometheus-config` directory rather than the file inside it. A single-file mount pins the inode and swallows the reload without an error; that cost me three reloads before I changed it on 2026-08-06. If one target stays down, test its `/metrics` endpoint from the Prometheus host before changing the scrape job.

## Known Limits

This walkthrough preserves the original baseline procedure, so the 49-target figures above are what I saw on the day rather than the current count. The current target list, dashboard checks, and recovery procedure live in the platform README and runbook. Nothing here alerts: the platform has no alert rules and no Alertmanager.

## Source Records

- [Prometheus overview](../Platforms/Prometheus/README.md)
- [Baseline cleanup](../Platforms/Prometheus/Documentation/Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md)
- [Relocation to monitor-01](../Platforms/Prometheus/Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md)
- [Versioned configuration](../Platforms/Prometheus/Configuration/prometheus-config/prometheus.yml)
- [Runbook](../Platforms/Prometheus/Documentation/Runbook.md)
- [Troubleshooting index](../Platforms/Prometheus/Documentation/Troubleshooting/README.md)
