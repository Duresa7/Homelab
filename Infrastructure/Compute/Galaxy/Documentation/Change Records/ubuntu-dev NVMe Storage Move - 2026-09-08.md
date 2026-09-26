# ubuntu-dev NVMe Storage Move

**Created:** 2026-09-08  
**Last updated:** 2026-09-08  
**Change date:** 2026-09-08

I moved VM 105 `ubuntu-dev` on `grey-server` from the SATA SSD pool `ssd-lvm1` to `local-lvm` on the M.2 NVMe drive. I then removed the two unused source volumes to recover SSD space.

## Storage move

I completed the Proxmox UI move before this verification. The procedure was to connect from another computer, wait for Grey's cloning tasks to finish, shut down VM 105, and use **Hardware → Disk Action → Move Storage** for `scsi0` and then `efidisk0`. I selected `local-lvm` for each and left **Delete source** unchecked before starting the VM again. I have no retained UI task capture for those steps; the live readback below confirms the resulting disk placement.

| Device | Previous volume | Attached volume after move | Size |
| --- | --- | --- | --- |
| `scsi0` | `ssd-lvm1:vm-105-disk-1` | `local-lvm:vm-105-disk-0` | 150 GiB |
| `efidisk0` | `ssd-lvm1:vm-105-disk-0` | `local-lvm:vm-105-disk-1` | 4 MiB |

The destination volume numbers differ from the source. `scsi0` retains discard, I/O thread, and SSD emulation; the EFI disk retains `efitype=4m`. Grey's `pve` volume group sits on `/dev/nvme0n1p3`, on the CT1000P310SSD8 NVMe drive. `ssd-lvm1` sits on `/dev/sda`, the CT2000BX500SSD1 SATA SSD.

## Source removal and verification

At 9:11 AM EDT, I read back VM 105 as running, with both attached disks on `local-lvm`. The retained SSD copies were exactly `unused0: ssd-lvm1:vm-105-disk-1` and `unused1: ssd-lvm1:vm-105-disk-0`. Before deletion, I checked those identities, confirmed no VM configuration lock or other QEMU configuration reference to either source volume, and received a successful QEMU guest-agent ping.

I ran `qm disk unlink 105 --idlist unused0,unused1`. Proxmox reported both logical volumes successfully removed. The follow-up configuration contains neither unused entry, `pvesm list ssd-lvm1 --vmid 105` contains no volumes, and both destination volumes remain on `local-lvm`. VM 105 stayed running and its guest agent responded again. No snapshot or backup was created.

`ssd-lvm1` usage fell from 296,613,421 KiB (15.45%) to 231,147,287 KiB (12.04%), a net reduction of about 62.4 GiB. The deleted volumes had 150 GiB plus 4 MiB of virtual capacity; thin provisioning accounts for the smaller amount of allocated space recovered.

I retained the exact commands, stdout, stderr, and exit codes in [Verification.log](../../Evidence/ubuntu-dev%20NVMe%20Storage%20Move%20-%202026-09-08/Logs/Verification.log). Both remote command batches exited 0. The initial SSH Manager lookup using `grey-server` failed before execution; its configured connection name is `grey_server`.

I verified the running VM, disk placement, source removal, and guest-agent response. Opening desktop files and applications and checking the T3 connection were part of the supplied post-move checklist, but I did not separately capture those checks.

The current disk inventory is in [VMs](../../../../../Operations/Inventory/Galaxy/VMs.md#vm-105---ubuntu-dev), and the physical storage mapping is in [Nodes](../../../../Hardware/Nodes.md).
