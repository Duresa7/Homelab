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

The Prometheus configuration in this repository no longer contains the Kasm node-exporter target or blackbox probe. I built the same narrow change against the live configuration, preserved the unrelated `ubuntu-dev` target, validated it with the running Prometheus image, deployed it after approval, and restarted Prometheus. The final API readback returned 50 active targets with all 50 up: 18 node exporters, nine cAdvisor exporters, 19 blackbox probes, two NUT exporters, the Proxmox exporter, and Prometheus itself. No label or scrape URL matched Kasm.

## Step 4: Remove the UniFi dependencies

The live controller inventory found five routed networks (`KASM-BROWSER`, `KASM-TRUSTED`, `MALWARE-OFFLINE`, `LAB-MGMT`, and `EVIDENCE-QUARANTINE`), five same-purpose custom zones, 68 policies that named or referenced them, the `kasm.alphasecunited.com` DNS record, and the `KASM Lab Proton Egress` traffic route. No Kasm firewall group, OON policy, or dedicated port profile existed.

I deleted the 68 policies one at a time through the controller's preview-and-confirm flow. I saved a full policy snapshot before the first deletion and a before-and-after snapshot for every step. Each comparison removed exactly the approved policy. The final firewall inventory contains 64 policies: 57 allows and seven blocks.

I deleted the Kasm DNS record, disabled and deleted its traffic route, and then deleted the five networks. I deleted the five empty zones after their networks were gone. The final controller inventory contains 23 network objects, 11 zones, one traffic route, and 27 enabled DNS records. It also contains 15 firewall groups, 15 client groups, four OON policies, five switch port profiles, and one VPN client.

The ProtonVPN client is shared, so I kept it. The separate `VPN - Proton` route remains enabled with its kill switch on and still targets the retained Proton WiFi network.

The generic `VM` client group contained both `security-01` and the retired Kasm VM by MAC. I removed only the retired member, reducing the group from two members to one. I also used the controller's forget action on the offline `kasm-01` client. UniFi returned success, although its historical-client listing continued to serve the old offline telemetry row with a last-seen time of 10:44 AM Eastern. No current group, policy, route, DNS record, network, zone, OON policy, or port profile references that row.

## Final verification

- Proxmox returns no VM 122 configuration, resource, or storage volume.
- Nginx Proxy Manager has no Kasm proxy host or generated configuration, and `nginx -t` passes.
- Wazuh has no agent 012 or Kasm identity.
- The deployed Ansible projects and SSH Manager profile inventory contain no Kasm target.
- Prometheus reports 50 of 50 targets up and no Kasm target.
- The UniFi configuration readback returns no Kasm match across firewall policies, zones, firewall groups, networks, traffic routes, DNS records, port profiles, VPN clients, client-group names, or OON policies. The `VM` group has one retained member.
- The repository keeps the retired platform and dedicated records under `Archive/`; no active deployment source or configuration references Kasm.

## Rollback

None. The guest, workspace state, system disk, cloud-init disk, EFI disk, and snapshot volumes were destroyed with no backup. Rebuilding would require a fresh VM and Kasm deployment from the archived records.

## Remaining work

None. The controller has accepted the historical-client forget request; the read-only client-history endpoint may retain its unreferenced offline telemetry row until controller retention expires.
