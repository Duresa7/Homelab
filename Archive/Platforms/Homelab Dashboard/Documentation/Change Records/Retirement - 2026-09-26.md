# Retirement

**Created:** 2026-09-26  
**Last updated:** 2026-09-26

**Status:** Complete  
**Date:** 2026-09-26

I retired Homelab Dashboard from `docker-main` (`192.168.40.35`, CT 110). The container had exited with code 137 at 3:39 AM Eastern on 2026-09-22. Its `probe_success` was 0, and Grafana's `Internal service is unreachable` alert was firing for `https://dashboard.alphasecunited.com/`. This work removes the service; I did not establish why it originally stopped.

## Removal

| Owner | Change and observed result |
|---|---|
| Docker Main | I removed `homelab-dashboard-aio` through Dockhand's authenticated stack API with stack-file and named-volume removal enabled. The preview listed no named volumes. I then deleted `/opt/docker/homelab-dashboard-aio`, including its environment file, application key and SQLite data. The imported definition under `/opt/docker/dockhand/stacks/imported/docker_main/homelab-dashboard-aio` was absent after the API operation. |
| Docker resources | I removed the unused `homelab-dashboard-aio_default` network and both image tags, `latest` and `sha-7585b06`. No dashboard container remains, TCP 3001 is closed, and all 14 remaining running containers have no unhealthy health checks. Docusaurus remains stopped as it was before this work. |
| Maintenance | I removed the dashboard project from the repository and live `/home/ansible/fleet-updates` inventory and validator. Both validators passed with 11 OS-update hosts, six Compose hosts and 19 projects. |
| Nginx Proxy Manager | I deleted proxy host 12 through its authenticated API. The active host count is 23; generated `12.conf` is absent. `nginx -t` passed and the container remained healthy. Certificate 1 is shared and remains in use. |
| UniFi | I deleted DNS record `6a60fd2b2d027bb05525a84f`, removed TCP 3001 from `Allow NPM to docker-main web UIs`, and deleted `Docker-main Allowed -> Server`, which admitted dashboard Proxmox API traffic on TCP 8006. Readback returned 29 DNS records, including 23 NPM names, and 88 firewall policies: 80 allows and eight blocks. Other ports in the shared NPM rule remain. |
| Proxmox | I verified the live monitoring exporter uses `pve-exporter@pve!monitor01`, then deleted the dashboard's `local-dash@pve!readonly` token and `local-dash@pve` account. Readback showed no dashboard user or ACL and retained the monitoring user. Token deletion briefly reported an invalid token ACL; the subsequent user deletion removed it, and the final ACL count was zero. |
| Prometheus | I removed only the dashboard blackbox target, validated with `promtool check config`, and reloaded with SIGHUP. I removed Homepage from the uptime generator and deployed the regenerated JSON. The shared alert rules and Discord delivery remain enabled. |

Initial non-interactive sudo checks on `docker-network` and `monitor-01` failed with `sudo: a password is required`. Their existing Docker access and owned configuration paths were sufficient; I changed no privilege policy. An unauthenticated Grafana alert read returned 401; the authenticated read established the firing alert and its later removal.

## Source archive

I preserved the Compose reference in this archive and retained the source in [Forgejo](https://forgejo.alphasecunited.com/dkadi/Homelab-Dashboard). The repository is ID 3, `dkadi/Homelab-Dashboard`.

Forgejo API reads returned 403, and the standard application login redirected to its password-change page. A temporary token scoped to `write:repository` also returned 403. I removed that token and verified its count was zero. I then set only repository 3's `is_archived` flag in a guarded SQLite transaction and read back `is_archived=1`. I changed no account password. The Git repository remains on disk as the source archive.

## Verification

At 12:18 PM Eastern, the [final checks](../../Evidence/Retirement%20-%202026-09-26/Exports/Final-Verification.json) showed:

- No Grafana alert instance for the dashboard URL and no reference to it in the provisioned uptime dashboard.
- All 56 expected Prometheus targets up, no failing blackbox probes, and the Proxmox exporter still reporting after credential removal.
- All 23 remaining HTTPS hosts returned their expected response or redirect with valid TLS. App Portal returned its existing root-path 404; none returned a gateway error.
- The regenerated uptime dashboard passed the layout assertion and all 112 query checks returned data without errors.

I updated the current service, access, DNS, firewall, automation and monitoring records, and regenerated the NPM and Prometheus diagrams with PNG renders. Historical deployment and incident records retain their event dates and observations.

The JSON export retains the final monitoring and HTTPS results. No complete terminal transcript is retained for the removal, credential, firewall, DNS, source archive or reload steps; the table records their observed results. I created no snapshot or backup and left no temporary credential or staging file. Nothing remains open for this retirement.
