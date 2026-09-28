# WUD Retirement

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

**Implemented:** 2026-09-27  
**Status:** Complete  
**Affected systems:** `docker-main`, `docker-blue`, `docker-network`, `media-01`, `alpha-prod-01`, `monitor-01`, `ansible-01`, Dockhand, Homarr, Nginx Proxy Manager and UniFi

I removed What's Up Docker from all six hosts because Dockhand already checks container images and applies the configured updates. WUD had supplied a separate container-image alert through Prometheus and Grafana and an update widget in Homarr. I retired those connections with it. OS-update, security-update and reboot alerts remain in Grafana; Dockhand's schedules and exclusions remain unchanged.

## Monitoring and applications

I removed the six authenticated WUD scrape configurations from `/home/dkadi/monitoring/prometheus-config/prometheus.yml`. The live file matched the repository before editing. `promtool check config` passed, then I sent Prometheus SIGHUP to reload without restarting its container. Its target API returned 50 targets across six jobs, all up: node 17, cAdvisor 8, blackbox 22, Proxmox 1, NUT 1 and self-scrape 1. The versioned target assertion passed against that live response.

I removed `homelab-image-update` from the Grafana provisioning file and added a `deleteRules` entry for its UID. An authenticated `POST /api/admin/provisioning/alerting/reload` returned HTTP 200. Readback showed exactly that rule removed, the other 23 UIDs preserved, and no rule evaluation errors. The deletion entry remains in the versioned file so an older database also loses the retired rule on provisioning. I removed `/home/dkadi/monitoring/prometheus-config/wud-passwords` after removing the scrapes.

Homarr was being cleaned up separately during this work. My first removal checks stopped before writing because its app count and board items had changed. I reread the current board rather than restoring the earlier layout. Final readback found no WUD integration, widget or shortcut: nine integrations and 41 board items remained, and the readiness endpoint returned HTTP 200. The separate Homarr cleanup owns the layout changes. The Apps API returned 33 catalog entries at my final check; this count includes entries outside the 32 shortcuts on the board.

## Six host removals

I used Dockhand's deletion preview on each `wud` stack. Every preview named only `/opt/docker/dockhand/stacks/imported/<host>/wud` and the named volume `wud_wud_store`. I deleted each stack with its files and volume through the API; all six returned success. A later API read found no WUD stack in any of the seven Dockhand environments.

The original `/opt/docker/wud` directories remained after Dockhand removed its imported definitions. I deleted those directories, including the dedicated `admin.env` credentials, and removed the unused `getwud/wud:latest`, `8.4.0` and `8.3.1` image tags from every host. I also checked `/opt/docker/hawser/stacks/wud`; no deployed definition remained there. A first unprivileged directory check failed on Hawser's protected parent directory, so I repeated the cleanup with the configured sudo access. No credential values were printed.

| Host | Other containers preserved | Running after removal |
|---|---:|---:|
| docker-main | 15 | 14 |
| docker-blue | 11 | 10 |
| docker-network | 6 | 5 |
| media-01 | 11 | 10 |
| alpha-prod-01 | 8 | 7 |
| monitor-01 | 10 | 9 |

All 61 other containers kept their IDs, start timestamps and states. The table includes the existing stopped documentation container and inactive Hawser updater helpers. Each host had no WUD container, volume, network, image or listener on TCP 9102 after removal. I left the inert WUD tag-filter labels on application containers in place; removing a label from their running configuration would require recreation and gives no benefit after WUD is gone.

## Deployment and network cleanup

I removed `playbooks/wud.yml`, the `wud_targets` inventory group, both WUD Semaphore template declarations and their view from `monitoring-exporters`, in the repository and on `ansible-01`. Both project validators passed with nine node-exporter targets and eight cAdvisor targets. The live Semaphore database held 23 templates and no WUD template or view, so no database mutation was needed. The remaining exporter inventory retains its earlier differences between the controller and repository; I did not overwrite unrelated inventory state.

I deleted NPM proxy host 35 for `wud.alphasecunited.com`; all other host IDs were preserved, leaving 24 live hosts. `nginx -t` passed. I deleted its UniFi local DNS record, leaving 30 static records, and removed TCP 9102 from `PG-Node-Exporter`, `Allow Monitor to A-Access monitoring` and `Allow NPM to docker-main web UIs`. The policies keep their existing selectors and other ports. The exporter port group now contains 9100 and 9101. Prometheus's post-change target assertion still reported all 50 targets up, and Homarr and App Portal readiness checks returned HTTP 200 through NPM.

I updated the living service inventory, monitoring and automation records, target assertion, network references, monitoring guide and five generated diagrams. Historical deployment and troubleshooting records remain as evidence of the earlier installation. The [host verification](../../Evidence/WUD%20Retirement%20-%202026-09-27/Exports/Host-Verification.json), [application verification](../../Evidence/WUD%20Retirement%20-%202026-09-27/Exports/Application-Verification.json), [target validation](../../Evidence/WUD%20Retirement%20-%202026-09-27/Exports/Target-Validation.json) and other filtered exports retain the observed results. I retained no separate raw terminal transcript for the API writes, credential handling, host cleanup, controller edits or network changes.

No work remains for this retirement. I took no snapshot or backup; restoring WUD would be a new deployment from the earlier git revision with newly created service credentials. Prometheus keeps previously collected WUD samples until its 15-day retention expires.
