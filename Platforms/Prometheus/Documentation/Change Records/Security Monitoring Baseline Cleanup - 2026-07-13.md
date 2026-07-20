# Security Monitoring Baseline Cleanup

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

**Implementation date:** 2026-07-13  
**Status:** Complete  
**Primary owner:** Prometheus infrastructure monitoring  
**Affected systems:** `security-01`, `app-01`, `edge-01`, `supabase-01`, `alpha-prod-01`, `purple-server`, `blue-server`, `red-server`, Wazuh manager, Prometheus

## Scope

I closed the monitoring gaps I had deliberately deferred from the Security-A migration: install `node_exporter` on the three Galaxy nodes that lacked it, remove the obsolete Wazuh registrations so I could perform fresh enrollment, and reconcile the stale Prometheus target set. I also wanted a verified list of the service endpoints moved or added by the related work.

## Starting State

- `purple-server`, `blue-server`, and `red-server` ran Debian 13 but had no exporter package, service, or TCP/9100 listener. `grey-server` already ran manual `node_exporter` 1.9.0.
- The Wazuh manager listed disconnected ID `002` `edge-01` and ID `003` `wp-01`.
- `app-01` had Wazuh agent 4.14.5 active with the incorrect `wp-01` key; `edge-01` had 4.10.3 active with its old key. Both still targeted retired manager address `192.168.70.20`.
- `supabase-01` and `alpha-prod-01` had no Wazuh agent package or key.
- Prometheus had six jobs: three healthy (`edge-01`, `grey-server`, `proxmox`) and three down/stale (`apps-01`, retired `security-01` address `192.168.70.20`, and `supabase-01`).

## Decisions

- I installed Debian's signed `prometheus-node-exporter` package version `1.9.0-1+b4`; it matches the major/minor exporter version already used on `grey-server` and stays managed through APT.
- I preserved one job per Proxmox node so the existing job-label behavior for `grey-server` did not change.
- I corrected the local `security-01` target to `192.168.72.2` and removed `app-01` and `supabase-01` rather than presenting known-unavailable targets as monitoring coverage.
- I removed only the two actual obsolete Wazuh registrations. I did not fabricate records for `supabase-01` or `alpha-prod-01`, which had no agent installed.
- I prepared `app-01` and `edge-01` for fresh enrollment: retained their packages, repointed the manager address, cleared stale keys, and stopped/disabled the services. The enrollment itself was a separate follow-up I performed later.

## Actions and Observed Results

### 1. Install the missing node exporters

I installed `prometheus-node-exporter` 1.9.0-1+b4 and its collector package through APT on `purple-server`, `blue-server`, and `red-server`. Each service is enabled and running. Local metrics checks and remote checks from `security-01` returned HTTP `200` with `node_uname_info` for all four Galaxy nodes.

### 2. Reset obsolete Wazuh registrations

I stopped and disabled `app-01` and `edge-01`, changed their manager address from `192.168.70.20` to `192.168.72.2`, and cleared their stale client-key files to zero bytes with root/Wazuh ownership. I removed the manager registrations ID `002` `edge-01` and ID `003` `wp-01`. A fresh manager list contains only local ID `000` `wazuh-01`.

The incorrect `wp-01` identity and retired manager address are recorded in the [Wazuh troubleshooting log](../../../Wazuh/Documentation/Troubleshooting-Log.md#1-incorrect-and-stale-endpoint-identities).

I left `supabase-01` and `alpha-prod-01` unchanged because neither has the agent installed. Fresh install/enrollment is tracked in the [Wazuh TODO](../../../Wazuh/Documentation/TODO.md).

### 3. Reconcile Prometheus

The versioned and live configurations now contain seven jobs: `security-01`, `edge-01`, `grey-server`, `purple-server`, `blue-server`, `red-server`, and `proxmox`. I validated the candidate with `promtool` before applying it.

My first host-path replacement plus SIGHUP did not change the running target set because Docker's single-file bind mount stayed attached to the old inode. A controlled Prometheus restart rebound the validated file. Prometheus returned ready, the in-container config passed `promtool`, the exact expected target set reported all seven jobs `UP`, and the retired `.70.20`, `app-01`, and `supabase-01` addresses were absent. See the [troubleshooting log](../Troubleshooting-Log.md#1-single-file-bind-mount-retained-the-old-inode).

## Resulting Configuration

| Job | Target | Result |
|---|---|---|
| `security-01` | `192.168.72.2:9100` | `UP` |
| `edge-01` | `192.168.90.10:9100` | `UP` |
| `grey-server` | `192.168.70.10:9100` | `UP` |
| `purple-server` | `192.168.70.11:9100` | `UP` |
| `blue-server` | `192.168.70.12:9100` | `UP` |
| `red-server` | `192.168.70.13:9100` | `UP` |
| `proxmox` | PVE exporter querying `192.168.70.10` | `UP` |

## Service Endpoints

| Service | Endpoint | Verification |
|---|---|---|
| Wazuh dashboard | `https://192.168.72.2/` | HTTP `302` |
| Wazuh API | `https://192.168.72.2:55000/` | HTTP `401` without credentials (expected) |
| Grafana | `http://192.168.72.2:3000/` | HTTP `302` |
| Prometheus | `http://192.168.72.2:9090/` | HTTP `302`; readiness passed |
| Security host node exporter | `http://192.168.72.2:9100/metrics` | HTTP `200` |
| Proxmox API exporter | `http://192.168.72.2:9221/` | HTTP `200` |
| Splunk Web | `https://192.168.72.3:8000/` | HTTP `303` |
| Splunk HEC health | `https://192.168.72.3:8088/services/collector/health` | HTTP `200` locally; backend-only from client VLAN |
| Splunk management API | `https://192.168.72.3:8089/` | HTTP `200` locally; backend-only from client VLAN |
| SC4S syslog | `tcp://192.168.72.3:1514` and `udp://192.168.72.3:1514` | Listeners active |
| Purple node exporter | `http://192.168.70.11:9100/metrics` | HTTP `200` from `security-01` |
| Blue node exporter | `http://192.168.70.12:9100/metrics` | HTTP `200` from `security-01` |
| Red node exporter | `http://192.168.70.13:9100/metrics` | HTTP `200` from `security-01` |

## Verification

- SSH Manager reported all three new exporter services enabled, running, and healthy.
- My Prometheus assertion script found exactly the seven expected jobs and all seven `UP`; stale addresses were absent.
- The Wazuh manager listed only local ID `000` after cleanup.
- `app-01` and `edge-01` reported the new manager address, zero-byte client-key files, and inactive/disabled agent services.
- Wazuh manager/indexer/dashboard, Docker, Splunkd, SC4S, and both SSH endpoints remained operational. The generic Ubuntu service-name check produced a false SSH warning, but `ssh.socket`, `ssh.service`, and TCP/22 were all active.
- I changed no firewall or WAN exposure.

## Rollback Points

- Prometheus: `/home/<YOUR_ADMIN_USERNAME>/monitoring/prometheus.yml.bak.security-monitoring-cleanup-20260713` on `security-01`.
- Wazuh manager keys: `/var/ossec/etc/client.keys.bak.security-monitoring-cleanup-20260713` on `security-01`, mode 0600.
- Endpoint configs: `/var/ossec/etc/ossec.conf.bak.security-monitoring-cleanup-20260713` on `app-01` and `edge-01`, mode 0600.
- The newly installed exporter packages can be removed with APT if rollback is required; no Proxmox networking or firewall state changed.

The Wazuh manager backup preserves the pre-change registration state. Restoring it would also restore the retired identities.

## Step Summary

| Step | What it established |
|---|---|
| S00: Preflight | The exact missing exporters, stale Wazuh identities, and stale Prometheus targets |
| S01: Node exporter installation | Package/service state and end-to-end metrics reachability |
| S02: Wazuh registration reset | Endpoint preparation and manager registration removal |
| S03: Prometheus reconciliation | Config validation, reload diagnosis, restart, and the seven-target assertion |
| S04: Final service and URL verification | Current health and replacement endpoint responses |

## Remaining Work

Only fresh Wazuh installation and enrollment remained, which I deliberately kept as a separate follow-up. The monitoring exporter and Prometheus cleanup requested in this change are complete.
