# Galaxy Incident Report: Blue-Server Duplicate VG

**Created:** 2026-07-31  
**Last updated:** 2026-08-04

## Incident metadata

| Field | Value |
|---|---|
| Incident ID | GLXY-INC-2026-07-30-001 |
| Start | 2026-07-30 23:19:14 EDT, planned Blue shutdown |
| Failure detected | 2026-07-30 23:31:26 EDT, first failed guest start |
| Core services restored | 2026-07-30 23:59:39 EDT |
| Monitoring restored | 2026-07-31 00:02:12 EDT |
| Status | Resolved |
| Severity | SEV-2, service outage |
| Affected node | `blue-server`, 192.168.70.12 |
| Affected services | Prometheus, Grafana, NetBird, Nginx Proxy Manager, RustDesk, Portainer agents, & supporting exporters |

## Summary

Blue booted with two different LVM volume groups named `pve`. The existing Samsung NVMe held the running Proxmox installation and all three LXC root volumes. A newly connected 500 GB WDC SATA disk held an older standalone Proxmox installation with another `pve` VG.

Proxmox identifies `local-lvm` by VG name, so it couldn't choose between the two `pve/data` thin pools. `local-lvm` remained inactive. CT 104 failed autostart, and HA put CT 107 & CT 108 into `error` after four failed start attempts per service.

I renamed the inactive SATA VG by UUID, which restored the NVMe storage without touching its metadata. After confirming the WDC disk's old layout wasn't needed, I deleted its stale LVM layout and GPT. I restarted all three LXCs, cleared both HA error latches, started Prometheus, and verified the workloads.

## Impact

The planned shutdown began at 23:19:14 EDT. Blue rejoined at 23:31:10, but the duplicate VG extended the outage by about 28 minutes for NetBird, Nginx Proxy Manager, & RustDesk and about 31 minutes for Prometheus.

| Asset | Impact |
|---|---|
| CT 104 `monitor-01` | Autostart failed. Grafana, Prometheus, exporters, PeaNUT, & cAdvisor stayed down until the LXC recovered. Prometheus needed one additional manual start. |
| CT 107 `docker-network` | NetBird, Nginx Proxy Manager, Portainer Edge Agent, & cAdvisor stayed down while HA held the service in `error`. |
| CT 108 `docker-blue` | RustDesk `hbbs` and `hbbr`, Portainer Edge Agent, & cAdvisor stayed down while HA held the service in `error`. |
| Galaxy cluster | Four-node quorum remained intact after Blue rejoined. No other node lost storage. |
| Data | No guest data was lost. The three current root volumes stayed on the NVMe thin pool. I destroyed the stale WDC disk layout only after its identity and mount checks passed. |
| Security | I found no credential exposure, unexpected guest relocation, or unauthorized configuration change. |

## Timeline

| Time | Event |
|---|---|
| 2026-07-30 23:19:14 | Blue began a planned poweroff after I added a SATA disk. |
| 23:19:17 through 23:19:33 | Proxmox cleanly stopped CT 104, CT 108, & CT 107. |
| 23:31:10 | The current boot began. Both `/dev/nvme0n1` and the newly visible `/dev/sda` appeared. |
| 23:31:26 | CT 104 autostart failed because `pve/data` was ambiguous. |
| 23:31:36 through 23:32:06 | HA made four failed starts each for CT 107 & CT 108, then set both to `error`. |
| 23:56 | Diagnosis reproduced inactive `local-lvm`, two different `pve` VG UUIDs, and the exact activation error. |
| About 23:58 | I renamed SATA VG UUID `bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj` to `pve-old-sata`; `local-lvm` became active at 11.07 percent used. |
| About 23:58 | CT 104 started. |
| 23:59:19 | Both HA services reached `disabled`, clearing their error latches; I restored desired state `started`. |
| 23:59:39 | HA reported CT 107 & CT 108 `started` on Blue. |
| About 00:00 | After confirming the WDC layout wasn't needed, I removed its stale VG/PV, filesystem signatures, & GPT. |
| 00:02:12 | Prometheus started and returned ready. |
| 00:04:46 | Final storage, quorum, LXC, HA, application, blank-disk, & journal checks passed. |

## Findings

The two physical disks were independent:

| Role | Device | Model | PV UUID | VG UUID |
|---|---|---|---|---|
| Current Proxmox boot and guests | `/dev/nvme0n1p3` | Samsung MZVLW256HEHP-000L7 | `Ka1ZeG-jzer-nW50-Hxzp-CcFD-WFGR-NjIkXG` | `bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e` |
| Stale prior installation | `/dev/sda3` | WDC WD5000LPVX-08V0TT5 | `nzL6Dc-DqiX-D0F0-FqWt-N8Vj-8OQV-5JKmSK` | `bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj` |

The NVMe VG contained `vm-104-disk-0`, `vm-107-disk-0`, & `vm-108-disk-0`. The SATA VG contained only an inactive `root`, `swap`, and empty `data` thin pool.

The previous boot kernel journal contained no WDC or `/dev/sda` discovery and no duplicate-VG warning. The shutdown journal recorded successful `vzshutdown` tasks, not a guest migration. The strict `pin-blue-local-storage` HA rule remained present.

## Root cause

The new SATA disk retained an older Proxmox partition table and LVM layout. Both that layout and Blue's live NVMe installation used the default VG name `pve`.

`/etc/pve/storage.cfg` addresses the current thin pool by `vgname pve` and `thinpool data`, not by VG UUID. Once LVM discovered both disks, Proxmox's activation request became ambiguous and failed with:

```text
activating LV 'pve/data' failed:   Use --select vg_uuid=<uuid> in place of the VG name.
```

The shutdown was the trigger because the next boot was the first one to discover the added disk. It did not create or copy either VG.

## Corrective actions

1. I mapped both PVs, VGs, LVs, mounts, disk identities, guest configs, and task logs.
2. I renamed only the inactive SATA VG by exact UUID to remove the collision without risking the current NVMe VG.
3. I verified `local-lvm active` and all three expected root volumes through Proxmox.
4. I started CT 104.
5. I moved CT 107 & CT 108 through HA state `disabled`, then restored state `started`.
6. I validated the destructive target as the WDC disk with serial suffix `6NSN`, with no mount and stale VG UUID `bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj`.
7. I removed the WDC disk's stale LVs, VG, PV label, filesystem signatures, & GPT. I did not write to `/dev/nvme0n1`.
8. I started the Prometheus container after it remained stopped with exit code 0.
9. I captured SMART data from the now-blank WDC disk and updated the hardware and Galaxy inventories.

## Validation

The final readback at 00:04:46 EDT showed one LVM PV, `/dev/nvme0n1p3`, in one VG named `pve`. `local-lvm` was active at 11.07 percent used. `/dev/sda` had no PTTYPE, filesystem, UUID, mount, or `wipefs` signature.

CTs 104, 107, & 108 were running. HA reported CT 107 & CT 108 `started` on Blue, and the strict pin rule remained listed.

Prometheus returned `Prometheus Server is Ready`. Grafana 13.1.1 returned database `ok`. Nginx Proxy Manager and all three cAdvisor containers with health checks reported healthy; NetBird, RustDesk, Portainer agents, Grafana, PeaNUT, Blackbox Exporter, the Proxmox exporter, Prometheus, & the NUT exporter were running.

The journal returned no activation or duplicate-VG message after 23:58:50 EDT. Galaxy remained quorate with four expected and four total votes.

## Lessons and follow-up

A newly installed disk isn't blank because it isn't mounted. Before the next Proxmox boot with a reused disk attached, I need to inspect `lsblk`, `wipefs`, `pvs`, and `vgs` for retained boot and LVM metadata.

Renaming by VG UUID was the safe first repair. It restored service while preserving the stale disk until I made the destructive decision.

Prometheus retained a stopped state across the interrupted CT boot despite `restart: unless-stopped`. Its configuration already had the desired policy, so I changed no Compose setting. I closed the follow-up on 2026-08-04 after reviewing the controlled 2026-08-01 restart: CT 104 booted at 11:11:33 EDT, and Prometheus started four seconds later with `RestartCount=0`. Docker was enabled and active, and all seven containers were running with `unless-stopped`. The completed check is recorded in the [Prometheus TODO](../../../Platforms/Prometheus/Documentation/TODO.md).

## Closure

GLXY-INC-2026-07-30-001 is resolved. Blue uses the NVMe for its OS, `local-lvm`, & all three LXC root volumes, and `vgs` now lists exactly one volume group named `pve`. CTs 104, 107, & 108 are running and `local-lvm` is active.

The disk that caused the outage turned out to be healthy. It passed a full extended SMART read on 2026-07-31 at 23,215 power-on hours with reallocated, pending, offline-uncorrectable, & CRC-error counts all at 0. It holds no filesystem and no LVM PV, and it carries an empty GPT written by a Proxmox `diskinit` task at 09:10 EDT that day, nine hours after the wipe. The failure was a volume-group name collision, not failing hardware.

The controlled Prometheus restart check completed on 2026-08-01 and was documented on 2026-08-04. No storage repair remains open from this incident.

## Linked records

- [Galaxy troubleshooting record](../../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/Duplicate%20pve%20Volume%20Group%20on%20blue-server%20-%202026-07-30.md)
- [Evidence index](Evidence/Blue%20Server%20Duplicate%20VG%20-%202026-07-30/Evidence-Index.md)
- [Current Galaxy inventory](../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md)
- [Drive inventory](../../../Infrastructure/Hardware/Components/Drives/README.md)
