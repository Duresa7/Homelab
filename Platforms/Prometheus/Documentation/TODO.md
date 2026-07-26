# Prometheus TODO

**Created:** 2026-07-13  
**Last updated:** 2026-07-26

Three items open. The UPS item closed on 2026-07-26 once the Proxmox cluster firewall permitted `192.168.72.2` to TCP 3493; both units now report and the dashboard carries a Power row. I record future monitoring changes here before promoting them to an active project.

## Open

**Recover per-container metrics on the six `overlayfs` hosts.** cAdvisor covers `docker-main` alone, so the container row shows 14 of roughly 46 containers. Either wait for cAdvisor to support the containerd snapshotter layout and add the six hosts back to `cadvisor_targets`, or vet a Docker-API-based exporter that reads `/containers/<id>/stats` and sidesteps the storage driver. Details and the three fixes that already failed are in [the troubleshooting record](Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

**Scrape `kasm-01`.** It's the one running host with no `node_exporter`. It sits outside the Ansible inventory, and the move to `purple-server` in [Kasm Relocation to Purple](../../Kasm%20Workspaces/Documentation/Change%20Plans/) is still open, so its address may change. Adding it now means redoing the inventory entry and the firewall scope afterward.

**Collect UniFi gateway, switch, and access-point metrics.** WAN throughput and per-AP client counts are the largest remaining blind spot, and the repository has never enumerated the access points or cameras. `unpoller` needs a read-only UniFi local account, which is a new credential in 1Password and deserves its own change record rather than being folded into a dashboard task.

## Known limits, not tracked as work

Prometheus and Grafana both run floating `:latest` tags. The four exporters added on 2026-07-25 are pinned (`blackbox-exporter:v0.27.0`, `cadvisor:v0.52.1`, `prometheus-nut-exporter:1`, `node_exporter` 1.9.0), so the two unpinned images are the older ones.

There are no alert rules and no Alertmanager. Rules that fire into nothing are worse than no rules, so this starts with choosing where notifications go, not with writing rules.
