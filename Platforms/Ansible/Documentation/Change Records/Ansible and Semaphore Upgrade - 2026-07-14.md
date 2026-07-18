# Ansible and Semaphore Upgrade

**Created:** 2026-07-14  
**Last updated:** 2026-07-14

**Implementation date:** 2026-07-14  
**Status:** Complete  
**Primary owner:** Platforms/Ansible  
**Affected systems:** `grey-server`; `ansible-01` LXC 100; Semaphore; SSH identity automation project

## Scope

Upgrade Ansible and Semaphore on `ansible-01` to the latest official releases available on 2026-07-14, preserve recovery points and the existing Semaphore project, and make the controller and web UI return automatically after a Proxmox-node boot. Do not run a key-changing Semaphore task and do not perform Git operations.

## Starting State

- Debian Ansible community package 12.0.0 with ansible-core 2.19.4 was installed through APT.
- Semaphore 2.17.33 ran as a direct process listening on TCP 3000. It had no systemd unit and was an orphaned child of PID 1, so boot recovery was not defined.
- LXC 100 had no `onboot` setting.
- The live Semaphore SQLite database held one project, 18 templates, six views, and one encrypted access key.
- `/root/config.json` and `/root/database.sqlite` were mode 0644 and were tightened during the backup step.

## Release Sources

| Component | Selected release | Official source |
|---|---:|---|
| Ansible community package | 14.2.0 | [PyPI release](https://pypi.org/project/ansible/14.2.0/) |
| ansible-core | 2.21.2 | [PyPI release](https://pypi.org/project/ansible-core/2.21.2/) |
| Semaphore | 2.18.27 | [GitHub release](https://github.com/semaphoreui/semaphore/releases/tag/v2.18.27) |

The Ansible 14.2.0 package declares `ansible-core~=2.21.2`. The official Semaphore Linux AMD64 package was verified against SHA256 `3ebf8b43de63eb4fd0c49b9d694d322bce52aea837908fe73a14c9dcbd60b104` before installation.

## Decisions and Rationale

- Install current Ansible into a versioned virtual environment at `/opt/ansible-14.2.0`. Debian's candidate remained 12.0.0, so the upstream package was required to satisfy the request for the current release.
- Select the runtime through `/opt/ansible-current` and `/usr/local/bin/ansible*` links. This keeps ordinary commands and Semaphore on one runtime while making a future version switch or rollback explicit.
- Retain Debian's older Ansible packages as an emergency fallback instead of removing the last known packaged runtime.
- Upgrade Semaphore with its official `.deb`, verified before installation, rather than replacing the binary from an unverified source.
- Run Semaphore under systemd with restart-on-failure, `C.utf8`, `/opt/ansible-current/bin` first in `PATH`, and `UMask=0077`. The prior direct process had no service manager or boot behavior.
- Enable `onboot: 1` for LXC 100. Ansible itself is a CLI and needs no daemon; automatic startup applies to the controller LXC and Semaphore.
- Validate the controller boot path with a controlled LXC reboot, but do not reboot the entire Proxmox node solely for this change. The LXC reboot proves systemd and Semaphore recover from a real controller boot; Proxmox's persisted `onboot` setting is the authoritative node-boot policy.

## Actions and Observed Results

1. Read the installed versions, APT candidates, Semaphore process model, database counts, and LXC boot configuration.
2. Created `/root/semaphore-backups/upgrade-2026-07-14` with root-only permissions. Saved the pre-upgrade configuration, an SQLite online backup, Semaphore 2.17.33 binary, package inventory, Ansible Python package inventory, verified 2.18.27 installer, and checksums.
3. Changed the live Semaphore configuration and SQLite database to mode 0600. Database contents were not printed or stored in repository evidence.
4. Installed `python3.13-venv`, built `/opt/ansible-14.2.0`, installed Ansible 14.2.0 with ansible-core 2.21.2, and selected it through `/opt/ansible-current` plus `/usr/local/bin` command links.
5. Verified the Semaphore 2.18.27 package checksum, installed it, gracefully stopped the unmanaged 2.17.33 process, deployed `semaphore.service`, and enabled and started the unit.
6. Set Proxmox LXC 100 to `onboot: 1`.
7. Refreshed and verified the backup manifest, checked both SQLite databases, validated HTTP and systemd state, ran the project validator, and syntax-checked all five operator playbooks.
8. Deployed the reusable backup and secret-safe state-verification Python utilities under `/opt/homelab/ansible-tools` from the repository's native `Scripts/` sources.
9. Compared the live database with the pre-upgrade online backup. Project, repository, inventory, template, view, environment, access-key metadata, encrypted key material, and environment payloads were unchanged. Semaphore 2.18.27 added 18 expected template-to-environment links during migration.
10. Rebooted LXC 100. Its boot ID changed, Semaphore returned automatically as an enabled systemd service with zero restarts, the UI returned HTTP 200, and the current-boot journal contained no warning-or-higher entries.

## Resulting Configuration

| Item | Result |
|---|---|
| Ansible | Community 14.2.0; ansible-core 2.21.2 |
| Selected runtime | `/opt/ansible-current` → `/opt/ansible-14.2.0` |
| Semaphore | Package and binary 2.18.27 |
| Semaphore service | `enabled`, `active`, zero restarts at final verification |
| UI health | HTTP 200 on `127.0.0.1:3000` |
| LXC boot | `hostname: ansible-01`; `onboot: 1` |
| Semaphore objects | One project, 18 templates, six views, one access key |
| Native maintenance tools | `/opt/homelab/ansible-tools`; source in `Platforms/Ansible/Scripts/` |
| Live and backup SQLite integrity | `ok` |
| Secret-bearing file modes | Configuration and live database 0600; backup directory 0700 |

## Verification

| Check | Observed result |
|---|---|
| Runtime selection | `ansible`, `ansible-community`, and `ansible-playbook` resolve into `/opt/ansible-14.2.0/bin` |
| Ansible versions | Community 14.2.0; core 2.21.2 |
| Semaphore versions | Binary and Debian package 2.18.27 |
| Service persistence | systemd `enabled` and `active`; `NRestarts=0` |
| Controller persistence | Proxmox reports `onboot: 1` for LXC 100 |
| Controller reboot | Boot ID changed; Semaphore automatically returned enabled/active with HTTP 200 |
| Web response | HTTP 200 on TCP 3000 |
| Database | Live and backup `PRAGMA integrity_check` returned `ok`; object counts preserved |
| Semaphore preservation | Secret-safe structure, environment payloads, and encrypted access-key records matched the pre-upgrade backup |
| Recovery files | Every file in `SHA256SUMS` returned `OK` |
| Project validator | Exit 0: four identities, 15 supported hosts, two unknown hosts, 18 templates |
| Playbook syntax | Audit, Stage, Verify, Retire, and Onboard passed |
| Managed-host smoke test | Read-only Mac audit completed on all four Proxmox nodes with `changed=0`, `unreachable=0`, and `failed=0` |
| Semaphore logs | No warning-or-higher journal entries during the upgrade window |

No Semaphore task was launched and no authorized key was added, removed, or rotated during this upgrade.

## Rollback

1. Stop `semaphore.service` and prevent operators from launching tasks.
2. Restore `/root/config.json`, `/root/database.sqlite`, and the saved 2.17.33 binary from `/root/semaphore-backups/upgrade-2026-07-14` if Semaphore rollback is required.
3. Repoint `/opt/ansible-current` and `/usr/local/bin/ansible*` to a retained runtime. If necessary, remove only the `/usr/local/bin` shadow links to expose Debian's retained `/usr/bin` packages.
4. Start Semaphore, verify SQLite integrity and HTTP 200, then rerun the project validator and syntax checks before resuming use.
5. Disable LXC auto-start only if intentionally reverting the boot policy: `pct set 100 -onboot 0` on the owning Proxmox node.

## Remaining Work

None required for the requested upgrade and boot persistence. The controller LXC was rebooted successfully. A full Proxmox-node reboot was intentionally not introduced solely as a test; persisted `onboot: 1` is the Proxmox node-boot control.

## Step Evidence

| Step | Evidence | Verification |
|---|---|---|
| S01 | [Discovery and backups](../../Evidence/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14/Logs/S01-Discovery-And-Backups-2026-07-14.md) | Starting versions, process model, object counts, permissions, and rollback copies recorded |
| S02 | [Upgrades and boot persistence](../../Evidence/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14/Logs/S02-Upgrades-And-Boot-Persistence-2026-07-14.md) | Versioned Ansible runtime, verified Semaphore package, systemd unit, and LXC onboot applied |
| S03 | [Post-upgrade verification](../../Evidence/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14/Logs/S03-Post-Upgrade-Verification-2026-07-14.md) | Versions, service, HTTP, databases, backups, project, playbooks, and boot configuration passed |
| S04 | [Boot and preservation verification](../../Evidence/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14/Logs/S04-Boot-And-Preservation-Verification-2026-07-14.md) | Controlled LXC reboot, automatic service return, native tools, and unchanged encrypted project state verified |
