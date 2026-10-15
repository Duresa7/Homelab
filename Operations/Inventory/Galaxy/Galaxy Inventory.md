# Galaxy Inventory

**Created:** 2026-07-08  
**Last updated:** 2026-10-15

This index points to the living records that hold Galaxy's current state. On 2026-09-24 the cluster held five nodes, 12 VMs, six LXCs and three templates; 16 guests were running, `kali-pen` and `HQ-WS001` were stopped, and `green-server` held no guests. No guest is an HA resource and there is no shared storage.

## Recent changes

- 2026-10-15: I turned TSO, GSO and GRO off on `nic0` on Purple, Green and Red, then rebooted all three to confirm the setting survives a boot. Red now runs `7.0.14-22-pve`; `media-01` was down for about a minute and a half and came back with working DNS. Purple's `edge-01` and `alpha-prod-01` were down for about two minutes; Minecraft hit its DNS boot race again and needed a restart, and the TeamSpeak boot recovery restored both public paths. `app-01` stays off. [Change record and reboot checks](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md#after-reboot-verification).

- 2026-10-14: Purple's NIC transmit hang interrupted its guest service paths for about 54 minutes and removed Purple from cluster membership for 51 minutes 42 seconds; the other four nodes stayed quorate. I recovered Purple with a physical power cycle on October 15 and verified both guests running, with `app-01` still stopped. LAN/public service checks passed; Minecraft logins were most likely impaired after it started at 12:37 AM until a separate container restart restored external DNS at 12:58:32 AM. [Minecraft DNS persistence](../../../Platforms/Minecraft/README.md#open-items) remains open. [Incident and preventive actions](../../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md).

- 2026-10-11: I increased `alpha-prod-01` to 8 GiB maximum and minimum RAM and Minecraft to a 4 GiB maximum heap with a 5 GiB container limit. I verified the retained world, Minecraft LAN/public responses and both TeamSpeak paths after the VM restart. [Memory increase and verification](../../../Platforms/Minecraft/Documentation/Change%20Records/Memory%20and%20Operator%20Update%20-%202026-10-11.md).

- 2026-10-09: I stopped `app-01` with automatic startup disabled, increased `alpha-prod-01` to 6 GiB maximum and minimum RAM, and deployed Minecraft 26.3 through Dockhand. CPU and disk allocations are unchanged; 15 of the 18 guests are running. [Deployment and verification](../../../Platforms/Minecraft/Documentation/Change%20Records/Deployment%20-%202026-10-09.md).

- 2026-10-07: I repaired the duplicate exporters, unused UPS services, obsolete Grey pool import and six OpenIPMI failures. All ten affected hosts reported `running`; Grey's pool stayed ONLINE and CT 110 stayed running. [Service repairs](../../Maintenance/Service%20Failure%20Repairs%20-%202026-10-07.md).

- 2026-10-06: I rebooted every node except `grey-server` onto kernel 7.0.14-20-pve, and `security-01` and `splunk-siem` onto their waiting kernels; every guest and service came back. [Fleet reboots](../../Maintenance/Fleet%20Reboots%20-%202026-10-06.md).

- 2026-10-05: I upgraded all five nodes to PVE 9.2.21 with kernel 7.0.14-20-pve installed and the node reboots pending, and updated every running Linux guest, Compose project and agent. [Fleet update](../../Maintenance/Fleet%20Update%20-%202026-10-05.md).

- 2026-09-28: I expanded `ubuntu-dev` from 150 GiB to 230 GiB and grew its root filesystem online without a restart. [Storage expansion](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20Storage%20Expansion%20-%202026-09-28.md).

- 2026-09-24: I read the cluster back and recorded four changes the inventories had missed: [CT 107 and CT 108 HA removal](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/CT%20107%20and%20CT%20108%20HA%20Removal%20-%202026-09-24.md), [monitor-01 rootfs at 20 GiB](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/monitor-01%20Rootfs%20at%2020%20GiB%20-%202026-09-24.md), [HQ-WS001 memory at 8 GiB](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/HQ-WS001%20Memory%20at%208%20GiB%20-%202026-09-24.md) and [ubuntu-dev 12 GiB applied](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%2012%20GiB%20Applied%20-%202026-09-24.md).
- 2026-09-23: I moved VM 103 `win11-dev` from Green to Grey. [Migration record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md).
- 2026-09-12: I retired `game-01` and deleted CT 123 with its game data. [Archived guest record](../../../Archive/Operations/Inventory/Galaxy/Game%2001%20Archived%20Guest%20-%202026-09-12.md).

## Current state

| File | Contents |
| --- | --- |
| [Cluster architecture](../../../Infrastructure/Compute/Galaxy/Documentation/Architecture/Cluster%20Architecture.md) | How the five nodes, two Corosync links, storage and firewall fit together |
| [Nodes](../../../Infrastructure/Hardware/Nodes.md) | Node hardware, physical storage, and cluster-storage state |
| [VMs](VMs.md) | QEMU virtual machines and templates |
| [LXCs](LXCs.md) | Linux containers |
| [Services](Services.md) | Workloads, monitoring targets, and service versions |

## Snapshot sequence

The ten dated inventory sets moved to `Archive/Operations/Inventory/Galaxy/Snapshots/` on 2026-09-25; the links below point there, and nothing is added to them.

| Set | Captures | Index |
| --- | --- | --- |
| `- 2026-07-27` | The fleet before the 850 EVO became `ssd-lvm2` | [Galaxy Inventory - 2026-07-27.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20-%202026-07-27.md) |
| `- 2026-07-28` | After moving Kasm VM 122 onto `ssd-lvm2` and expanding `scsi0` to 150G | [Galaxy Inventory - 2026-07-28.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20-%202026-07-28.md) |
| `Post-Kasm Build-Out - 2026-07-28` | After the workspace build-out: 200G disk, VLAN 75, four session lanes | [Galaxy Inventory Post-Kasm Build-Out - 2026-07-28.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20Post-Kasm%20Build-Out%20-%202026-07-28.md) |
| `Post-Parrot - 2026-07-30` | After the controlled Parrot install, image-update control, and replacement snapshot | [Galaxy Inventory Post-Parrot - 2026-07-30.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20Post-Parrot%20-%202026-07-30.md) |
| `Post-PXE - 2026-07-30` | After deploying the Galaxy PXE and TFTP workloads on `ansible-01` | [Galaxy Inventory Post-PXE - 2026-07-30.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20Post-PXE%20-%202026-07-30.md) |
| `Post-Blue SATA Wipe - 2026-07-31` | After adding Blue's WDC disk, resolving its duplicate `pve` VG, and leaving the disk blank | [Galaxy Inventory Post-Blue SATA Wipe - 2026-07-31.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20Post-Blue%20SATA%20Wipe%20-%202026-07-31.md) |
| `Post-Green Expansion - 2026-07-31` | After Green joined as the fifth node, the Blue and Green memory change, and the two extended HDD tests | [Galaxy Inventory Post-Green Expansion - 2026-07-31.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20Post-Green%20Expansion%20-%202026-07-31.md) |
| `- 2026-08-02` | After adding the internal documentation workload on Docker Main | [Galaxy Inventory - 2026-08-02.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20-%202026-08-02.md) |
| `- 2026-08-03` | After deploying Wazuh agents across twelve new endpoints and all five Galaxy nodes | [Galaxy Inventory - 2026-08-03.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20-%202026-08-03.md) |
| `Post-Staleness Audit - 2026-08-03` | After checking current cluster, workload, monitoring, network, media, Portainer, and Wazuh state | [Galaxy Inventory Post-Staleness Audit - 2026-08-03.md](../../../Archive/Operations/Inventory/Galaxy/Snapshots/Galaxy%20Inventory%20Post-Staleness%20Audit%20-%202026-08-03.md) |
