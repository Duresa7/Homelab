# ubuntu-dev Storage Expansion

**Created:** 2026-11-09  
**Last updated:** 2026-11-10

I expanded VM 105 `ubuntu-dev` on `grey-server` by 100 GiB, from 230 GiB to 330 GiB, on 2026-11-09 at 12:56 PM Eastern. I extended its root partition and ext4 filesystem online. I did not restart the guest or stop its workloads. This repeats the procedure from the [2026-09-28 expansion](ubuntu-dev%20Storage%20Expansion%20-%202026-09-28.md).

Before the change, `/dev/sda2` was 85% used with 34,850,758,656 bytes available. Grey's NVMe-backed `local-lvm` was 39.78% used with 501,244,995 KiB available, and the thin pool's metadata was 1.53% used. All steps are in [Verification.log](../../Evidence/ubuntu-dev%20Storage%20Expansion%20-%202026-11-09/Logs/Verification.log).

I ran `qm disk resize 105 scsi0 +100G`. LVM resized `pve/vm-105-disk-0` from 58,880 to 84,480 extents, and Ubuntu saw 354,334,801,920 bytes without a rescan or reboot. A `growpart` dry run showed partition 2 keeping its start sector of 2,203,648 and the EFI partition unchanged. I then ran `sudo -n growpart --update on /dev/sda 2` and `sudo -n /usr/sbin/resize2fs /dev/sda2`; both succeeded, and the filesystem is now 86,232,059 4 KiB blocks.

At 12:56 PM Eastern I verified:

- Proxmox reports `scsi0` as 330G on `local-lvm:vm-105-disk-0`, and VM 105 remains running with a successful guest-agent ping.
- `/dev/sda2` is 353,206,517,248 bytes, mounted read-write as ext4 on `/`.
- `df -h /` reports 323G capacity, 182G used, 127G available and 59% usage. The exact available space was 136,239,194,112 bytes.
- Guest uptime increased from 251,975.96 to 251,984.92 seconds across the operation.
- Grey's pool remains active at 39.80% usage with 501,078,523 KiB available. The disk is thin-provisioned, so the extra 100 GiB is not allocated from the pool until the guest writes it.

No restart is needed for this change: the guest saw the larger disk live and ext4 grew while mounted. On 2026-11-10 I read it back with the guest still up at 329,873 seconds, `scsi0` at 330G and `/` at 323G with 189G available. I created no snapshot or backup. I updated the [VM inventory](../../../../../Operations/Inventory/Galaxy/VMs.md), [Galaxy inventory](../../../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md), and [node record](../../../../Hardware/Nodes.md).
