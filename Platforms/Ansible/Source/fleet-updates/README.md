# Fleet Updates

**Created:** 2026-07-20  
**Last updated:** 2026-07-29

I run two playbooks from `ansible-01` to keep the Linux fleet current. `os-update.yml` patches packages through apt or dnf, and `docker-compose-update.yml` pulls new images & recreates the compose stacks. Both use the same `ansible` account, the same key, & the same inventory style as `ssh-key-automation` next door.

## Scope

The inventory holds 11 running Linux guests for OS updates & 6 hosts with directly managed compose projects. The four Proxmox nodes, stopped guests, `kasm-01`, & every Windows host are absent on purpose. This automation patches guests, not hypervisors, and apt or dnf can't patch Windows. Keeping the Proxmox nodes out means a run here can never reboot a node that's holding the controller or another guest.

`os_update_targets` covers ansible-01, monitor-01, docker-main, docker-network, docker-blue, media-01, alpha-prod-01, app-01, edge-01, security-01, & splunk-siem. Ten run apt; splunk-siem runs dnf on Rocky Linux. The playbook detects which one per host from `ansible_facts.pkg_mgr`, so I don't group hosts by package manager. `ansible-01` uses a local connection so the controller doesn't depend on an SSH round trip to patch itself. A hostname assertion stops that local entry from patching the wrong runner if someone invokes this copy elsewhere. I keep `kasm-01` outside both plays as requested.

`docker_compose_targets` covers docker-main (6 managed stacks), docker-network (3), docker-blue (2), media-01 (2), alpha-prod-01 (7), & monitor-01 (2). The three 2026-07-28 Portainer Edge Agent projects use `/opt/docker/portainer-edge-agent`. The media project requests the `vpn` profile so the update matches its deployed eight-container topology. cAdvisor stays pinned under the separate monitoring-exporters project, so those eight compose projects aren't duplicated here. app-01 is left out because Coolify owns its two generated projects; a manual `docker compose up -d` would fight Coolify's own reconcile.

## os-update.yml

The play upgrades packages and never reboots unless I tell it to. On apt hosts it refreshes the cache & runs a safe upgrade with autoremove & autoclean. On dnf hosts it runs `name: '*' state: latest`. It sets `NEEDRESTART_MODE=l` so needrestart lists services instead of restarting them mid-run, and `DEBIAN_FRONTEND=noninteractive` so no prompt can hang the play.

Reboot handling is report-only by default. The play checks `/var/run/reboot-required` on Debian. On Rocky it tries the standalone `needs-restarting` helper, the dnf4 `dnf needs-restarting -r` subcommand, & `dnf5 needs-restarting --reboothint`. If none answer, a mismatch between the running and newest installed kernels can still prove that a reboot is needed. A matching kernel alone does not rule out another reason, so the play reports that fallback as inconclusive instead of returning a false negative.

Normal patching runs two guests at a time so concurrent package extraction doesn't saturate the shared guest-storage SSD. Pass `-e reboot=auto` to reboot flagged remote hosts one at a time. That path records the boot ID, schedules the reboot through a transient systemd timer outside the SSH session, waits for the guest to stop answering on TCP 22, waits for SSH to come back, proves the boot ID changed, & allows up to 5 minutes for systemd and startup health checks to settle. The local ansible-01 connection refuses automatic reboot. Override the package or reboot batch size with `-e os_update_serial=N`.

The wait for the SSH listener to drop is there so the reconnect can't race the shutdown. Without it, a guest still answering five seconds after the timer fires lets the reconnect succeed before the reboot starts, and the boot ID check then fails on a guest that reboots correctly. That wait uses a 120-second `reboot_drop_timeout` and never fails the play on its own, because a guest that reboots faster than it samples never looks down. The boot ID comparison is the actual proof.

```bash
cd /home/ansible/fleet-updates
export LANG=C.utf8 LC_ALL=C.utf8

# Preview the whole fleet, change nothing.
ansible-playbook playbooks/os-update.yml --check

# Patch the whole fleet, report reboots, reboot nothing.
ansible-playbook playbooks/os-update.yml

# Patch one host or group.
ansible-playbook playbooks/os-update.yml -e target=splunk-siem

# Patch and reboot one remote host when its check requires a reboot.
ansible-playbook playbooks/os-update.yml -e target=splunk-siem -e reboot=auto
```

Every host connects through the dedicated `ansible` account. Its sudo rule is `NOPASSWD: ALL`, so scheduled runs don't carry a sudo password or stop at an interactive prompt. Override the upgrade type with `-e apt_upgrade=full` for a dist-upgrade when I actually want new dependencies pulled in.

## docker-compose-update.yml

The play runs `docker compose pull` then `docker compose up -d` for each registry-backed stack listed on the host. It uses `community.docker.docker_compose_v2` with `pull: always` & `state: present`, which pulls every registry image then recreates only the containers whose image or config changed. An optional `profiles` list passes deployed compose profiles such as media-01's `vpn` profile. `teamspeak-monitor` sets `pull: never` because its `teamspeak-monitor:local` image is built on alpha-prod-01 and has no registry source; the module still reconciles that project with `up -d`. The module becomes root because several projects protect their `.env` files from non-owner reads.

The module retries a failed registry pull up to three times, then passes `docker compose up -d --wait` with a 180-second default timeout. It returns the full `docker compose ps --all` state for each project, including stopped containers. The play asserts that each project has at least one container, every container is running, & every configured health check is healthy. Its own assertion failure names only the affected containers, not their commands or labels. A successful recap therefore proves both reconciliation & the settled state of every service in the 22 managed projects.

Each stack is pinned by `project_name` taken from `docker compose ls`, not from the directory name. immich runs as project `immich` out of `/opt/docker/immich-app`, so pinning the name keeps the update on the running project instead of starting a second one called `immich-app`.

## Floating image tags are the intended policy

Most managed projects track floating tags rather than fixed versions, and that's deliberate. Taking the newest image is the reason this play exists. On docker-main, booklore, homelab-dashboard-aio, nginx-proxy-manager, & portainer run `:latest`. On monitor-01, the monitoring project runs `prom/prometheus:latest`, `grafana/grafana:latest`, & `prompve/prometheus-pve-exporter:latest`, alongside `prom/blackbox-exporter:v0.28.0` & `hon95/prometheus-nut-exporter:1`. PeaNUT is pinned to `brandawg93/peanut:6.0.0` by digest.

Be clear about what that buys and costs. A scheduled run can land a new major release without me reading its notes first, including on the monitoring stack that watches the rest of the fleet. The `--wait` behavior and the `ps --all` assertion are what catch it: a project whose containers don't come back running and healthy fails the play loudly instead of leaving a half-started stack. What they can't catch is an image that starts cleanly and behaves differently, such as a Grafana major that changes how a datasource or dashboard resolves.

cAdvisor is the deliberate exception and stays out of this project. It's pinned to `ghcr.io/google/cadvisor:v0.60.5` under monitoring-exporters, where a version bump is an explicit edit rather than a scheduled pull.

```bash
cd /home/ansible/fleet-updates
export LANG=C.utf8 LC_ALL=C.utf8

# Preview every stack on every compose host.
ansible-playbook playbooks/docker-compose-update.yml --check

# Update every stack on every compose host.
ansible-playbook playbooks/docker-compose-update.yml

# Update the stacks on one host.
ansible-playbook playbooks/docker-compose-update.yml -e target=docker-main
```

A `--check` run reports `changed=true` for every stack because `pull: always` can't know whether a pull would fetch a newer layer without pulling it. A real run reports `changed` only for stacks whose containers it actually recreated.

## Adding a host

For OS updates, add the host under `os_update_targets` with its `ansible_host` & `ansible_user`, then confirm the controller key already reaches it. For compose, add the host under `docker_compose_targets` and list its stacks under `compose_projects`, one entry per project with `name` & `project_src`. Add `profiles` only when the deployed project requires one or more compose profiles. Get the project name & path from `docker compose ls --format json`, using the `Name` field for `name` & the directory of `ConfigFiles` for `project_src`. Run `python3 tests/validate_project.py` and `ansible-playbook --syntax-check` before the first live run.

## Publication note

The copy in this repository uses `<YOUR_ADMIN_USERNAME>` in workload-owned compose paths on alpha-prod-01 & monitor-01. The copy deployed at `/home/ansible/fleet-updates` on `ansible-01` uses the accounts that own those directories.

## Semaphore

`semaphore/task-templates.yml` defines an optional web interface with an OS Updates view & a Docker Compose view, each carrying a dry-run template, a full-run template, & a single-target template. Semaphore isn't required; every operation runs from `ansible-playbook` directly.
