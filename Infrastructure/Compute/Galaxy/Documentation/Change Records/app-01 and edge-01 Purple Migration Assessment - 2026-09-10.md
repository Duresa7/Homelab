# app-01 and edge-01 Purple Migration Assessment

**Created:** 2026-09-10  
**Last updated:** 2026-09-10

I checked moving VM 116 `app-01` and VM 121 `edge-01` from Grey to Purple at about 11:49 PM Eastern on 2026-09-10. I interpreted “app-zero one” as `app-01`, the Coolify host. Both VMs fit Purple's current CPU and memory capacity. I performed read-only checks; neither VM, host, service, nor network configuration changed.

## Live capacity and configuration

I read the configurations, pending settings, migration eligibility, cluster resources, and storage through SSH Manager. Galaxy was quorate with five votes. Both nodes ran `pve-manager/9.2.11/f6997e698c7933ea` and kernel `7.0.14-8-pve`. Purple had no assigned guests.

| Item | app-01 | edge-01 |
|---|---|---|
| Current placement | VM 116 on grey-server | VM 121 on grey-server |
| vCPU | 4 | 2 |
| Memory maximum / balloon minimum | 8 / 4 GiB | 4 / 2 GiB |
| Guest memory used at inspection | 1,398 MiB | 459 MiB |
| System disk | 200 GiB on ssd-lvm1 | 30 GiB on ssd-lvm1 |
| Additional disk | 4 MiB EFI on ssd-lvm1 | 4 MiB EFI on ssd-lvm1 |
| Guest root filesystem used | 14 GiB | 2.2 GiB |
| Source thin-volume allocation | 24.24%, about 48.48 GiB | 26.58%, about 7.97 GiB |
| Retained address | 192.168.80.10/24 | 192.168.30.10/24 |
| Retained network | vmbr0, VLAN 80 | vmbr0, VLAN 30 |

Purple has six Intel i5-8500T cores and 15.46 GiB usable RAM. `free -m` reported 13,449 MiB available and 77 MiB swap occupied. The VMs' combined 12 GiB maximum leaves about 3.46 GiB for the host and virtualization overhead. This fits but leaves limited room for additional guests. The guest readings are a point-in-time observation, not a workload peak study; I propose retaining their existing allocations.

Purple's empty `ssd-lvm2` has 228.11 GiB of data capacity and its empty NVMe-backed `local-lvm` has 140.87 GiB. I would place app-01's system and EFI disks on `ssd-lvm2`, and edge-01's system and EFI disks on `local-lvm`. Putting both on `ssd-lvm2` would overcommit its physical capacity because their virtual system disks alone total 230 GiB. Thin provisioning would not remove that growth limit.

## Migration constraints

Both VMs use `cpu: host`; Grey is AMD Ryzen and Purple is Intel. I would shut each VM down cleanly and migrate it while stopped. Proxmox staff [confirm that cross-vendor live migration is not guaranteed](https://forum.proxmox.com/threads/live-migration-between-intel-and-amd.147990/), even with a generic CPU model. A cold start presents Purple's CPU to the guest; application startup still needs verification.

The read-only migration endpoints for both VMs returned Purple under `not_allowed_nodes` because `ssd-lvm1` is unavailable there. They reported the two local disks per VM and no local passthrough resources. The move must copy both disks and explicitly map the destination storage; a node-only move retaining `ssd-lvm1` cannot work. Neither VM had pending changes, attached installation media, or a configured migration lock in the inspected configuration.

Both nodes have VLAN-aware `vmbr0` with `bridge-vids 2-4094`. Purple's physical uplink reported 1,000 Mbps. I could not finish the live switch-port check: UniFi initially listed Bane Switch POE, then `unifi_list_port_profiles` returned `401 Unauthorized`; the follow-up device lookup returned `Not connected to controller`. Before cutover I need to verify Purple's actual port and every uplink carry VLANs 30 and 80. The retained [port-profile record](../../../../Network/UniFi/Configuration/vpn-networks-port-profiles.md) is supporting history, not a substitute for that check.

## Destination drive condition

I read selected SMART fields without starting a self-test. Both drives returned SMART passed and exit code 0. The Toshiba NVMe reported 30% endurance used, zero media errors, and zero error-log entries. The Samsung 850 EVO reported zero reallocated sectors, uncorrectable errors, and CRC errors, but its normalized `Wear_Leveling_Count` was 12 at 46,308 power-on hours, down from 15 in the [July baseline](../../../../Hardware/Components/Drives/SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-28.txt).

That wear indicator is not a prediction of failure time. It does make the SATA SSD a concern for long-term application storage. I would replace it before making it app-01's permanent home. Edge-01 fits the existing NVMe pool; app-01's current 200 GiB disk exceeds that pool's full capacity, even though the guest presently uses little space. Moving both to NVMe would require a separate disk-layout decision or more capacity.

## Proposed sequence

1. Resolve the SATA storage decision, restore the controller read connection, and verify Purple's physical VLAN path. Recheck capacity and cluster state immediately before starting.
2. Capture service health, stop deployment jobs, shut down app-01 cleanly, migrate VM 116 with both disks mapped to the selected SATA pool, and start it on Purple. Verify SSH, Coolify, Traefik, database/container health, and a published application before moving edge-01.
3. Shut down edge-01 cleanly, migrate VM 121 with both disks mapped to Purple's `local-lvm`, and start it there. Verify SSH, Caddy, cloudflared connectivity, and public routes to both moved and unmoved application hosts.
4. Verify monitoring and security-agent connectivity, retained IPs and VLANs, memory pressure, and final disk ownership. Update the living node, VM, service, and Galaxy inventory records after the move.

App services would be unavailable during VM 116's stop/copy/start. Published routes using edge-01 would be unavailable during VM 121's stop/copy/start. I have not measured transfer throughput and cannot promise an outage duration from guest filesystem usage; source allocated blocks and virtual disk size differ. Purple becoming the host for both guests also makes its failure interrupt both application hosting and ingress to other hosts.

If a VM fails verification after migration, I would inspect its final ownership and disk state before proposing a reverse cold migration to Grey. I would never start duplicate copies with the same identity. I created no backup or snapshot. I retained the measured findings here rather than a raw terminal transcript. Actual migration and its service interruptions remain unapproved.
