# Textfile Collectors and What's Up Docker

**Created:** 2026-09-03  
**Last updated:** 2026-09-03

**Implemented:** 2026-09-02  
**Status:** Complete. All 18 hosts publish update metrics, six publish image metrics  
**Affected systems:** the `monitoring-exporters` project on `ansible-01`, the six hosts running the upstream `node_exporter` binary, the six Compose hosts, Prometheus on `monitor-01`

## Change

Two new playbooks in [monitoring-exporters](../../Source/monitoring-exporters/README.md), each with its own inventory group, Semaphore templates and validator coverage. Together they give Grafana the numbers the four Updates alert rules and the three drive-health rules read. Those rules are in [Certificate, Drive Health and Update Alert Rules](../../../Prometheus/Documentation/Change%20Records/Certificate,%20Drive%20Health%20and%20Update%20Alert%20Rules%20-%202026-09-02.md).

### textfile-collectors.yml

The twelve hosts on Debian's `prometheus-node-exporter` package already had the textfile collector, because the package ships `apt_info.py`, a reboot check and the SMART and NVMe scripts on systemd timers, and its unit passes `--collector.textfile.directory`. The six hosts on the upstream binary had none of it: `grey-server` as root, `docker-main`, `app-01`, `edge-01`, `security-01` and `splunk-siem`. They are the new `textfile_collector_targets` group.

On the five apt hosts the play installs `prometheus-node-exporter-collectors` with `install_recommends: false`. Recommends would pull `ipmitool` and `openipmi`, which is how four Lenovo nodes with no management controller came to have a failing `openipmi.service` in the first place, masked on 2026-09-02. The SMART and NVMe timers and `nvme-cli` are enabled only where `ansible_facts.virtualization_role` is `host`, which is `grey-server` alone in this group. Inside a guest those scripts find no drives and only produce a scrape error.

`splunk-siem` runs Rocky Linux and has no such package. It gets a POSIX shell script, [dnf-updates-textfile.sh](../../Source/monitoring-exporters/playbooks/files/dnf-updates-textfile.sh), installed as `/usr/local/sbin/dnf-updates-textfile` and driven by a systemd timer 5 minutes after boot and every 15 minutes after. It writes `dnf_upgrades_pending` by repository, `dnf_security_upgrades_pending`, `dnf_updates_check_timestamp_seconds` and `node_reboot_required`, computed as the running kernel differing from the newest installed one, to `dnf.prom` through a temporary file and a rename so a scrape never reads a half-written file.

Every host in the group gets `/var/lib/prometheus/node-exporter` and a drop-in at `/etc/systemd/system/node_exporter.service.d/textfile.conf` that resets `ExecStart` and re-declares it with `--collector.textfile.directory` added. The play asserts the upstream unit exists first, so it cannot be pointed at a package-managed host by mistake.

The play verifies itself. It scrapes `:9100` on each host and asserts `node_textfile_scrape_error 0`, the presence of `apt_package_cache_timestamp_seconds` or `dnf_updates_check_timestamp_seconds`, and `node_reboot_required`. On bare metal it also asserts a `smartmon_device_smart_healthy` and an `nvme_critical_warning` row. The first version asserted on `apt_upgrades_pending` and failed on `security-01`, which was fully patched and therefore emitted no such row; the timestamp metric is present whether or not anything is pending, so that is what the assertion reads now.

### wud.yml

What's Up Docker 8.3.1 from `getwud/wud`, one container per Compose host at `/opt/docker/wud`, host port 9102 to container port 3000. The six hosts are the new `wud_targets` group: `docker-main`, `docker-network`, `docker-blue`, `media-01`, `alpha-prod-01` and `monitor-01`. It reads the Docker socket read-only, keeps its store in a named volume, and runs with `WUD_SERVER_FEATURE_DELETE=false` so the interface cannot remove a container.

Each host gets its own `wud_cron`, twenty minutes apart from 6:00 AM to 7:40 AM, because Docker Hub allows an anonymous client 100 pulls in six hours per address and all six hosts share one WAN address. `WUD_REGISTRY_HUB_PUBLIC_WATCHDIGEST=true` makes a `:latest` tag on Docker Hub report a new build; GHCR does that by default and Hub does not. The suppress-warning variable stops WUD logging that choice on every run.

The play's guard compares the rows WUD registered against the containers Docker reports running. It first demanded equality and failed, because WUD skips a container whose image is pinned by digest, and one whose registry it cannot query. The guard now fails only when a host with running containers registers nothing.

## Deployment

I synchronised the project to `/home/ansible/monitoring-exporters` on `ansible-01` over a tar stream, since the controller has no `rsync`, and ran both plays from there with `LANG=C.utf8 LC_ALL=C.utf8`. Neither play was run through Semaphore; the templates exist for next time.

Two things had to change outside Ansible before Prometheus could scrape the new port. The UniFi port group `PG-Node-Exporter` gained 9102 alongside 9100 and 9101, which carries it through the four monitoring policies that reference the group, and the one policy that names ports inline, `Allow Monitor to A-Access monitoring`, gained 9102 as well. That is recorded in [Monitoring Ports for What's Up Docker and the Alert Bot](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Monitoring%20Ports%20for%20What's%20Up%20Docker%20and%20the%20Alert%20Bot%20-%202026-09-02.md).

## Verification

- `python3 tests/validate_project.py` passes with the two new groups, the new playbooks and their Semaphore templates.
- Both plays completed with every assertion passing on every host in scope.
- Prometheus reports all 18 `node` targets emitting `node_reboot_required` and a package-cache timestamp. `grey-server` emits SMART rows for its three disks and NVMe rows for its drive. `splunk-siem` reported 116 pending dnf upgrades, 38 of them security, at deploy time.
- Prometheus reports all six `wud` targets up after the UniFi port change, and `wud_containers` series on each.
- At 2:10 AM on 2026-09-03 the fleet stood at 16 hosts with a pending security upgrade, 17 with some pending upgrade, none needing a reboot, and two containers with a newer tag.

No snapshot or backup was taken. Both plays are idempotent and a rebuild from the baseline plus a re-run reproduces the state.

## Known limits

- The WUD interface on port 9102 has no login. Deletion is disabled and the port is reachable only from inside each host's VLAN and from `monitor-01` across VLANs, so the exposure is a read-only view of image names and tags to hosts that already sit beside the containers. I accept that; a reverse-proxy login in front of six instances is more than the page is worth.
- `lscr.io` images are not watched, because LinuxServer's registry requires a GitHub token and I have not issued one. Digest-pinned images are skipped by design. Locally built images produce a `401` in WUD's log on every run, which is noise and not a fault.
- WUD's default tag matching offered `16-rootless` for `forgejo:15`. Containers with variant tags need a `wud.tag.include` label in their own Compose file to narrow the candidates. Forgejo got `wud.tag.include=^[0-9]+$` on 2026-09-03 and now reports `16`; the other five hosts' containers have not needed one yet.
- WUD skips its start-up scan when the store volume is not empty, so a configuration change made through the environment takes effect at the next cron unless `POST /api/containers/watch` is called. I triggered that on `monitor-01` after enabling Hub digest watching; the other five pick it up on their morning run.
- The `node_exporter_targets` group still lists `db-13-dev` at `192.168.40.135`, a workstation that has since been renamed and left the fleet's other inventories. The validator pins that host set, so removing it is its own small change rather than a side effect of this one.
