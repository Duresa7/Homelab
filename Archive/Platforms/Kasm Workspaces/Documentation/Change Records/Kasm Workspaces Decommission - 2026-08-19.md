# Kasm Workspaces Decommission

**Created:** 2026-08-19  
**Last updated:** 2026-08-19

**Date:** 2026-08-19  
**Scope:** Retire Kasm Workspaces, destroy VM 122 and its storage, remove the service's supporting integrations and network path, and archive its records. I kept no backup.

## Starting state

Kasm Workspaces 1.19.0 Community Edition ran as the single-server control plane on `kasm-01`, Proxmox VM 122 on `purple-server`. The guest had six vCPUs, 12 GiB of fixed memory, a 200 GiB `ssd-lvm2` system disk, cloud-init and EFI volumes, and one persistent snapshot named `baseline-parrot-2026-07-30`.

The VM was running with one workspace container and the eight Kasm control-plane containers. `who -u` returned no logged-in shell users. Proxmox reported no replication job and no scheduled backup entry for VM 122. I chose deletion without creating a backup or another snapshot.

The supporting path included a Prometheus node-exporter target and blackbox probe, Wazuh agent 012, an Nginx Proxy Manager proxy host, one internal DNS record, five Kasm VLANs, four session zones, firewall policies and groups, a traffic route through the Kasm Proton VPN client, and the retained SSH Manager profile.

## Step 1: Destroy VM 122

I shut VM 122 down through Proxmox with a 180-second timeout. The graceful shutdown completed, and I destroyed it with `--purge` and `--destroy-unreferenced-disks`.

Proxmox removed `vm-122-cloudinit`, `vm-122-disk-0`, `vm-122-disk-1`, and the EFI and system-disk snapshot volumes associated with `baseline-parrot-2026-07-30`. It also purged VM 122 from related cluster configuration.

The post-delete readback returned no VM 122 configuration, no cluster resource with VMID 122, and no VM 122 volume on `ssd-lvm2`. The pool reported 228.11 GiB total and 0.00 percent used. The old `kasm_01` SSH Manager profile timed out, which is expected until that profile is removed from the connector inventory.

## Step 2: Archive the platform records

I moved the full platform tree from `Platforms/Kasm Workspaces/` to `Archive/Platforms/Kasm Workspaces/`. The archive retains the deployment and workflow records, change plans, dated change records, troubleshooting record, and all three evidence sets. The existing relocation plan already under the archive now sits beside the rest of the Kasm records.

I also archived the isolated-lab architecture and diagrams, the Kasm security assessment and incident, the Kasm-specific UniFi and Proxmox change records, the UniFi network-build evidence, and the Nginx Proxy Manager route record and evidence under their original categories. I repaired their cross-links after the moves.

## Rollback

None. The guest, workspace state, system disk, cloud-init disk, EFI disk, and snapshot volumes were destroyed with no backup. Rebuilding would require a fresh VM and Kasm deployment from the archived records.

## Remaining work

- Remove the Wazuh agent and Prometheus targets.
- Delete the Nginx Proxy Manager route and internal DNS record.
- Remove Kasm from active automation and monitoring configuration.
- Remove the Kasm UniFi policies, networks, zones, traffic route, VPN client, and related objects after the compute teardown.
- Remove stale local and connector artifacts, update all living records, and verify that no active Kasm dependency remains.
