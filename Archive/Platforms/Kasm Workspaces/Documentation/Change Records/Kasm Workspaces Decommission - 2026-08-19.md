# Kasm Workspaces Decommission

**Created:** 2026-08-19  
**Last updated:** 2026-08-19

**Date:** 2026-08-19  
**Scope:** Retire Kasm Workspaces, destroy VM 122 and its storage, remove the service's supporting integrations and network path, and archive its records. I kept no backup.

## Starting state

Kasm Workspaces 1.19.0 Community Edition ran as the single-server control plane on `kasm-01`, Proxmox VM 122 on `purple-server`. The guest had six vCPUs, 12 GiB of fixed memory, a 200 GiB `ssd-lvm2` system disk, cloud-init and EFI volumes, and one persistent snapshot named `baseline-parrot-2026-07-30`.

The VM was running with one workspace container and the eight Kasm control-plane containers. `who -u` returned no logged-in shell users. Proxmox reported no replication job and no scheduled backup entry for VM 122. I chose deletion without creating a backup or another snapshot.

The supporting path included a Prometheus node-exporter target and blackbox probe, Wazuh agent 012, an Nginx Proxy Manager proxy host, one internal DNS record, five Kasm VLANs, five custom firewall zones, 68 firewall policies, and a Kasm-specific traffic route through the shared ProtonVPN client. The host also remained in deployed Ansible inventories and the SSH Manager profile list.

## Step 1: Destroy VM 122

I shut VM 122 down through Proxmox with a 180-second timeout. The graceful shutdown completed, and I destroyed it with `--purge` and `--destroy-unreferenced-disks`.

Proxmox removed `vm-122-cloudinit`, `vm-122-disk-0`, `vm-122-disk-1`, and the EFI and system-disk snapshot volumes associated with `baseline-parrot-2026-07-30`. It also purged VM 122 from related cluster configuration.

The post-delete readback returned no VM 122 configuration, no cluster resource with VMID 122, and no VM 122 volume on `ssd-lvm2`. The pool reported 228.11 GiB total and 0.00 percent used.

## Step 2: Archive the platform records

I moved the full platform tree from `Platforms/Kasm Workspaces/` to `Archive/Platforms/Kasm Workspaces/`. The archive retains the deployment and workflow records, change plans, dated change records, troubleshooting record, and all three evidence sets. The existing relocation plan already under the archive now sits beside the rest of the Kasm records.

I also archived the isolated-lab architecture and diagrams, the Kasm security assessment and incident, the Kasm-specific UniFi and Proxmox change records, the UniFi network-build evidence, and the Nginx Proxy Manager route record and evidence under their original categories. I repaired their cross-links after the moves.

## Step 3: Remove service and automation integrations

I deleted Nginx Proxy Manager proxy host 23 through its supported API. The host's generated configuration disappeared, no remaining generated file referenced Kasm or its former backend address, and `nginx -t` passed.

I removed disconnected Wazuh agent 012 through the manager's supported `manage_agents` command. Its identity no longer appears in the manager inventory. The inventory now contains the manager identity and 15 endpoint agents.

I removed `kasm-01` from the deployed host-access, monitoring-exporter, and Wazuh deployment inventories on `ansible-01`. I also removed the Kasm-specific exporter explanation and examples from the deployed project documentation. All three inventories parsed with `ansible-inventory`, and a readback found no Kasm name or former address in the active project trees.

I removed the `kasm_01` block from the SSH Manager source configuration. The source file and the loaded connector inventory both returned zero matching profiles afterward.

The Prometheus configuration in this repository no longer contains the Kasm node-exporter target or blackbox probe. I built the same narrow change against the live configuration and validated the candidate with the running Prometheus image. Its deployment remains pending because the deployment safety guard requires separate explicit approval to overwrite the live file; the candidate preserves the unrelated live `ubuntu-dev` target.

## Step 4: Inventory the UniFi dependencies

The live controller inventory found five routed networks (`KASM-BROWSER`, `KASM-TRUSTED`, `MALWARE-OFFLINE`, `LAB-MGMT`, and `EVIDENCE-QUARANTINE`), five same-purpose custom zones, 68 policies that name or reference them, the `kasm.alphasecunited.com` DNS record, and the `KASM Lab Proton Egress` traffic route. No Kasm firewall group, client group, OON policy, or dedicated port profile exists.

The ProtonVPN client is shared: `KASM Lab Proton Egress` targets `KASM-BROWSER`, while the separate `VPN - Proton` route targets the retained Proton WiFi network. I will remove only the Kasm route and keep the shared client and unrelated route.

## Rollback

None. The guest, workspace state, system disk, cloud-init disk, EFI disk, and snapshot volumes were destroyed with no backup. Rebuilding would require a fresh VM and Kasm deployment from the archived records.

## Remaining work

- Deploy the validated Prometheus change after explicit approval and verify that both live Kasm targets disappear.
- Preview, approve, and remove the 68 UniFi policies, DNS record, traffic route, five networks, and five zones. Keep the shared ProtonVPN client and unrelated Proton WiFi route.
- Update the living UniFi records from the final controller readback, run the repository-wide artifact and link sweeps, and record the final verification here.
