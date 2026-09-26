# Ansible

**Created:** 2026-07-14  
**Last updated:** 2026-09-25

I run the reusable Ansible control plane on `ansible-01`. It manages SSH public-key identities on 16 hosts, patches 11 Linux guests through apt or dnf, updates 20 Compose projects on 6 hosts, manages exporters and What's Up Docker across the fleet, owns account and sudo policy through the host access baseline, and hosts the [Galaxy PXE](../Galaxy%20PXE/README.md) runtime. Semaphore puts a web interface over the same playbooks; every operation also runs through `ansible-playbook` from the project directory.

## Current State

| Item | Current value |
|---|---|
| Controller | `ansible-01`, LXC 100 on `blue-server`, `192.168.40.36`, 1 vCPU and 1 GiB |
| Ansible | Community package 14.2.0 with ansible-core 2.21.2 on `PATH`, read 2026-09-24. Debian's `ansible` 12.0.0 and `ansible-core` 2.19.4 packages stay installed underneath as a fallback |
| Semaphore | 2.18.27, systemd unit `semaphore`, SQLite, at `https://semaphore.alphasecunited.com` through Nginx Proxy Manager; direct fallback `http://192.168.40.36:3000` |
| Semaphore content (live, 2026-09-24) | 3 projects, 23 templates: `Server-SSH` 13, `Fleet-Updates` 6, `Monitoring-Exporters` 4; 0 schedules |
| Manifests in `Source/` | 4 projects, 41 templates: `Server-SSH` 17, `Fleet-Updates` 6, `Monitoring-Exporters` 8, `Host-Access-Baseline` 10 |
| Execution account | `ansible`; I reach the controller with `ssh ansible-01` from my workstations |
| Boot | Proxmox starts LXC 100 automatically; systemd starts Semaphore, `galaxy-pxe` and `tftpd-hpa` |

The manifests under `Source/` are meant to be the source of truth, and they are ahead of the live Semaphore database by 18 templates and one project. The four `Ubuntu Dev` identity templates, the textfile-collector and What's Up Docker templates, and the whole `Host-Access-Baseline` project exist only in the manifests. Until I reconcile them, the read-only drift check in the [Runbook](Documentation/Runbook.md) reports those as actions.

Fleet package updates include `ansible-01` itself through Ansible's local connection. No fleet-update playbook targets a Proxmox node.

## Layout

| Location | Purpose |
|---|---|
| `Source/ssh-key-automation/` | SSH identity inventory, identity definitions, playbooks, validator and Semaphore manifest |
| `Source/fleet-updates/` | OS-update and Compose-update playbooks, scoped inventory, validator and Semaphore manifest |
| `Source/monitoring-exporters/` | node_exporter, cAdvisor, textfile-collector and What's Up Docker playbooks, scoped inventory, validator and Semaphore manifest |
| `Source/host-access-baseline/` | `ai-agent` account, account passwords and sudo policy playbooks, validator and Semaphore manifest |
| `Configuration/semaphore.service` | Deployed systemd unit for Semaphore |
| `Scripts/` | Semaphore backup, state-verification and manifest-reconciliation utilities |
| `Tests/` | Unit tests for the Semaphore reconciler |
| `Documentation/Architecture.md` | How the projects, identities and privileges fit together |
| `Documentation/Runbook.md` | Commands for SSH identity audits, onboarding, rotation and the Semaphore drift check |
| `Documentation/Troubleshooting/` | Issue index and one dated record per problem |
| `Documentation/TODO.md` | Platform backlog |
| `Documentation/Change Records/` | Dated implementation history |
| `Evidence/` | Sanitized verification summaries beside each change |

## Open

- `node_exporter_targets` in `Source/monitoring-exporters/inventory/hosts.yml` still lists `db-13-dev`, which is `debian-dev`, decommissioned 2026-08-14. Removing it is its own small change with the validator pin.
- Reconcile or trim the manifests so Semaphore and `Source/` agree.

I moved the controller to Blue on 2026-09-12 ([migration record](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ansible-01%20Blue%20Migration%20-%202026-09-12.md)) and removed retired `game-01` from every inventory the same day.

## Key Records

- [Architecture](Documentation/Architecture.md)
- [Runbook](Documentation/Runbook.md)
- [Platform TODO](Documentation/TODO.md)
- [Fleet update automation source](Source/fleet-updates/README.md)
- [Monitoring exporter source](Source/monitoring-exporters/README.md)
- [Hosted Galaxy PXE service](../Galaxy%20PXE/README.md)
- [Galaxy PXE provisioning deployment](../Galaxy%20PXE/Documentation/Change%20Records/Provisioning%20Service%20-%202026-07-30.md)
- [SSH identity automation implementation](Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
- [Ansible and Semaphore upgrade](Documentation/Change%20Records/Core%20and%20Semaphore%20Upgrade%20-%202026-07-14.md)
- [Fleet update automation](Documentation/Change%20Records/Fleet%20Update%20Automation%20-%202026-07-20.md)
- [Fleet maintenance](Documentation/Change%20Records/Fleet%20Maintenance%20-%202026-07-28.md)
- [Compose fleet maintenance](Documentation/Change%20Records/Compose%20Fleet%20Maintenance%20-%202026-08-31.md)
- [Textfile collectors and What's Up Docker](Documentation/Change%20Records/Textfile%20Collectors%20and%20What's%20Up%20Docker%20-%202026-09-02.md)
- [SSH identity registration for green-server, monitor-01, game-01 and ansible-01](Documentation/Change%20Records/SSH%20Identity%20Registration%20for%20green-server,%20monitor-01,%20game-01%20and%20ansible-01%20-%202026-09-07.md)
- [Semaphore and Ansible project parity](Documentation/Change%20Records/Semaphore%20and%20Ansible%20Project%20Parity%20-%202026-07-30.md)
- [Dedicated Ansible account and fleet expansion](Documentation/Change%20Records/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25.md)
- [Direct administrative SSH to the controller](Documentation/Change%20Records/Direct%20Administrative%20SSH%20to%20the%20Controller%20-%202026-07-25.md)
- [Internal HTTPS onboarding](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
