# ubuntu-dev Storage Expansion

**Created:** 2026-09-28  
**Last updated:** 2026-09-28

I expanded VM 105 `ubuntu-dev` on `grey-server` by 80 GiB, from 150 GiB to 230 GiB, on 2026-09-28 at 2:13 PM Eastern. I extended its root partition and ext4 filesystem online. I did not restart the guest or stop its workloads.

Before the change, `/dev/sda2` was 90% used with 15,422,095,360 bytes available. Grey's NVMe-backed `local-lvm` had 565,253,198 KiB available and was 32.09% used. I checked this through SSH Manager; I did not retain a transcript of the initial host capacity check. The guest preflight and all resize steps are in [Verification.log](../../Evidence/ubuntu-dev%20Storage%20Expansion%20-%202026-09-28/Logs/Verification.log).

I ran `qm disk resize 105 scsi0 230G`. Proxmox reported the volume resized successfully, and Ubuntu saw 246,960,619,520 bytes without a rescan or reboot. A `growpart` dry run confirmed that partition 2 could expand without moving its start or changing the EFI partition. I then ran `sudo -n growpart --update on /dev/sda 2` and `sudo -n /usr/sbin/resize2fs /dev/sda2`; both succeeded.

At 2:14 PM Eastern I verified:

- Proxmox reports `scsi0` as 230G on `local-lvm:vm-105-disk-0`, and VM 105 remains running with a successful guest-agent ping.
- `/dev/sda2` is 245,832,334,848 bytes, mounted read-write as ext4 on `/`.
- `df -h /` reports 225G filesystem capacity, 124G used, 90G available, and 58% usage. The exact available space was 96,537,899,008 bytes.
- Guest uptime increased from 519,847.19 to 519,878.69 seconds across the operation.
- Grey's pool remains active at 32.12% usage with 565,003,491 KiB available. The disk is thin-provisioned, so its virtual growth does not immediately allocate 80 GiB from the pool.

I created no snapshot or backup. Nothing remains open for this expansion. I updated the [VM inventory](../../../../../Operations/Inventory/Galaxy/VMs.md), [Galaxy inventory](../../../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md), and [node record](../../../../Hardware/Nodes.md).
