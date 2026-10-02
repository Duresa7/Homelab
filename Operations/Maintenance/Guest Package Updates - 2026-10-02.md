# Guest Package Updates

**Created:** 2026-10-02  
**Last updated:** 2026-10-02

**Implementation date:** 2026-10-02  
**Status:** Package updates complete; reboots deferred

## Scope

I checked the live Proxmox guest list and targeted all twelve running Linux guests: `alpha-prod-01`, `ansible-01`, `app-01`, `docker-blue`, `docker-main`, `docker-network`, `edge-01`, `media-01`, `monitor-01`, `security-01`, `splunk-siem`, and `ubuntu-dev`. Eleven use APT; `splunk-siem` uses DNF. The existing [fleet update inventory](../../Platforms/Ansible/Source/fleet-updates/inventory/hosts.yml) covers eleven of them, so I handled `ubuntu-dev` separately.

I left the powered-off `kali-pen` VM, templates, Windows guests, physical laptops, and Proxmox nodes outside this run. I updated installed host packages within their configured repositories, without a distribution upgrade or a Docker image refresh. Existing package holds remained in place.

## Execution

At 12:50:35 AM EDT I started the deployed `os-update.yml` on `ansible-01` with `target=os_update_targets:!docker-blue:!docker-network`, `reboot=report`, `apt_autoremove=false`, and `apt_autoclean=false`. Its normal serial limit kept package installation to two guests at a time. A transient systemd service kept the process independent of the management connection. I reserved `docker-network` and `docker-blue` for separate runs because they carry the proxy and management services used to reach the fleet.

Before installation I recorded each guest's boot ID, package audit, held packages, root and boot filesystem space, failed units, and container states. `security-01` and `ubuntu-dev` already had reboot flags. Six guests already had failed `openipmi.service` units: `alpha-prod-01`, `ansible-01`, `docker-blue`, `docker-network`, `media-01`, and `monitor-01`; `ubuntu-dev` had the same failure, making seven. `security-01` already had a failed `prometheus-node-exporter.service`. All three Wazuh services, Splunk and SC4S, Caddy and Cloudflared, and Semaphore were running.

The first elevated probes used a here-document that competed with sudo's password input. Three probes returned `sudo: 3 incorrect password attempts`. I changed the probes to pass their Python program as a quoted argument; all twelve elevated checks then succeeded.

## Verification

The main batch ended at 1:19:34 AM EDT, `docker-network` at 1:34:39 AM EDT, `ubuntu-dev` at 1:34:58 AM EDT, and `docker-blue` at 1:36:16 AM EDT. All four runs returned exit code 0. The three Ansible recaps report zero failed and zero unreachable hosts. I ran the two reserved hosts separately with the same playbook options; Ubuntu Dev used `apt-get update` followed by `apt-get --no-remove --with-new-pkgs -y upgrade` with noninteractive configuration handling.

| Guest | Installed or upgraded package entries | Result |
|---|---:|---|
| alpha-prod-01 | 60 | Complete; newer kernel installed |
| ansible-01 | 53 | Complete; Semaphore active |
| app-01 | 70 | Complete; newer kernel installed |
| docker-blue | 69 | Complete; management containers running |
| docker-main | 19 | Complete; application containers running |
| docker-network | 54 | Complete; proxy and NetBird containers running |
| edge-01 | 53 | Complete; newer kernel and Cloudflared binary installed |
| media-01 | 53 | Complete; media containers running |
| monitor-01 | 53 | Complete; 50 of 50 Prometheus targets up |
| security-01 | 74 | Complete; Wazuh central stack upgraded to 4.14.8-1 |
| splunk-siem | 82 | DNF transaction 5 succeeded: 77 upgrades and 5 kernel-package installs |
| ubuntu-dev | 43 | Complete; newer kernel installed |

The APT counts are install and upgrade entries from `dpkg.log` after the run began. DNF also removed five packages from the oldest kernel set under its installed-kernel retention policy; I did not run APT autoremove or autoclean.

I repeated the host checks between 1:39 AM and 1:41 AM EDT. Every guest retained its original boot ID. All eleven APT guests passed `dpkg --audit` and `apt-get check`; Rocky passed `dnf check` and its cached update query returned no available updates. Two queries in the first verification batch did not return usable results, including a 35-second DNF query timeout; both hosts passed on individual retries at 1:41 AM EDT.

Every container that was running in the baseline was running afterward, with no new failed systemd units. Docker Engine reports 29.8.2 on all nine guests with Docker installed. The seven pre-existing `openipmi.service` failures and `security-01`'s pre-existing `prometheus-node-exporter.service` failure remain. The stopped `docusaurus` container and the created `hawser-updater` container on `media-01` were already in those states.

At 1:41 AM EDT I counted 15 active remote Wazuh agents, zero disconnected, and 50 of 50 Prometheus targets up. Wazuh manager, indexer and dashboard were active; their [earlier endpoint checks](../Evidence/Guest%20Package%20Updates%20-%202026-10-02/Exports/post-update-service-checks.json) returned HTTP 401 for the unauthenticated API and indexer and HTTP 302 for the dashboard. These establish endpoint reachability, not an authenticated dashboard test. The Wazuh cluster-health MCP query returned HTTP 400, so I used the local process, endpoint and agent checks for this all-in-one deployment. Splunk, SC4S, Semaphore, Caddy and Cloudflared were active, and `https://mcp.alphasecunited.com` returned HTTP 200 through Nginx Proxy Manager.

Cloudflared now has binary `2026.9.3-3-gad3c6d1c` on disk. Its existing process still reports `2026.8.3-5-g2253eeeb`, with four tunnel connections. I left its restart for the pending Edge 01 reboot.

I retained the four [package-run logs](../Evidence/Guest%20Package%20Updates%20-%202026-10-02/Logs), the [baseline summary](../Evidence/Guest%20Package%20Updates%20-%202026-10-02/Exports/baseline.json), [post-update capture](../Evidence/Guest%20Package%20Updates%20-%202026-10-02/Exports/post-update.json), [final host checks and retries](../Evidence/Guest%20Package%20Updates%20-%202026-10-02/Exports/final-verification.json), and [monitoring and edge checks](../Evidence/Guest%20Package%20Updates%20-%202026-10-02/Exports/service-checks.json). The baseline is a structured summary, not a complete terminal transcript. The detached package logs combine stdout and stderr; their executed scripts and exit codes are included. I compared normalized text hashes with all twelve remote run files before cleanup.

At 1:42:51 AM EDT I removed the nine run files and their directory from `ansible-01`, and the three run files and their directory from `ubuntu-dev`. Both checks confirmed the directories absent and no matching transient run units remaining ([Ansible cleanup](../Evidence/Guest%20Package%20Updates%20-%202026-10-02/Exports/cleanup-ansible-01.json), [Ubuntu Dev cleanup](../Evidence/Guest%20Package%20Updates%20-%202026-10-02/Exports/cleanup-ubuntu-dev.json)). I created no snapshots or backups.

## Open state

I left six VM reboots pending. The Debian guests did not create `/var/run/reboot-required`, but their installed and running kernels differ, so the missing flag does not mean a reboot is unnecessary.

| Guest | Running kernel | Installed kernel awaiting reboot |
|---|---|---|
| alpha-prod-01 | 6.12.107+deb13-amd64 | 6.12.111+deb13-amd64 |
| app-01 | 6.12.107+deb13-amd64 | 6.12.111+deb13-amd64 |
| edge-01 | 6.12.107+deb13-amd64 | 6.12.111+deb13-amd64 |
| security-01 | 6.8.0-138-generic | 6.8.0-146-generic |
| splunk-siem | 6.12.0-211.50.1.el10_2.x86_64 | 6.12.0-211.61.1.el10_2.x86_64 |
| ubuntu-dev | 7.0.0-31-generic | 7.0.0-38-generic |

The LXCs share their Proxmox host kernels. I did not update or reboot the Proxmox nodes. A later reboot window needs service and monitoring checks again after each VM returns.

I preserved all ten existing `wazuh-agent` package holds. The cached APT lists still offered agent 4.14.8-1 on `app-01`, `edge-01` and `ubuntu-dev`, while the other held hosts' cached lists showed no newer candidate. I did not release holds or change repositories. Ubuntu phased updates deferred `sosreport` and `thermald` on `security-01`; its safe-upgrade simulation proposed no installations. Those deferred packages and the agent holds remain outside the completed transaction.
