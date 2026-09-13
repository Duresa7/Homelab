# Container Image Updates

**Created:** 2026-09-13  
**Last updated:** 2026-09-13

I updated 14 containers across the six Compose hosts after checking the live image-update alert query. The final Prometheus query `wud_containers{update_available="true"}` returned no rows, `up == 0` returned no rows, and all 54 targets were UP. I kept the existing application image tags and database version policy.

## Updates applied

| Service | Host | Verified result |
|---|---|---|
| What's Up Docker | docker-main, docker-network, docker-blue, media-01, alpha-prod-01, monitor-01 | 8.4.0 to 9.0.2; all six healthy with zero restarts after configuration repair |
| Open WebUI | docker-main | New `main` build, still reporting 0.11.3; registry digest `sha256:1a6399d237dc392a2313e0ca826020b3fd5d22536357840eb63393d18dc8b924` |
| CLI Proxy API | docker-main | 7.2.149 to 7.3.0; registry digest `sha256:235cc72d39834d4f9dc012b119253cd56319a8f5aacb25296446f7fb50593ff3` |
| FlareSolverr | media-01 | 3.5.2; image `sha256:c80ae007ce2ccdcd217a12426e4f039ef763ff90738c808d38810c3e59323767` |
| Gluetun | media-01 | New `latest` build at revision `21b46a808147e77a65e86ff5fe9f102759f27ab0`; image `sha256:6bdf70ced4f3ea33b9091f3af7a710b47be003673b6ea94abfeed3343a580d8c` |
| Prowlarr | media-01 | 2.5.2.5491-ls158 to 2.5.2.5491-ls159 |
| qBittorrent | media-01 | 5.2.3_v2.0.14-ls474 to 5.2.3_v2.0.14-ls476 |
| Radarr | media-01 | 6.3.0.10514-ls314 to 6.3.0.10514-ls315 |
| Sonarr | media-01 | 4.0.19.2979-ls322 to 4.0.19.2979-ls324 |

I validated each affected Compose project, pulled the selected services, and reconciled them with `--pull never` to use the images already downloaded. Open WebUI used `--no-deps`; Ollama retained container ID `90628ded73539540d94c8327a0e268e3b9537d61fae90f066cd36fa8809e177b` and restart count zero. I recreated Gluetun and qBittorrent together for the VPN namespace change. The subsequent LinuxServer update recreated qBittorrent with its new image while retaining the new Gluetun namespace.

I reviewed the upstream [Open WebUI](https://github.com/open-webui/open-webui/releases), [CLI Proxy API](https://github.com/router-for-me/CLIProxyAPI/releases), [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr/releases), [Gluetun](https://github.com/passteque/gluetun/releases), and LinuxServer release records before their pulls. The published [WUD changelog](https://getwud.app/docs/changelog/v8/) still described 8.4.0; the actual pulled image reported 9.0.2 and required additional configuration.

## WUD 9 compatibility repair

The first WUD recreation on `docker-blue` failed its health gate and restarted with `Authentication is mandatory: No administrator user found.` I stopped the rollout at that host and inspected the pulled image's bootstrap and HTTP route code. Both administrator bootstrap and authenticated `/metrics` access are mandatory in 9.0.2. `/health` remains unauthenticated.

I changed the [WUD playbook](../../Platforms/Ansible/Source/monitoring-exporters/playbooks/wud.yml) to generate a separate administrator password on each host, preserve it in root-owned mode-0600 `/opt/docker/wud/admin.env`, and load it through Compose `env_file`. The playbook copies each scrape credential through Ansible to `monitor-01`, under `/home/dkadi/monitoring/prometheus-config/wud-passwords/<host>`. Those files belong to UID/GID 65534 at mode 0600 inside a mode-0700 directory. Secret-handling tasks use `no_log`; the repository ignores both credential locations.

The [Prometheus configuration](../../Platforms/Prometheus/Configuration/prometheus-config/prometheus.yml) now uses six separately authenticated scrape configurations. Each reads its own `password_file` and relabels its series to `job="wud"`, preserving existing dashboard and alert queries. Before deployment, the live configuration hash matched the previous repository version. `promtool check config` passed, SIGHUP reloaded it, and `prometheus_config_last_reload_successful` returned 1.

The repaired first host exported metrics successfully. The full six-host deployment then passed, and a second complete playbook run reported `changed=0`, `failed=0`, and `unreachable=0` on every host. The local project validator and remote Ansible syntax check also passed. Every WUD health check later reported healthy with restart count zero.

The new scan found updates for four LinuxServer media images that the previous collector had skipped. I applied those builds and repeated the media checks. WUD now reports 57 containers across the six hosts, compared with 52 before the upgrade; these hosts run 60 containers in total.

## MariaDB tag matching

WUD 9 proposed `110.4.21mariabionic-ls31` as newer than BookLore's supported `11.4.8` dependency. I added a [Compose override](../../Platforms/BookLore/Configuration/docker-compose.override.yml) restricting that container to rebuilds of the exact 11.4.8 tag, with digest watching enabled. The dependency policy comes from the [2026-09-03 update](Container%20Image%20Updates%20-%202026-09-03.md). Future dependency changes must update both the image pin and this label.

I pulled the configured MariaDB tag and recreated only that service to apply the label. MariaDB and BookLore both reported healthy with restart count zero, and BookLore's HTTPS endpoint returned 200. The pinned MariaDB image is `sha256:19afb688f47676ea02b5428963e557ad4473a11790df614cbe3deec7230befb1`. I did not switch database branches to clear an alert.

## Verification and remaining scope

- Open WebUI's direct and HTTPS `/health` endpoints returned 200 with `status=true`; `/api/version` returned 0.11.3. Model discovery from inside the container returned `qwen3.5:2b`.
- CLI Proxy API's root, management page and HTTPS route returned 200. The unauthenticated model endpoint returned 401; an authenticated request returned 200 with 32 models.
- FlareSolverr returned 200 and its 3.5.2 ready response. Jellyfin, Seerr, Sonarr, Radarr and Prowlarr endpoints returned 200 after the final media recreation.
- Gluetun reported healthy, an outbound request through its namespace succeeded, qBittorrent's namespace matched Gluetun's current container ID, and its listen port matched the forwarded-port file. UPnP remained false and the payload filter remained enabled.
- All six authenticated WUD rescans returned 200. After Prometheus scraped the results, the image-update query returned zero rows and all 54 targets were UP. The final six-host inspection found 60 running containers and no unhealthy or starting health checks.

I did not retain standalone terminal captures for these steps; this record contains the observed tool results. Two initial application probes used loopback addresses where the services bind a host address or only a container network; I corrected the probe locations before recording the successful checks. The first forwarded-port probe used `/tmp/gluetun/forwarded_port`; the deployed path is `/gluetun/forwarded_port`.

I created no snapshots or backups and retained no temporary diagnostic container. OS updates and host reboots were outside this Compose-image maintenance. Existing intentional application and database pins remain. The final zero-row result verifies the image-alert input; I did not verify delivery of a resolved notification to Discord or decode Grafana's persisted alert-instance cache.
