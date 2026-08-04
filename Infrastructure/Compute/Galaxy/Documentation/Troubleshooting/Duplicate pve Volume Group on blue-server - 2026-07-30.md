# Duplicate `pve` Volume Group on `blue-server`

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Investigated:** 2026-07-30 through 2026-07-31  
**Owner:** Galaxy / Proxmox storage  
**Status:** Resolved

## Symptom and impact

`blue-server` booted after a planned shutdown, but `local-lvm` stayed inactive and Proxmox logged this error every 10 seconds:

```text
activating LV 'pve/data' failed:   Use --select vg_uuid=<uuid> in place of the VG name.
```

CT 104 `monitor-01` failed its autostart. HA retried CT 107 `docker-network` and CT 108 `docker-blue` four times each between 23:31:36 and 23:32:06 EDT, then left both services in `error`. Monitoring, NetBird, Nginx Proxy Manager, & the RustDesk relay remained unavailable until I restored the NVMe thin pool and restarted the guests.

## Hypotheses and tests

| Rank | Hypothesis | Test | Result |
|---:|---|---|---|
| 1 | A stale Proxmox system disk introduced a second VG named `pve` | Compare PV, VG, LV, disk, boot, and mount identities | Confirmed. `/dev/sda3` held inactive VG UUID `bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj`; the running system and all three guest volumes were on `/dev/nvme0n1p3`, VG UUID `bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e`. |
| 2 | The shutdown or an HA migration created the duplicate VG | Inspect the previous boot journal and Proxmox task records | Ruled out. The shutdown cleanly stopped CTs 104, 107, & 108. No 2026-07-30 `vzmigrate`, `pvcreate`, or `vgcreate` task created `/dev/sda3`. |
| 3 | LVM saw one physical disk through two device paths | Compare disk serials, PV UUIDs, and VG UUIDs | Ruled out. The Samsung NVMe and WDC SATA disk had different serials, PV UUIDs, and VG UUIDs. |
| 4 | The SATA VG held a current guest disk | List every LV by VG UUID and compare CT rootfs configuration | Ruled out. The SATA VG contained only inactive `root`, `swap`, and `data` LVs. The NVMe VG contained `vm-104-disk-0`, `vm-107-disk-0`, & `vm-108-disk-0`. |

## Root cause

I added a WDC WD5000LPVX-08V0TT5 SATA disk before this boot. The prior boot detected only the Samsung NVMe; the 2026-07-30 boot detected both devices. The WDC disk carried an older standalone Proxmox installation with its own volume group named `pve`.

Blue's current Proxmox installation also uses `pve`, and the `local-lvm` storage entry identifies its thin pool by `vgname pve` and `thinpool data`. LVM found two different VGs with that name and refused the ambiguous activation request. The active root filesystem was never on the WDC disk.

The shutdown exposed the problem because it was the first boot with the SATA disk visible. It did not create the duplicate VG. The existing strict HA rule `pin-blue-local-storage` also remained present, so the HA manager kept CT 107 & CT 108 assigned to Blue instead of repeating the 2026-07-20 config-stranding incident.

## Corrective action

I first renamed only the inactive SATA VG by its exact UUID:

```text
vgrename bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj pve-old-sata
```

That made `pve` unique again. `pvesm status` immediately returned `local-lvm active` at 11.07 percent used and listed the expected 16 GiB, 32 GiB, & 15 GiB LXC root volumes.

I started CT 104 directly. I cleared the HA error latches on CT 107 & CT 108 by setting both to `disabled`, waited for both disabled states, then restored their desired state to `started`.

After I confirmed the newly installed WDC disk was the intended destructive target, I removed `pve-old-sata`, erased its PV and filesystem signatures, destroyed both GPT headers, and refreshed the kernel partition view. The validation guard required the WDC identity with serial suffix `6NSN`, stale VG UUID `bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj`, no mounted path, current VG `pve` on `/dev/nvme0n1p3`, and `/dev/mapper/pve-root` mounted at `/`.

Prometheus had exited cleanly during the shutdown but remained stopped after CT 104 returned despite its `unless-stopped` policy. I started that container once and received `Prometheus Server is Ready`.

## Verification

At 00:04:46 EDT on 2026-07-31:

- `pvesm status` reported `local-lvm active`, 148,086,784 KiB total, & 11.07 percent used.
- `pvs` and `vgs` reported one PV and one VG: `/dev/nvme0n1p3` in `pve`, UUID `bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e`.
- `lsblk` reported `/dev/sda` as a 465.8 GiB WDC disk with no partition table, filesystem, UUID, or mount.
- `wipefs --no-act /dev/sda` returned no signature.
- CTs 104, 107, & 108 were running.
- HA reported CT 107 & CT 108 `started` on Blue; `pin-blue-local-storage` remained present.
- Prometheus returned ready, Grafana reported database `ok`, and every checked monitoring, NetBird, NPM, RustDesk, Portainer, & cAdvisor container was running.
- The boot journal contained no `activating LV`, duplicate `pve`, or multiple-VG entry after 23:58:50 EDT.
- Galaxy remained quorate with four votes.

The WDC drive's SMART capture reported `PASSED`, 23,204 power-on hours, and zero reallocated, pending, offline-uncorrectable, or CRC-error sectors. I left it blank and unallocated.

I ran a full extended SMART test on that drive on 2026-07-31. It completed without error at 23,215 hours with the same four counters at 0, which rules out failing hardware as a contributor here. The [hardware change record](../../../../Hardware/Documentation/Change%20Records/Galaxy%20Green%20and%20Blue%20Hardware%20Changes%20-%202026-07-31.md) carries the result and the disk's current empty-GPT state.

## Related records

- [Galaxy incident report](../../../../../Security/Incidents/Galaxy/Blue%20Server%20Duplicate%20VG%20-%202026-07-30.md)
- [Incident evidence index](../../../../../Security/Incidents/Galaxy/Evidence/Blue%20Server%20Duplicate%20VG%20-%202026-07-30/Evidence-Index.md)
- [Current Galaxy inventory](../../../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md)
- [2026-07-20 HA local-storage stranding](HA%20Local-Storage%20Stranding%20of%20CT%20107%20and%20CT%20108%20After%20a%20Blue-Server%20Shutdown%20-%202026-07-20.md)
