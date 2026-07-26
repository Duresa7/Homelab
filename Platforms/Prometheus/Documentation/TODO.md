# Prometheus TODO

**Created:** 2026-07-13  
**Last updated:** 2026-07-26

Three items open. Two closed on 2026-07-26: UPS collection, once the Proxmox cluster firewall permitted `192.168.72.2` to TCP 3493, and per-container metrics on the six `overlayfs` hosts, once cAdvisor moved to v0.60.5. I record future monitoring changes here before promoting them to an active project.

## Open

**Scrape `kasm-01`.** It's the one running host with no `node_exporter`. It sits outside the Ansible inventory, and the move to `purple-server` in [Kasm Relocation to Purple](../../Kasm%20Workspaces/Documentation/Change%20Plans/) is still open, so its address may change. Adding it now means redoing the inventory entry and the firewall scope afterward.

**Collect UniFi gateway, switch, and access-point metrics.** WAN throughput and per-AP client counts are the largest remaining blind spot, and the repository has never enumerated the access points or cameras. `unpoller` needs a read-only UniFi local account, which is a new credential in 1Password and deserves its own change record rather than being folded into a dashboard task.

**Decide where alerts go, then write rules.** There are no alert rules and no Alertmanager. I kept alerting out of the 2026-07-25 expansion deliberately, because rules that fire into nothing are worse than no rules, so this starts with picking a notification path rather than with writing conditions. The dashboard already encodes the thresholds worth alerting on: targets down, `probe_success == 0`, certificate expiry, ZFS pool state, `nvme_critical_warning`, NVMe spare below 10%, filesystem above 90%, and a UPS off mains.

## Known limits, not tracked as work

Prometheus and Grafana both run floating `:latest` tags. The four exporters added on 2026-07-25 are pinned (`blackbox-exporter:v0.27.0`, `cadvisor:v0.52.1`, `prometheus-nut-exporter:1`, `node_exporter` 1.9.0), so the two unpinned images are the older ones.
