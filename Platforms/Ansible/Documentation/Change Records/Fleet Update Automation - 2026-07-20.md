# Fleet Update Automation

**Created:** 2026-07-20  
**Last updated:** 2026-07-25

I built two Ansible playbooks on `ansible-01` to patch the Linux fleet & to update the docker compose stacks, then verified both with dry runs against live hosts without changing a single package or container. The work lives in a new self-contained project, `Platforms/Ansible/Source/fleet-updates`, deployed to `/home/ansible/fleet-updates` beside `ssh-key-automation`.

## Scope

The change adds `os-update.yml`, `docker-compose-update.yml`, a scoped inventory, a project validator, & a Semaphore manifest. The inventory targets 10 Linux guests for OS updates & 3 hosts for compose. It contains no Proxmox node & no Windows host. No target machine was modified in this change; every live run was `--check`.

## Starting state

Before this change, `ansible-01` ran one automation: `ssh-key-automation` for SSH public-key identities. There was no fleet update tooling. OS patching & `docker compose pull` ran by hand, host by host, over SSH. The controller already had `community.docker` 5.2.1, `community.general` 13.2.0, & `ansible.posix` 2.2.2 installed under ansible-core 2.21.2.

## Actions

I probed the fleet read-only first. `docker compose ls --format json` returned the running project name & config-file path per host, `/etc/os-release` gave the package manager, and `sudo -n true` plus `id -nG` told me where the admin account has passwordless sudo & docker-group access. docker-main runs Debian 12; the rest of the apt hosts run Debian 13 or Ubuntu; splunk-siem runs Rocky Linux on dnf.

I authored the project files with sanitized usernames for the repository, built a real-valued copy, uploaded it to grey-server, & pushed it into LXC 100 with `pct push`. I extracted it to `/home/ansible/fleet-updates` owned by the `ansible` account. No collection install was needed because `community.docker` was already present.

I ran an independent review of both playbooks after the first verification. It found four defects, all in the RHEL & auto-reboot paths of `os-update.yml`: the reboot probe assumed dnf4 `needs-restarting` and would report a false negative on Rocky 10's dnf5; the probe was an `ansible.builtin.command` that `--check` skips, so a Rocky dry run defaulted to "no reboot"; `reboot=auto` kept `serial: 100%` and could reboot many guests at once; and the cached `reboot_required` fact stayed true in the final report after a successful reboot. I fixed all four, then re-verified.

## Decisions

I excluded the four Proxmox nodes entirely. They host every VM & LXC, including this controller, so an update run that could reboot the wrong node would strand workloads; CT 107 & 108 already got stranded once on local storage during an HA event. Guests only.

Reboots are report-only by default. The play flags any host whose OS marks a reboot required & reboots nothing unless I pass `-e reboot=auto`. I set `NEEDRESTART_MODE=l` so needrestart lists services rather than restarting them during an apt upgrade. The Rocky reboot probe handles both dnf generations: `needs-restarting -r` on dnf4 & `dnf5 needs-restarting --reboothint` on dnf5, and it reports the check inconclusive rather than a false negative if neither tool answers. The `reboot=auto` path defaults to `serial: 1`, so a fleet auto-reboot restarts one guest at a time.

The OS play auto-detects apt versus dnf from `ansible_facts.pkg_mgr` instead of pre-splitting the inventory, so one host list covers both families. The compose play uses `community.docker.docker_compose_v2` with `pull: always` & `state: present`, which is `docker compose pull` then `up -d`. Each stack is pinned by `project_name` from `docker compose ls`, because immich runs as project `immich` from `/opt/docker/immich-app`; without the pin the module would start a second project named `immich-app`. I left app-01 out of the compose group because Coolify reconciles its own containers.

## Resulting configuration

The project holds `ansible.cfg`, `requirements.yml`, `inventory/hosts.yml`, `playbooks/os-update.yml`, `playbooks/docker-compose-update.yml`, `tests/validate_project.py`, & `semaphore/task-templates.yml`.

`os_update_targets` (10): docker-main, docker-network, alpha-prod-01, app-01, supabase-01, ai-alpha-01, ai-bravo-02, edge-01, security-01, splunk-siem. docker-main connects as `root` with `os_update_become: false`; the rest connect as their admin account & become root.

`docker_compose_targets` (3): docker-main (booklore, forgejo, homelab-dashboard-aio, immich, portainer, termix), docker-network (netbird, nginx-proxy-manager), & alpha-prod-01 (playit-agent, portainer-edge-agent, teamspeak, teamspeak-02, teamspeak-03, ts3-manager). Connection details are inherited from `os_update_targets`; the compose group only attaches each host's `compose_projects` list.

## Verification

`python3 tests/validate_project.py` reported `10 OS-update hosts, 3 compose hosts`. `ansible-playbook --syntax-check` passed for both playbooks. `--list-hosts` returned exactly 10 hosts for os-update & 3 for docker-compose-update, with no Proxmox node & no Windows host in either list.

The os-update dry run against docker-main (`--check --limit docker-main`), re-run after the Codex fixes, gathered facts, passed the package-manager assertion, selected the apt task, skipped the dnf & RHEL-reboot tasks, and honored report-only. Recap: `ok=6 changed=1 unreachable=0 failed=0 skipped=4`. Report line: `docker-main: pkg_mgr=apt changed=True reboot_required=False reboot_policy=report`.

The compose dry run against docker-network (`--check --limit docker-network`) resolved both stacks & ran clean. Recap: `ok=3 changed=1 unreachable=0 failed=0`. The `changed=True` markers are check-mode "would change" reports: apt has real updates pending on docker-main's Debian 12, and `pull: always` always reports would-pull under `--check`. Neither dry run altered a target.

splunk-siem was powered off during this work (no route to 192.168.72.3 from the controller), so I verified the dnf path by syntax check & logic only, not a live dry run. It runs the next time that host is up.

## Rollback points

The project is additive. Deleting `/home/ansible/fleet-updates` removes it with no effect on `ssh-key-automation`, the inventory it uses, or any target host. Because every live run was `--check`, there is nothing to roll back on the fleet.

## 2026-07-25 Follow-up

I closed the unattended privilege gap with one dedicated `ansible` account on the controller and nine running workload guests. The [2026-07-25 account and fleet expansion](Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25.md) records the new 9-host OS scope, 5-host and 16-project Compose scope, restricted controller key, passwordless sudo, & full check-mode verification. The first real fleet update remains operator-initiated because it can install packages, recreate containers, & identify reboot work.
