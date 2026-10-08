# Duplicate Exporters Contended for Port 9100

**Created:** 2026-10-07  
**Last updated:** 2026-10-07

**Status:** Resolved 2026-10-07

I found `node_exporter.service` on docker-main restarting every five seconds with `listen tcp :9100: bind: address already in use`. Its counter reached 549642 before the repair. Debian's packaged exporter 1.5.0 held port 9100, so Prometheus still reported the target up. On security-01, upstream 1.9.0 held the port and Ubuntu's duplicate 1.7.0 service was failed instead.

The September 2 textfile-collector deployment installed `prometheus-node-exporter-collectors`. Debian 12 and Ubuntu 24.04 make it depend on the distro exporter, so `install_recommends: false` did not prevent a second service. With both services enabled, startup order decided which exporter owned the port. A failed-unit check missed docker-main because its upstream unit was `activating/auto-restart`.

I stopped and masked `prometheus-node-exporter.service` on both hosts, retained the packages for their collector scripts, and started upstream 1.9.0 on docker-main. Security-01's upstream service stayed running. I corrected [textfile-collectors.yml](../../../Ansible/Source/monitoring-exporters/playbooks/textfile-collectors.yml) to suppress package service startup, stop and mask the duplicate, clear any retained failure, and verify the intended service's restart counter before checking metrics.

My initial docker-main command stopped on `Unit prometheus-node-exporter.service not loaded` when resetting the already-masked unit. I completed the upstream start immediately in the next call. Its first metrics connection failed before the listener was ready; the retry returned 1.9.0 and `node_textfile_scrape_error 0`.

The corrected play then passed on both hosts with zero changes and zero failures. At 9:25 PM EDT both services were active, both duplicates inactive and masked, and their counters had stayed at 549642 and zero respectively. All 50 Prometheus targets were up. Wazuh recorded zero new docker-main exporter alerts in the short 9:19 PM to 9:22 PM observation window. The counters, commands, full play recap and alert check are retained in the [repair record](../../../../Operations/Maintenance/Service%20Failure%20Repairs%20-%202026-10-07.md).
