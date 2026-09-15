# Monitoring Exporters

**Created:** 2026-07-25  
**Last updated:** 2026-09-13

I removed retired `game-01` from this project’s active inventory on 2026-09-12 and applied the same removal on `ansible-01`. Its historical deployment details below are retained for context.

I run four playbooks from `ansible-01` to keep Prometheus exporters installed across the fleet. `node-exporter.yml` puts `node_exporter` 1.9.0 on every running Linux guest that lacked it, `cadvisor.yml` manages cAdvisor on all 9 Docker hosts, `textfile-collectors.yml` gives the six hosts on the upstream `node_exporter` binary the textfile collector and its update, reboot and drive scripts, and `wud.yml` runs What's Up Docker on the six Compose hosts. All use the same `ansible` account except for the single-account development workstation and `grey-server`, the same key, & the same inventory style as `fleet-updates` next door. The Semaphore project is declared in `semaphore/task-templates.yml`; it exposes whole-scope & single-host templates for every playbook.

## Scope

`node_exporter_targets` holds 9 hosts: docker-main, docker-network, docker-blue, media-01, alpha-prod-01, splunk-siem, ansible-01, monitor-01, & db-13-dev. The development workstation connects as `ai-agent`; every other remote target uses the dedicated `ansible` account.

Command allowlisting is not achievable for any Ansible-managed account, here or elsewhere. Escalation runs `sudo -u root /bin/sh -c '<token>; python3'` with the module fed on stdin, so a sudoers rule permissive enough for a play to succeed is equivalent to full root, and sudoers wildcards on command arguments are unsafe by design. The controls that actually constrain this account are the `from="192.168.40.36"` restriction on its key, the disabled pty and forwarding, and the empty group list. It deliberately excludes the hosts that already export. The four Proxmox nodes got theirs in the 2026-07-13 baseline cleanup, `edge-01` & `security-01` have had theirs longer, and `app-01` runs a hand-installed `node_exporter.service` binary already bound to 9100. Adding the Debian package there would collide with a working listener, so the playbook leaves it alone and Prometheus just scrapes it.

`ansible-01` manages itself over `ansible_connection: local`, so the controller doesn't depend on its own key sitting in its own `authorized_keys`.

`textfile_collector_targets` holds the six hosts that run the upstream binary rather than Debian's package, because the package brings the collector with it and the binary does not: `grey-server` as root, `docker-main`, `app-01`, `edge-01`, `security-01` and `splunk-siem`. `wud_targets` holds the six Compose hosts: `docker-main`, `docker-network`, `docker-blue`, `media-01`, `alpha-prod-01` and `monitor-01`, each with its own `wud_cron`.

`cadvisor_targets` holds all eight Docker hosts: the six shared targets above plus `app-01` and `security-01`, which run containers but get their `node_exporter` elsewhere. `splunk-siem` is out because it runs Podman, and `ansible-01` because it runs no containers.

## One exporter version, two install methods

Every host ends on `node_exporter` 1.9.0, matching what the four Proxmox nodes already run. The dashboard aggregates across hosts, so a mixed exporter version would mean mixed metric and label sets.

Debian 13 trixie carries `prometheus-node-exporter` 1.9.0-1+b4, so trixie hosts stay APT-managed. Two hosts can't get there through their package manager. `docker-main` runs Debian 12 bookworm, whose only candidate is 1.5.0-1+b6 from December 2022. `splunk-siem` runs Rocky Linux 10.2, which carries no build in `baseos`, `appstream`, or `extras`. Both take the upstream release instead.

The playbook decides per host by reading the APT candidate version, not by looking at the package manager or the distribution release. When `docker-main` eventually moves to trixie, the next run switches it to the package with no edit here.

The upstream download is verified against the release's own `sha256sums.txt`, so no hash is hardcoded and nothing is trusted blind. `grey-server` has run a hand-installed 1.9.0 since before this project existed, so this matches existing practice rather than introducing a new one. I did not add EPEL to `splunk-siem`: pulling a third-party repository onto the host that holds the security logs to obtain one binary isn't a trade worth making.

The `prometheus-node-exporter-collectors` package is present on the package-managed hosts, because it is what Debian's `prometheus-node-exporter` recommends, and `textfile-collectors.yml` installs it on the five apt hosts that run the binary. What the playbook does not do is enable its `smartmon` and `nvme` timers inside a guest: those scripts find no block devices inside an LXC or behind a virtio disk, which would pin `node_textfile_scrape_error` at 1 and report a fault that isn't real. They run on bare metal only, which in this group is `grey-server`. The earlier version of this paragraph said the package was deliberately absent everywhere; that was wrong about the twelve package-managed hosts, which had carried it all along.

## Update and drive metrics come from the textfile collector

The four Grafana update rules read `apt_upgrades_pending`, `dnf_upgrades_pending`, `node_reboot_required` and What's Up Docker's `wud_containers`. The first three are textfiles: Debian's collectors package writes `apt.prom` from `apt_info.py` on a timer, and `splunk-siem` on Rocky gets [dnf-updates-textfile.sh](playbooks/files/dnf-updates-textfile.sh) on a 15-minute timer instead, writing counts by repository, a security count, a check timestamp and a reboot flag derived from the running kernel differing from the newest installed one. Every host in the group gets a systemd drop-in that adds `--collector.textfile.directory=/var/lib/prometheus/node-exporter` to the upstream unit. The collectors package is installed with `install_recommends: false`, because its Recommends pull in `ipmitool` and `openipmi`, and a failing `openipmi.service` on four Lenovo nodes with no management controller is how I learned that.

The play verifies itself by scraping each host and asserting `node_textfile_scrape_error 0`, a package-cache timestamp, and `node_reboot_required`, plus a SMART and an NVMe row on bare metal. It asserts on the timestamp rather than on `apt_upgrades_pending`, because a fully patched host emits no pending rows and `security-01` failed the first version for being up to date.

## What's Up Docker watches images on the Compose hosts

`wud.yml` runs `getwud/wud:latest`, verified as 9.0.2 on 2026-09-13, at `/opt/docker/wud` on each of the six Compose hosts, host port 9102, Docker socket read-only, deletion disabled. Each host's `wud_cron` is twenty minutes from the last, 6:00 AM to 7:40 AM, because Docker Hub allows an anonymous address 100 pulls in six hours and all six hosts share one. `WUD_REGISTRY_HUB_PUBLIC_WATCHDIGEST=true` makes a `:latest` tag on Hub report a new build the way GHCR does by default. The play fails a host that runs containers and registers none, and no stricter than that, because WUD skips digest-pinned images and registries it cannot query.

WUD 9 requires authentication, including for `/metrics`. The playbook generates a distinct `admin` password per host in `/opt/docker/wud/admin.env`, owned by root at mode `0600`, and preserves it on subsequent runs. It copies the matching scrape credential to `monitor-01` under `/home/dkadi/monitoring/prometheus-config/wud-passwords/<host>`, owned by Prometheus UID/GID 65534 at mode `0600` inside a `0700` directory. Credential-handling tasks use `no_log`. I retrieve a UI password from the protected host file when needed; no credential is kept in this repository. Prometheus uses one scrape configuration per host with `basic_auth.password_file`, retaining `job="wud"` through relabeling.

The 2026-09-13 scan also discovered the LinuxServer media images that WUD 8 had skipped. Tag variants still need a container-specific include label: Forgejo limits candidates to its numeric tags, and BookLore's MariaDB only watches rebuilds of its application-supported 11.4.8 pin. Removal is `-e wud_state=absent`. The [maintenance record](../../../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-13.md) covers the WUD 9 migration and verification.

## cAdvisor needs GHCR and v0.60.5 or newer

The image is `ghcr.io/google/cadvisor:latest`, currently resolving to v0.60.5. The registry and that minimum version both matter.

cAdvisor v0.52.1 can't resolve a container's read-write layer ID under Docker 29's default `overlayfs` driver, because it reads the old graphdriver `layerdb` path and the containerd snapshotter doesn't keep one. The lookup happens during registration rather than during collection, so the container is abandoned outright and only the root cgroup is emitted. From 2026-07-25 to 2026-07-26 this project ran cAdvisor on `docker-main` alone for that reason, since `docker-main` was the one host still on `overlay2`.

v0.60.5 handles the snapshotter. It lives on `ghcr.io/google/cadvisor`; `gcr.io/cadvisor/cadvisor` stops at v0.55.1 and never published v0.53.0, v0.54.0, or v0.55.0, which is how I convinced myself for a day that v0.52.1 was current. The original seven hosts reported all 50 containers they ran before I added `monitor-01` as the eighth target. After I moved the five-container monitoring project off `security-01` and started the six-container stack on `monitor-01`, the eight targets reported 51 named containers. Full account in the [troubleshooting record](../../../Prometheus/Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

The playbook no longer asserts on the storage driver, because that assert would have refused the version that fixes the problem. It reports the driver, and after installing it compares the containers cAdvisor registered against the containers Docker says are running, failing the play when a host with containers reports none. That catches this failure and any future one, whatever the cause.

cAdvisor publishes on 9101 instead of the usual 8080. `coolify-proxy` uses 8080 on `app-01`, and the NetBird server uses 8081 on `docker-network`. Port 9101 was available on all eight hosts and sits next to `node_exporter`.

## Running the playbooks

```bash
cd /home/ansible/monitoring-exporters
export LANG=C.utf8 LC_ALL=C.utf8

# Structural check, contacts no host.
python3 tests/validate_project.py

# Preview, change nothing.
ansible-playbook playbooks/node-exporter.yml --check

# Install across the fleet.
ansible-playbook playbooks/node-exporter.yml

# One host.
ansible-playbook playbooks/node-exporter.yml -e target=splunk-siem

# cAdvisor across all eight Docker hosts, then removal from one.
ansible-playbook playbooks/cadvisor.yml
ansible-playbook playbooks/cadvisor.yml -e target=media-01 -e cadvisor_state=absent

# Textfile collectors on the six binary-managed hosts, and What's Up Docker on the six Compose hosts.
ansible-playbook playbooks/textfile-collectors.yml
ansible-playbook playbooks/wud.yml
ansible-playbook playbooks/wud.yml -e target=media-01 -e wud_state=absent
```

Both plays verify their own work. `node-exporter.yml` probes the exporter and asserts the version it reports matches the pinned one, so a silent drift fails the run rather than passing on the package manager's word. `cadvisor.yml` compares the containers cAdvisor registered against the containers Docker reports running, and fails the play on a mismatch instead of warning.

`node-exporter.yml` also refuses to overwrite an unmanaged listener. If something already answers on 9100 and neither the Debian package nor a managed `node_exporter.service` is present, the play stops and asks for `-e allow_port_takeover=true`. That guard exists because of `app-01`.

A `--check` run of `node-exporter.yml` isn't a pass/fail gate. On a binary-managed host, `get_url` predicts the download without creating the staging archive, then `unarchive` & `copy` can't read that missing file. Ansible also skips the `uri` & shell verification modules in check mode, so installed package-managed hosts report an unknown version. I keep that command as a command-line preview of package decisions, but I don't expose it as a Semaphore template that looks like a health check.

The deployed SHA256 matches this repository, and
`python3 tests/validate_project.py` passes with 10 node-exporter hosts, nine
cAdvisor hosts, six textfile-collector hosts and six What's Up Docker hosts. The
`node_exporter_targets` entry for `db-13-dev` at `192.168.40.135` is stale; the
validator pins the set, so removing it is its own change.

## Adding a host

Add it under `node_exporter_targets`, `cadvisor_targets`, `textfile_collector_targets` or `wud_targets` with its `ansible_host` & `ansible_user`, and a `wud_cron` for the last, confirm the controller key already reaches it, then update the matching `EXPECTED_*` set and `EXPECTED_IPS` in `tests/validate_project.py`. The validator is deliberately strict about both host sets so an unreviewed addition fails rather than quietly widening scope.

Scraping the new host also needs a UniFi policy from the collector's zone to the target, and possibly a rule in the Proxmox cluster firewall. Test reachability from the active Prometheus host before adding it to `prometheus.yml`.

## Relationship to fleet-updates

Separate projects on purpose. `fleet-updates` patches packages on 12 guests & updates 24 application Compose projects on a schedule; this project manages node_exporter on 10 targets & cAdvisor on 9 Docker hosts. They share the `ansible` account and inventory style but not their target groups.

The cAdvisor compose project at `/opt/docker/cadvisor` is not in the `fleet-updates` compose inventory, so the monitoring-exporters playbook owns its updates. Its `:latest` tag follows the fleet's floating-image policy; re-running `cadvisor.yml` pulls the tag and reconciles all eight projects. The explicit move from v0.52.1 to v0.60.5 remains the historical fix for Docker's containerd snapshotter.
