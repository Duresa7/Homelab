# debian-dev Decommission - 2026-08-14

**Created:** 2026-08-14  
**Last updated:** 2026-08-14

**Implementation date:** 2026-08-14  
**Status:** Complete  
**Primary owner:** Infrastructure/Compute/Galaxy (VM 102 `debian-dev`)  
**Affected systems:** Galaxy VM 102 on `grey-server`, this repository's documentation tree

## Scope

`ubuntu-dev` (VM 105) took over as the machine I develop on when CLI Proxy API moved across on 2026-08-13. `debian-dev` (VM 102) sat idle from that point with an empty `/home/ai-agent/docker/` directory, and the Proxmox Datacenter firewall, UniFi client MAC, UniFi firewall policy, UniFi local DNS record, and Prometheus scrape target had already been repointed to `ubuntu-dev` as part of that migration. This record covers what was still outstanding: the Proxmox guest itself and the documentation that treated it as current.

## Starting State

`qm list` on `grey-server` showed VM 102 running at 16 GiB with no snapshot, no backup job, no HA resource, and no replication job configured. `who` on the guest showed a stale console session on `tty2` and several stale SSH sessions from Jedi PC and `ubuntu-dev` itself, none of them running active work. The Proxmox cluster's `pve_admins` IPSet membership for `192.168.40.135` had already been removed during the 2026-08-13 migration; the VM itself, Wazuh agent `019` (enrolled as `db-13-dev`, still registered on the manager), and roughly a dozen documentation references were what remained.

## Decisions

- **Shut down before destroy, not a forced stop.** Nothing was running that needed a clean database or application shutdown, but an ACPI shutdown costs nothing extra and rules out a dirty filesystem state on a disk about to be deleted anyway.
- **`--purge` on the destroy.** It removes the guest from any backup job, replication job, or HA resource membership as part of the same command; the pre-checks below confirmed none existed, so this was a no-op safety net rather than a required step.
- **Archive the four dedicated debian-dev records rather than delete them.** The GNOME installation, the workstation baseline and toolchain build, and two resolved troubleshooting records describe real work with a still-useful narrative (the `nvm`-vs-non-interactive-shell lesson from the toolchain build, in particular, is the same class of problem `ubuntu-dev`'s own Node.js setup now carries). Deleting them would throw away that history for no gain; moving them keeps the active `Documentation/` tree free of dead-host records without losing anything.
- **Deregister the Wazuh manager-side agent record rather than leave it.** Agent `019` reported `Disconnected`, not merely absent, so its stale record would otherwise sit in the manager's agent list indefinitely. I retrieved the account credential from the `Linux Server Standard` 1Password item and ran `manage_agents` on `security-01` to remove it.
- **UniFi is explicitly out of scope for this record.** The controller-side cleanup for `debian-dev` was already completed during the 2026-08-13 migration (client MAC swap, firewall policy repoint, DNS record repoint); this decommission touches Proxmox and this repository only.

## Actions and Observed Results

### Pre-destruction checks

1. `qm listsnapshot 102` returned `current` alone: no snapshot.
2. `pvesh get /cluster/backup`, `/cluster/ha/resources`, and `/cluster/replication` returned no entry naming VMID 102: no backup job, no HA resource, no replication job.
3. `qm status 102` reported `running`.

### Proxmox

4. `qm shutdown 102 --timeout 60` completed a clean ACPI shutdown; `qm status 102` read back `stopped`.
5. `qm destroy 102 --purge` removed logical volumes `vm-102-disk-1` and `vm-102-disk-0` and purged the guest from related configurations.
6. Verification: `pvesh get /cluster/resources` returns no VMID 102. `/etc/pve/qemu-server/102.conf` does not exist. `pvesm list ssd-lvm1` holds no `vm-102-*` volume; its 120 GiB is back. `qm list` shows 9 QEMU VMs, VM 102 absent.

### Documentation

7. Moved four dedicated records to `Archive/Infrastructure/Compute/Galaxy/Documentation/` under matching `Change Records/` and `Troubleshooting/` subfolders: the GNOME installation record, the workstation baseline and toolchain build record, and both resolved troubleshooting records. Corrected each moved file's relative links for the added path depth.
8. Updated the Troubleshooting index to point its two `debian-dev` entries at the archived location rather than a now-missing local path.
9. Removed VM 102's row and detail block from [Galaxy VMs](../../../../../Operations/Inventory/Galaxy/VMs.md) and added a decommission paragraph with the verification above. Guest count corrected from 10 to 9.
10. Removed `debian-dev`'s row and detail section from [Galaxy Services](../../../../../Operations/Inventory/Galaxy/Services.md); corrected the guest count from 15 to 14 and updated the Wazuh coverage note to describe the still-open agent `019` cleanup honestly rather than silently.
11. Updated the root [TODO](../../../../../TODO.md): removed the now-moot Ansible SSH-identity-registration item for `debian-dev`, added agent `019` deregistration as a tracked Wazuh backlog item, and corrected the single-account-exception note to name `ubuntu-dev`.
12. Updated [Ansible TODO](../../../../../Platforms/Ansible/Documentation/TODO.md): replaced the closed `debian-dev` SSH-identity item with the equivalent open item for `ubuntu-dev`.
13. Updated [Wazuh Configuration reference](../../../../../Platforms/Wazuh/Configuration/README.md): marked agent `019`'s row as decommissioned rather than active, added the missing `ubuntu-dev` (`020`) row with its state verified directly on that host, and corrected the `workstation` group's membership description.
14. Updated [Prometheus platform README](../../../../../Platforms/Prometheus/README.md) and the [Prometheus guide](../../../../../Guides/Prometheus.md): the live `node` job's workstation member was already `ubuntu-dev` under `host` label `ubuntu-dev`, not `debian-dev`/`db-13-dev` as the prose still claimed. I verified this directly against `/home/dkadi/monitoring/prometheus-config/prometheus.yml` and the live `/api/v1/targets` response on `monitor-01` before correcting the text; no configuration change was needed there, only the documentation.
15. Updated the [Galaxy Proxmox Cluster guide](../../../../../Guides/Galaxy-Proxmox-Cluster.md) and [Guides index](../../../../../Guides/README.md) to note the VM's retirement without rewriting the historical build walkthrough.
16. Corrected the Personal-A VLAN 40 example device list in [UniFi network/VLAN reference](../../../../Network/UniFi/Configuration/network-vlan.md) from `debian-dev` to `ubuntu-dev`. This is a documentation text correction, not a controller change.
17. Wrote [Debian Dev Archived Guest - 2026-08-14](../../../../../Archive/Operations/Inventory/Galaxy/Debian%20Dev%20Archived%20Guest%20-%202026-08-14.md), the final configuration snapshot and preserved-records index for this guest.

## Verification

| Check | Result |
|---|---|
| `qm listsnapshot 102` (pre-destroy) | `current` alone |
| `pvesh get /cluster/backup` / `/cluster/ha/resources` / `/cluster/replication` (pre-destroy) | No match for VMID 102 in any of the three |
| `qm shutdown 102` | Clean ACPI shutdown; `qm status 102` read `stopped` |
| `qm destroy 102 --purge` | Both logical volumes removed; guest purged from related configurations |
| `pvesh get /cluster/resources` | No VMID 102 |
| `/etc/pve/qemu-server/102.conf` | Does not exist |
| `pvesm list ssd-lvm1` | No `vm-102-*` volume |
| `qm list` | 9 QEMU VMs; VM 102 absent |
| `192.168.40.135` in Proxmox `pve_admins` IPSet | Absent; only `192.168.40.179` (`ubuntu-dev`) present, confirmed live via `pvesh get /cluster/firewall/ipset/pve_admins` |
| CLI Proxy API on `ubuntu-dev` | `docker ps` shows `cli-proxy-api` up; `/home/ai-agent/docker/` on `debian-dev` was already empty before shutdown |
| Ubuntu-dev documentation review | Sudoers drop-in, SSH hardening (six settings), locked root, timezone, locale, cloud-init disabled, Docker/Compose versions, VS Code version, `gh` auth, Node version, and Wazuh agent state all verified directly against the live host and matched the written record; no fabricated claims or embedded secrets found |
| Wazuh agent `019` | Deregistered from the manager on `security-01` via `manage_agents`; `agent_control -l` no longer lists it |

## What I Did Not Do

- **I did not touch UniFi.** The controller-side migration away from `debian-dev` (client MAC, firewall policy, DNS record) was already complete before this record started, and further UniFi work was explicitly out of scope for this decommission.

## Related records

- [Debian Dev Archived Guest - 2026-08-14](../../../../../Archive/Operations/Inventory/Galaxy/Debian%20Dev%20Archived%20Guest%20-%202026-08-14.md)
- [debian-dev Workstation Baseline and Toolchain Build - 2026-08-08](../../../../../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Workstation%20Baseline%20and%20Toolchain%20Build%20-%202026-08-08.md) (archived)
- [Galaxy Debian Dev GNOME Installation - 2026-07-15](../../../../../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15.md) (archived)
- [Galaxy VM inventory](../../../../../Operations/Inventory/Galaxy/VMs.md) and [service inventory](../../../../../Operations/Inventory/Galaxy/Services.md)
- [CLI Proxy API](../../../../../Platforms/CLI%20Proxy%20API/README.md), the workload that moved off this host first
