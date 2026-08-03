# Ansible

**Created:** 2026-07-14  
**Last updated:** 2026-07-31

I run the reusable Ansible control plane on `ansible-01`. It manages SSH public-key identities across 14 supported hosts, patches 11 running Linux guests through apt or dnf, updates 22 docker compose projects on 6 hosts, manages node_exporter on 9 targets, manages cAdvisor on 8 Docker hosts, and hosts the Galaxy PXE runtime. Semaphore provides 23 task templates across three projects over the same maintenance playbooks.

Fleet package updates include `ansible-01` through Ansible's local connection. The fleet-update inventory excludes `kasm-01` and all five Proxmox nodes.

## Live Deployment

- Controller: `ansible-01` LXC 100, `192.168.40.36`
- Project: `/home/ansible/ssh-key-automation`
- PXE project: `/home/ansible/proxmox-pxe-provisioning`
- Execution account: `ansible`
- Administrative access: `ssh ansible-01` from my workstations
- Ansible: community package 14.2.0 with ansible-core 2.21.2
- Semaphore: 2.18.27 at `https://semaphore.alphasecunited.com` through NPM; direct fallback `http://192.168.40.36:3000`
- Boot behavior: Proxmox starts LXC 100 automatically; systemd starts Semaphore, `galaxy-pxe`, and `tftpd-hpa` inside it
- Source of truth: each Ansible platform project under `Source/`, including its `semaphore/task-templates.yml` manifest; the hosted Galaxy PXE source belongs to `Platforms/Galaxy PXE/`

Semaphore isn't required. Every operation also runs through `ansible-playbook` from the project directory.

## Layout

| Location | Purpose |
|---|---|
| `Source/ssh-key-automation/` | Versioned inventory, identity definitions, playbooks, tests, & Semaphore manifest |
| `Source/fleet-updates/` | OS-update & docker-compose-update playbooks, scoped inventory, validator, & Semaphore manifest |
| `Source/monitoring-exporters/` | node_exporter & cAdvisor playbooks, scoped inventory, validator, & Semaphore manifest |
| `Configuration/semaphore.service` | Deployed systemd unit for Semaphore startup & recovery |
| `Scripts/` | Native Python backup, state-verification, & manifest-reconciliation utilities |
| `Tests/` | Unit tests for the Semaphore reconciler |
| `Documentation/Architecture.md` | How the system fits together |
| `Documentation/Runbook.md` | Commands for audits, onboarding, & future rotations |
| `Documentation/Troubleshooting/` | Issue index & one dated record per operational problem |
| `Documentation/TODO.md` | Platform-owned backlog |
| `Documentation/Change Records/` | Dated implementation history |
| `Evidence/` | Sanitized verification summaries retained beside each change |

## Key Records

- [Architecture](Documentation/Architecture.md)
- [Runbook](Documentation/Runbook.md)
- [Platform TODO](Documentation/TODO.md)
- [Fleet update automation source](Source/fleet-updates/README.md)
- [Monitoring exporter source](Source/monitoring-exporters/README.md)
- [Hosted Galaxy PXE service](../Galaxy%20PXE/README.md)
- [Galaxy PXE provisioning deployment](../Galaxy%20PXE/Documentation/Change%20Records/Galaxy%20PXE%20Provisioning%20Service%20-%202026-07-30.md)
- [SSH identity automation implementation](Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
- [Ansible and Semaphore upgrade](Documentation/Change%20Records/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14.md)
- [Fleet update automation](Documentation/Change%20Records/Fleet%20Update%20Automation%20-%202026-07-20.md)
- [Fleet maintenance](Documentation/Change%20Records/Fleet%20Maintenance%20-%202026-07-28.md)
- [Semaphore & Ansible project parity](Documentation/Change%20Records/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30.md)
- [Dedicated Ansible account and fleet expansion](Documentation/Change%20Records/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25.md)
- [Direct administrative SSH to the controller](Documentation/Change%20Records/Direct%20Administrative%20SSH%20to%20the%20Controller%20-%202026-07-25.md)
- [Internal HTTPS onboarding](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
