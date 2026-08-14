# Debian Dev Archived Guest

**Created:** 2026-08-14  
**Last updated:** 2026-08-14

**Asset:** Galaxy VM 102 `debian-dev`  
**Node:** `grey-server`  
**Archive date:** 2026-08-14  
**Status:** Retired; VM 102 and both disk volumes were deleted on 2026-08-14

## Archived Configuration

I captured this from the live `qm config 102` output and the former active inventory tables before deletion, without dropping the storage, network, or firmware fields.

### Identity

| Setting | Value |
| --- | --- |
| Node | grey-server |
| Guest hostname | debian-dev |
| Role | GNOME development workstation, database test VM, and Docker host |
| High availability | disabled |
| Template | no |
| OS family | Linux |
| Guest OS | Debian GNU/Linux 13.6 (trixie), GNOME Shell 48.7 |
| IPv4 | 192.168.40.135/24 |
| Gateway | 192.168.40.1 |
| Login account | `ai-agent` |
| Snapshot | none |

### Hardware

| Setting | Value |
| --- | --- |
| vCPU | 6 |
| CPU type | host |
| Memory | 16 GiB maximum; 12 GiB minimum |
| Ballooning | on (`balloon: 12288`) |
| BIOS | ovmf |
| Machine | q35 |
| SCSI controller | virtio-scsi-single |
| Display | qxl, 256 MiB |
| QEMU agent | enabled |
| TPM | disabled |

### Storage

| Device | Bus | Storage | Volume | Size | Media | Options |
| --- | --- | --- | --- | --- | --- | --- |
| scsi0 | scsi | ssd-lvm1 | vm-102-disk-1 | 120G | disk | discard, I/O thread, SSD emulation |
| efidisk0 | efidisk | ssd-lvm1 | vm-102-disk-0 | 4M | disk | efitype 4m |

### Network

| NIC | Model | Bridge | VLAN | IPv4 | Gateway | Firewall | MAC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net0 | virtio | vmbr0 | 40 | 192.168.40.135/24 | 192.168.40.1 | enabled | `<REDACTED_DEBIAN_DEV_MAC>` |

### Account & Workload

| Setting | Value |
| --- | --- |
| Administrative account | `ai-agent`, sole login (single-account exception to the baseline standard) |
| Workload | GNOME development workstation; ran CLI Proxy API until it moved to `ubuntu-dev` on 2026-08-13 |
| Successor | `ubuntu-dev` (VM 105), which took over the development-workstation role and the single-account exception |

This final configuration snapshot survives in the archive. It is not a restorable guest backup; this project keeps no snapshots or backups, so none existed when I retired the machine.

## Archival Verification

I queried VM 102 through `grey-server` before archiving it. `qm listsnapshot 102` returned `current` alone, and `pvesh get /cluster/backup`, `/cluster/ha/resources`, and `/cluster/replication` returned no entry naming VMID 102. There was no snapshot, backup job, HA resource, or replication job to reconcile before deletion.

## Retirement Verification

I shut the guest down cleanly with `qm shutdown 102 --timeout 60` and confirmed `qm status 102` read `stopped` before destroying it. `qm destroy 102 --purge` removed logical volumes `vm-102-disk-1` and `vm-102-disk-0` and purged the guest from related configurations. Afterward, `pvesh get /cluster/resources` returned no VMID 102, `/etc/pve/qemu-server/102.conf` did not exist, `pvesm list ssd-lvm1` held no `vm-102-*` volume, and `qm list` showed 9 QEMU VMs with VM 102 absent. The [decommission record](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Decommission%20-%202026-08-14.md) holds the complete command sequence, decisions, and documentation cleanup.

The Proxmox Datacenter firewall, the UniFi client MAC entry, the UniFi firewall policy, the UniFi local DNS record, and the Prometheus scrape target had already been repointed to `ubuntu-dev` during the 2026-08-13 CLI Proxy API migration, ahead of this retirement.

## Preserved Records

- [debian-dev Decommission - 2026-08-14](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Decommission%20-%202026-08-14.md)
- [Galaxy Debian Dev GNOME Installation - 2026-07-15](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15.md)
- [debian-dev Workstation Baseline and Toolchain Build - 2026-08-08](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/debian-dev%20Workstation%20Baseline%20and%20Toolchain%20Build%20-%202026-08-08.md)
- [GNOME Wired Network Indicator Showed a Question Mark on debian-dev - 2026-07-15](../../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/GNOME%20Wired%20Network%20Indicator%20Showed%20a%20Question%20Mark%20on%20debian-dev%20-%202026-07-15.md)
- [Claude Desktop Keyring and KVM Access on debian-dev - 2026-07-15](../../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/Claude%20Desktop%20Keyring%20and%20KVM%20Access%20on%20debian-dev%20-%202026-07-15.md)

## Current-State Cleanup

I removed `debian-dev` from the active Galaxy VM table and detail section, the Galaxy Services inventory and its Wazuh/exporter coverage tables, the root TODO, the Ansible TODO, the Wazuh configuration reference, the Prometheus platform README and guide, the Galaxy Proxmox Cluster guide and Guides index, and the UniFi network/VLAN example device list. I left dated change records, troubleshooting records, and the completed-work log unchanged as history.

Wazuh agent `019` was deregistered from the manager on `security-01` via `manage_agents` on 2026-08-14; `agent_control -l` no longer lists it.
