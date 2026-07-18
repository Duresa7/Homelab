# Ansible

**Created:** 2026-07-14  
**Last updated:** 2026-07-17

This platform owns the homelab's reusable Ansible control plane. The current deployment on `ansible-01` manages SSH public-key identities, while Semaphore provides an optional web interface over the same project.

## Live Deployment

- Controller: `ansible-01` LXC 100, `192.168.40.36`
- Project: `/home/ansible/ssh-key-automation`
- Execution account: `ansible`
- Ansible: community package 14.2.0 with ansible-core 2.21.2
- Semaphore: 2.18.27 at `http://192.168.40.36:3000`
- Boot behavior: Proxmox starts LXC 100 automatically; systemd starts Semaphore inside it
- Source of truth: [SSH identity automation source](Source/ssh-key-automation/README.md)

Semaphore is not required. Every operation can be run directly with `ansible-playbook` from the project directory.

## Layout

| Location | Purpose |
|---|---|
| `Source/ssh-key-automation/` | Versioned inventory, identity definitions, playbooks, tests, and Semaphore manifest |
| `Configuration/semaphore.service` | Deployed systemd unit for Semaphore startup and recovery |
| `Scripts/` | Native Python backup and secret-safe verification utilities |
| `Documentation/Architecture.md` | Simple explanation of how the system fits together |
| `Documentation/Runbook.md` | Commands for audits, onboarding, and future rotations |
| `Documentation/Troubleshooting-Log.md` | Chronological operational problems and fixes |
| `Documentation/TODO.md` | Platform-owned backlog |
| `Documentation/Change Records/` | Dated implementation history |
| `Evidence/` | Command results and retained audit logs |

## Key Records

- [Architecture](Documentation/Architecture.md)
- [Operator runbook](Documentation/Runbook.md)
- [Platform TODO](Documentation/TODO.md)
- [SSH identity automation implementation](Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
- [Ansible and Semaphore upgrade](Documentation/Change%20Records/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14.md)
