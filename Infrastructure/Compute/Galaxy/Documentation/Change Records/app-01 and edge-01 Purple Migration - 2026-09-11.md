# app-01 and edge-01 Purple Migration

**Created:** 2026-09-11  
**Last updated:** 2026-09-25

**Status:** Complete 2026-09-11. Both guests run on Purple; source volumes are removed.

I continued the move after completing app-01's [64 GiB disk replacement](app-01%2064%20GiB%20Boot%20Disk%20Replacement%20-%202026-09-11.md). I moved VM 116 app-01 and VM 121 edge-01 from Grey to Purple, placing both system and EFI disks on Purple's NVMe-backed `local-lvm`. I retain their addresses, VLANs, CPU settings, and memory allocations. The [initial assessment](app-01%20and%20edge-01%20Purple%20Migration%20Assessment%20-%202026-09-10.md) explains the AMD-to-Intel shutdown migration.

## Preflight

At about 2:39 AM Eastern, Purple had no guests, 13,488 MiB available RAM, and an empty 147,714,048 KiB `local-lvm` pool. Galaxy held five votes and quorum. App-01 had a 64 GiB system disk and 4 MiB EFI disk; edge-01 had 30 GiB and 4 MiB. Neither configuration showed an unused disk, passthrough device, or lock in the selected fields.

UniFi reads succeeded. Purple's address `192.168.71.11` appeared on Bane Switch POE port 2 at 1 Gb/s with `Proxmox-Trunk`. That profile excludes five other networks; DMZ/VLAN 30 and SERVERS-A/VLAN 80 are not excluded. Bane port 17 uplinks to Ahsoka Gateway port 6 at 10 Gb/s. Both uplink ends allow all tagged VLANs. Purple's `vmbr0` is VLAN-aware with VLANs 2-4094. I changed no network policy or port setting.

App-01 had seven healthy containers and PostgreSQL accepted connections. A read-only query found no queued or in-progress Coolify deployments. Edge-01's Caddy, cloudflared, guest agent, node exporter, and Wazuh agent services were active, with no failed units; its request to the app dashboard returned HTTP 302. These preflight observations are summarized without a separate raw transcript.

## Execution

I started the app migration at 2:40:49 AM Eastern under `app01-purple-migration-20260911.service` on Grey. It runs a clean shutdown with a 60-second timeout, followed by `qm migrate 116 purple-server --targetstorage local-lvm`. The SSH call timed out while systemd waited for the oneshot job; I checked the existing job rather than starting another. The log reported the VM stopped, migration beginning at 2:41:03 AM, and the EFI volume imported. The system disk copy completed at 2:52:33 AM Eastern with the Proxmox migration task reporting `OK`. When I resumed verification at about 3:22 AM, app-01 was running on Purple with both disks on `local-lvm`, no configuration lock, and about 44 GiB free in its root filesystem. All seven containers were healthy, PostgreSQL accepted connections, and edge-01 received HTTP 302 from the dashboard. Its node exporter was active and Wazuh reported `connected`. These observations are summarized without a separate raw transcript.

At about 3:23 AM Eastern I started `edge01-purple-migration-20260911.service` on Grey. It performs `qm shutdown 121 --timeout 60` followed by `qm migrate 121 purple-server --targetstorage local-lvm`. Shutdown completed and the EFI import succeeded; the 30 GiB system disk subsequently completed. Proxmox reported migration success at 3:28:25 AM Eastern, duration 4 minutes 48 seconds, and removed both source volumes. I started VM 121 on Purple and confirmed it running. Purple had 8,180 MiB available memory and about 127 GiB available in its thin pool before this second move.

## Verification and cleanup

At about 3:29 AM Eastern I verified both VMs running on Purple. Its `local-lvm` holds VM 116's 64 GiB disk, VM 121's 30 GiB disk, and two 4 MiB EFI volumes. The configuration displays each EFI disk as 528K after import, while `pvesm list` reports its allocated volume as 4,194,304 bytes. Neither configuration has a migration lock. Grey's `pvesm list ssd-lvm1 --vmid` returned no volume for either guest.

App-01's seven containers were healthy, PostgreSQL accepted connections, and its root had about 44 GiB free. Edge-01 had Caddy, cloudflared, the guest agent, node exporter, and Wazuh active, no failed units, and about 24 GiB free on root. Both its direct dashboard request and its local Caddy request with `Host: coolify-a1.alphsec.com` returned HTTP 302. Cloudflared registered four connections in the new boot. Prometheus reported app-01's node and cAdvisor targets and edge-01's node target up.

The first guest-agent check reached edge-01 before boot finished and returned `QEMU guest agent is not running`; the subsequent check succeeded. I initially queried the obsolete `prometheus-node-exporter` unit name and got inactive. The running service is `node_exporter.service` using `/usr/local/bin/node_exporter`, now corrected in the service inventory. Direct Wazuh state reads over the ordinary SSH account were denied and passwordless sudo was unavailable, so I read the state through Proxmox's guest agent. Both guests reported `connected`; the manager listed all 16 remote agents active.

A direct HTTP probe from monitor-01 to edge-01 timed out; that cross-VLAN HTTP path was not established as a preflight baseline and I changed no policy to open it. The local proxy test passed. An unauthenticated request from the workstation to `https://coolify-a1.alphsec.com` returned HTTP 403; I did not establish an authenticated public dashboard session. The local application path, tunnel registration, and monitoring checks passed independently.

I stopped both completed transient migration units and deleted `/var/tmp/app01-purple-migration-20260911.log`. Both units read inactive and the temporary file was absent. Grey's `ssd-lvm1` then reported 233,259,098 KiB used (12.15%). Purple's `local-lvm` used 21,950,307 KiB (14.86%), with 125,763,740 KiB available, and its SATA pool remained empty. I summarized the migration, final checks, and cleanup here without retaining a separate raw transcript. No snapshot or backup was created.

The separate [Wazuh manager incident](../../../../../Security/Incidents/Wazuh/Manager%20Processes%20Terminated%20by%20Hash%20Refresh%20-%202026-09-11.md) is closed after fleet verification. A manager process/listener health check remains on the Wazuh backlog.
