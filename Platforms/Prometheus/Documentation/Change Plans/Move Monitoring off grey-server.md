# Move Monitoring off grey-server

**Created:** 2026-07-26  
**Last updated:** 2026-07-26

**Status:** Planned, not started  
**Owner:** Prometheus infrastructure monitoring  
**Affected systems:** `security-01`, a new monitoring guest, UniFi firewall, Proxmox cluster firewall, Nginx Proxy Manager, all 44 scrape targets

## Why

Prometheus and Grafana run on `security-01`, which is a QEMU VM on `grey-server`. So do `app-01`, `docker-main`, and `splunk-siem`. Grey carries most of the fleet and 73% of its own memory:

```
grey-server      16 cpu   45.6 / 62.7 GiB used
blue-server       4 cpu    2.6 / 11.6 GiB used
purple-server     6 cpu    1.8 / 15.5 GiB used
red-server        6 cpu    3.0 / 15.5 GiB used
```

**If `grey-server` dies, monitoring dies with most of what it monitors, at the moment I would most want to look at it.** Purple's boot NVMe failed on 2026-07-25 and monitoring was unaffected, because monitoring is not on Purple. Grey failing is a different outcome: Prometheus, Grafana, Wazuh, Splunk, `app-01`, and `docker-main` all go at once and nothing is left to say what happened.

There is a smaller second reason. `security-01` uses 8 of its 12 GiB and almost all of that is Wazuh's indexer. Prometheus and Grafana are minor tenants on a VM dominated by a memory-hungry neighbour, so an OOM there does not necessarily kill the process I would choose.

## Not docker-blue

The obvious "spare Docker host" is the worst option available. `docker-blue` is a 4 GiB LXC on `blue-server`, the smallest node in the cluster at 4 CPUs and 11.6 GiB, and it already runs three containers whose fate the monitoring stack would then share. 4 GiB fits Prometheus at today's 40,000 series and leaves little room for the UniFi metrics and any retention increase.

## Target shape

A dedicated guest, `monitor-01`, on `purple-server` or `red-server`. Both sit near idle with 15.5 GiB.

| Property | Value |
|---|---|
| Node | `purple-server` or `red-server`, decided at step 1 |
| Type | VM, not LXC, so `node_exporter` on it reports its own hardware rather than the hypervisor's |
| Size | 2 vCPU, 6 GiB, 60 GiB disk |
| VLAN | 72 Security-A, keeping the same zone so existing policies need a source change rather than a rewrite |
| Workloads | `prometheus`, `grafana`, `pve-exporter`, `blackbox-exporter`, `nut-exporter`, `cadvisor` |
| Left on `security-01` | Wazuh manager, indexer, dashboard, and its own `node_exporter` and cAdvisor |

Staying inside VLAN 72 is the single biggest cost saver. Every existing UniFi policy is scoped Security-A to somewhere, so a new address in the same zone means editing a source, not designing a new zone pair.

## What is hard about this

Not the containers. The whole monitoring stack is already Compose plus versioned configuration in this repository, so standing it up elsewhere is a clone and a `docker compose up`. What is hard is that **the collector's IP address is written by hand into six rules across two firewalls that enforce independently**, and a missed rule produces a silently dead target rather than an error.

`192.168.72.2` currently appears in:

| System | Rule | Covers |
|---|---|---|
| UniFi | Security-A to Personal-A | 9100 and 9101 on docker-main, ansible-01, docker-blue, media-01 |
| UniFi | Security-A to SERVERS-A | 9100 and 9101 on app-01, alpha-prod-01 |
| UniFi | Security-A to Access-A | 9100, 9101, and 443 on docker-network |
| UniFi | Security-A to MGMT-A | 3493 on grey-server and red-server, plus 8006 for the PVE exporter |
| Proxmox `cluster.fw` | `IN ACCEPT` | 3493 on 192.168.70.10 |
| Proxmox `cluster.fw` | `IN ACCEPT` | 3493 on 192.168.70.13 |

The lesson from 2026-07-25 applies directly: the UniFi policy for NUT was correct and the path stayed blocked for a day because the Proxmox cluster firewall dropped it separately. Nothing surfaces that. The target just reads down.

## Steps

1. **Pick the node.** Compare `purple-server` and `red-server` on current load, disk headroom on their storages, and what else they hold. Red holds `media-01` and `ups01`; Purple has the newer boot drive. Record the reason.
2. **Build `monitor-01`** from template 9000 per the [Linux Host Baseline Standard](../../../../Security/Hardening/Linux-Host-Baseline-Standard.md). Remember `qm set --delete cicustom` after cloning or the cloud-init keys are overridden and you are locked out.
3. **Add it to the exporter inventory** in [monitoring-exporters](../../../Ansible/Source/monitoring-exporters/README.md) under `node_exporter_targets` and `cadvisor_targets`, update `EXPECTED_IPS` and both expected host sets in the validator, and install.
4. **Duplicate the firewall rules to the new source, do not move them.** Add `monitor-01` alongside `192.168.72.2` in all four UniFi policies and add two more `IN ACCEPT` lines to `cluster.fw`. Both collectors reachable at once is what makes the cutover reversible.
5. **Prove reachability before moving anything.** From `monitor-01`, curl 9100 and 9101 on all 14 hosts, 3493 on both UPS units, 8006 on grey, and 443 on `docker-network`. Every one must answer before the stack moves. A failure here is a firewall problem; a failure after the move is a mystery.
6. **Stand the stack up** from `Configuration/` in this repository, substituting the real base domain. Point it at the same targets. Run both collectors in parallel and let it fill.
7. **Migrate Grafana.** The datasource and `homelab-overview` are file-provisioned, so they come across with the repository. `grafana.db` still holds users, preferences, and API keys, so copy the volume rather than starting fresh. Verify the dashboard provisions and all 65 queries return data.
8. **Re-point NPM.** The `grafana.` and `prometheus.` proxy hosts in [Nginx Proxy Manager](../../../Nginx%20Proxy%20Manager/) point at `192.168.72.2`. Change both to `monitor-01` and confirm the certificate and the real user path still work.
9. **Decommission the old stack.** Stop the six containers on `security-01`, leave Wazuh alone, confirm 44 targets still report from the new collector, then remove the old UniFi sources and the two old `cluster.fw` lines. Keep `security-01` itself as a scrape target and a cAdvisor host.
10. **Update the records.** `prometheus.yml` self-scrape address, `assert_targets.py` expected URLs, both firewall inventories, `Operations/Inventory/Galaxy/` VMs and Services, this platform's README and runbook, and a change record for the move.

## Rollback

Steps 1 through 6 add things and change nothing, so rollback is deleting the new guest. The commit point is step 8, re-pointing NPM. Before that, the old stack is still running and still authoritative. After it, rollback means pointing NPM back and restarting the six containers on `security-01`, which stays possible until step 9 removes them.

Keep the old `grafana_data` volume until the new stack has run clean for a week.

## What this does not fix

Correlated failure, only reduced. HA is disabled on every guest, so whichever node holds `monitor-01` still takes monitoring down when it fails. Real survivability needs HA, and HA needs shared storage that `ssd-lvm1` and a local ZFS pool do not provide. Worth checking what the cluster's storages actually support before assuming this is available.

Nothing here alerts. A perfectly placed collector that nobody is watching is worth less than a badly placed one that pages, which is why the [platform backlog](../TODO.md) puts alert routing ahead of this move.

## Sequencing

After alerting. Alerting covers the many ordinary failures where the monitoring host is fine and something else broke; this covers one specific scenario. Doing it second also means the alert rules move with the stack instead of being written twice.
