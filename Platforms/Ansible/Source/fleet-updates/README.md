# Fleet Updates

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

I run two playbooks from `ansible-01` to keep the Linux fleet current. `os-update.yml` patches packages through apt or dnf, and `docker-compose-update.yml` pulls new images & recreates the compose stacks. Both use the same `ansible` account, the same key, & the same inventory style as `ssh-key-automation` next door.

## Scope

The inventory holds 10 Linux guests for OS updates & 3 hosts for compose. The four Proxmox nodes & every Windows host are absent on purpose. This automation patches guests, not hypervisors, and apt or dnf can't patch Windows. Keeping the Proxmox nodes out means a run here can never reboot a node that's holding the controller or another guest.

`os_update_targets` covers docker-main, docker-network, alpha-prod-01, app-01, supabase-01, ai-alpha-01, ai-bravo-02, edge-01, security-01, & splunk-siem. Nine run apt; splunk-siem runs dnf on Rocky Linux. The playbook detects which one per host from `ansible_facts.pkg_mgr`, so I don't group hosts by package manager.

`docker_compose_targets` covers docker-main (6 stacks), docker-network (2 stacks), & alpha-prod-01 (6 stacks). app-01 is left out because Coolify owns its containers; a manual `docker compose up -d` would fight Coolify's own reconcile. supabase-01 & the AI hosts aren't in the compose group yet. I add a host only after I confirm its project paths with `docker compose ls`.

## os-update.yml

The play upgrades packages and never reboots unless I tell it to. On apt hosts it refreshes the cache & runs a safe upgrade with autoremove & autoclean. On dnf hosts it runs `name: '*' state: latest`. It sets `NEEDRESTART_MODE=l` so needrestart lists services instead of restarting them mid-run, and `DEBIAN_FRONTEND=noninteractive` so no prompt can hang the play.

Reboot handling is report-only by default. The play checks `/var/run/reboot-required` on Debian & `needs-restarting` on Rocky, using the dnf-utils tool on dnf4 or the `dnf5 needs-restarting --reboothint` subcommand on dnf5. It prints `reboot_required=true` for any host that needs one, and prints `reboot check inconclusive` rather than a false negative when neither tool answers. Pass `-e reboot=auto` to reboot the flagged hosts; that path defaults to one host at a time so a fleet auto-reboot never restarts several guests at once. Override the batch size with `-e os_update_serial=N`.

```bash
cd /home/ansible/fleet-updates
export LANG=C.utf8 LC_ALL=C.utf8

# Preview the whole fleet, change nothing.
ansible-playbook playbooks/os-update.yml --check -K

# Patch the whole fleet, report reboots, reboot nothing.
ansible-playbook playbooks/os-update.yml -K

# Patch one host or group.
ansible-playbook playbooks/os-update.yml -K -e target=splunk-siem
```

The `-K` flag prompts for a sudo password. docker-main connects as `root` and needs no sudo, and docker-network has passwordless sudo, but alpha-prod-01 & app-01 don't, so a fleet run needs `-K`. If a host's sudo password differs from the one typed at the prompt, set that host's `ansible_become_password` from an Ansible Vault file instead of using `-K`. Override the upgrade type with `-e apt_upgrade=full` for a dist-upgrade when I actually want new dependencies pulled in.

## docker-compose-update.yml

The play runs `docker compose pull` then `docker compose up -d` for each stack listed on the host. It uses `community.docker.docker_compose_v2` with `pull: always` & `state: present`, which pulls every image then recreates only the containers whose image or config changed. No sudo runs here: docker-main connects as `root`, and dkadi is in the `docker` group on docker-network & alpha-prod-01.

Each stack is pinned by `project_name` taken from `docker compose ls`, not from the directory name. immich runs as project `immich` out of `/opt/docker/immich-app`, so pinning the name keeps the update on the running project instead of starting a second one called `immich-app`.

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

For OS updates, add the host under `os_update_targets` with its `ansible_host` & `ansible_user`, then confirm the controller key already reaches it. For compose, add the host under `docker_compose_targets` and list its stacks under `compose_projects`, one entry per project with `name` & `project_src`. Get both from `docker compose ls --format json` on the host, using the `Name` field for `name` & the directory of `ConfigFiles` for `project_src`. Run `python3 tests/validate_project.py` and `ansible-playbook --syntax-check` before the first live run.

## Publication note

The copy in this repository uses placeholder usernames: `<YOUR_ADMIN_USERNAME>` for the admin account & `<YOUR_DEPLOYMENT_USER>` for the ai-bravo-02 account. The copy deployed at `/home/ansible/fleet-updates` on `ansible-01` uses the real accounts.

## Semaphore

`semaphore/task-templates.yml` defines an optional web interface with an OS Updates view & a Docker Compose view, each carrying a dry-run template, a full-run template, & a single-target template. Semaphore isn't required; every operation runs from `ansible-playbook` directly. An OS-update run through Semaphore against a host that needs a sudo password requires that password stored as a Semaphore credential.
