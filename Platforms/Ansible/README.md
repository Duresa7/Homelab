# Ansible

**Created:** 2026-07-14  
**Last updated:** 2026-07-20

I run the reusable Ansible control plane on `ansible-01`. It manages SSH public-key identities across 15 supported hosts, patches the Linux fleet through apt or dnf, & pulls new images to update the docker compose stacks. Semaphore provides an optional web interface over the same playbooks.

## Live Deployment

- Controller: `ansible-01` LXC 100, `192.168.40.36`
- Project: `/home/ansible/ssh-key-automation`
- Execution account: `ansible`
- Ansible: community package 14.2.0 with ansible-core 2.21.2
- Semaphore: 2.18.27 at `http://192.168.40.36:3000`
- Boot behavior: Proxmox starts LXC 100 automatically; systemd starts Semaphore inside it
- Source of truth: [SSH identity automation source](Source/ssh-key-automation/README.md)

Semaphore isn't required. Every operation also runs through `ansible-playbook` from the project directory.

## Layout

| Location | Purpose |
|---|---|
| `Source/ssh-key-automation/` | Versioned inventory, identity definitions, playbooks, tests, and Semaphore manifest |
| `Source/fleet-updates/` | OS-update & docker-compose-update playbooks, scoped inventory, validator, and Semaphore manifest |
| `Configuration/semaphore.service` | Deployed systemd unit for Semaphore startup and recovery |
| `Scripts/` | Native Python backup and state-verification utilities |
| `Documentation/Architecture.md` | How the system fits together |
| `Documentation/Runbook.md` | Commands for audits, onboarding, and future rotations |
| `Documentation/Troubleshooting-Log.md` | Chronological operational problems and fixes |
| `Documentation/TODO.md` | Platform-owned backlog |
| `Documentation/Change Records/` | Dated implementation history |

## Key Records

- [Architecture](Documentation/Architecture.md)
- [Runbook](Documentation/Runbook.md)
- [Platform TODO](Documentation/TODO.md)
- [Fleet update automation source](Source/fleet-updates/README.md)
- [SSH identity automation implementation](Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
- [Ansible and Semaphore upgrade](Documentation/Change%20Records/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14.md)
- [Fleet update automation](Documentation/Change%20Records/Fleet%20Update%20Automation%20-%202026-07-20.md)
