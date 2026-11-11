# Guest Disk Shrink

**Created:** 2026-11-11  
**Last updated:** 2026-11-11

**Change date:** 2026-11-11  
**Target:** VMs 109 `splunk-siem`, 200 `security-01`, 301 `HQ-DC01`, 302 `HQ-DC02`, 303 `HQ-MGT01` and 310 `HQ-WS001`, all on `grey-server`'s `ssd-lvm1`

## Outcome

I lowered six guests' system disks before I migrate them, because an offline move streams the whole virtual disk and not just the blocks in use.

| VM | Before | After | Used in the guest afterwards |
|---|---|---|---|
| 109 `splunk-siem` | 150G | 100G | 65G of 92G |
| 200 `security-01` | 100G | 64G | 30G of 62G |
| 301 `HQ-DC01` | 80G | 48G | 20.5G of 46.7G |
| 302 `HQ-DC02` | 80G | 48G | 20.5G of 46.7G |
| 303 `HQ-MGT01` | 100G | 64G | 21.6G of 62.7G |
| 310 `HQ-WS001` | 80G | 64G | 26.5G of 62.7G |

Each guest booted on its smaller disk and passed its checks, and I removed every rollback snapshot once it had. `HQ-DC02`, `HQ-MGT01` and `HQ-WS001` were stopped before the work and are stopped again. `HQ-DC01`, `security-01` and `splunk-siem` are running.

Splunk did not index from about 1:58 PM to about 2:37 PM, and again for about a minute from 2:41 PM. Syslog that SC4S would have received in those windows was not received. Wazuh was down from 1:44 PM to 1:54 PM.

`ssd-lvm1` is thin, so the old sizes were ceilings and not allocations. The pool was 13.07% used before and 12.66% after, with 1,676,777,747 KiB available. The space that matters for the migration is the smaller ceiling.

## Sizing

| VM | Used before | Why this size |
|---|---|---|
| `security-01` | 30G | 13G of that is the Wazuh vulnerability feed in `/var/ossec/queue/vd/feed`, which roughly doubles while a feed update writes its replacement. 64G leaves about 30G free. |
| `HQ-DC01`, `HQ-DC02` | 20.9G and 20.5G | Windows reported a minimum C: of 23.5G and 25.1G. 48G leaves room for cumulative updates. |
| `HQ-MGT01` | 27.6G | 64G. |
| `HQ-WS001` | 26.8G | 64G is Windows 11's own minimum disk size. |
| `splunk-siem` | 66G on `/`, 39G of it Splunk indexes | The index caps add up to about 48 GiB plus the uncapped default index. 100G leaves `/` at 91.5G. |

## Method

Proxmox has no disk shrink, so every guest followed the same order: make the guest's last partition end below the new size, shut the guest down, take a `preshrink` snapshot, cut the thin LV on Grey, then rebuild the backup GPT at the new end of the disk. The scripts are in [Scripts/guest-disk-shrink](../../Scripts/guest-disk-shrink/).

`host-cut.sh` refuses to cut unless the VM is stopped and the last partition ends at least 1 MiB below the target. It then runs `qm snapshot <vmid> preshrink`, `lvreduce --fs ignore -L <size>g`, `sgdisk -e` to move the backup GPT header, `sgdisk -v`, and `qm rescan`. On every disk `sgdisk` first warned that the backup header was invalid, which is expected because the backup sat past the new end. After `-e`, `sgdisk -v` returned `No problems found` each time.

### Windows guests

On each Windows guest a recovery partition sat after C:, so C: could not shrink past it. `win-shrink.ps1` follows Microsoft's KB5028997 method and runs as SYSTEM through `qm guest exec`:

1. `reagentc /disable`, which stages `Winre.wim` back to `C:\Windows\System32\Recovery`. The script stops if the file is not there.
2. `diskpart` `delete partition override` on the recovery partition.
3. `Resize-Partition -DriveLetter C` to the target, less 1 GiB for recovery and 1 MiB of tail.
4. A new 1 GiB recovery partition directly after C:, formatted NTFS, type `de94bba4-06d1-4d40-a16a-bfd50179d6ac`, attributes `0x8000000000000001`.
5. `reagentc /enable`.

The old recovery partitions were 870 MiB on both DCs, 1,023 MiB on `HQ-MGT01` and 886 MiB on `HQ-WS001`. Each is now 1,024 MiB, which leaves the small ones more room for WinRE servicing updates.

On `HQ-WS001`, the first run failed at step 4: diskpart rejects a partition type GUID wrapped in braces, `The arguments specified for this command are not valid`. C: had already shrunk and the old recovery partition was gone, so WinRE stayed disabled. `reagentc /enable` then refused because C: is BitLocker-encrypted and WinRE would have landed on C:. I fixed the GUID in the script and created the recovery partition with `win-fixrec.ps1`, then `reagentc /enable` placed WinRE on `partition4`. The other three Windows guests ran the corrected script cleanly.

I did `HQ-DC02` before `HQ-DC01` and left `HQ-DC02` running while `HQ-DC01` was down, so the domain always had a DC.

### security-01

The root filesystem is ext4 on `/dev/sda2` with no LVM, and ext4 cannot shrink while mounted. `ext4-cut.sh` did the work on Grey with the VM stopped, through `losetup -P` on the LV:

1. `e2fsck -f -p` returned clean. It listed 17 `extent tree could be shorter` hints, which are optimisations and not errors.
2. `resize2fs` to 1 GiB below the new partition size.
3. `sfdisk -N 2` rewrote partition 2 with its start sector 2,203,648, its type and its partition UUID `72CED9A5-6BD1-429C-823E-0F634E7C6902` unchanged and a size of 132,012,032 sectors.
4. `resize2fs` grew the filesystem to fill the partition, then `e2fsck -f -n` returned clean with 309,091 files in 16,501,504 4 KiB blocks.
5. The cut, as above.

The filesystem UUID `9c093835-5606-4608-8b74-5613c97e2f61` that `/etc/fstab` mounts by did not change.

### splunk-siem

The root filesystem is XFS on LVM, and XFS cannot shrink at all. The 150G disk held `/boot/efi` on `sda1` (600 MiB), `/boot` on `sda2` (2 GiB) and the PV of volume group `rl` on `sda3`, with `rl/root` at 141.54G and `rl/swap` at 5.87G. Root had 66G in use. I built a new 100G disk and copied root onto a smaller filesystem.

1. I stopped `sc4s`, `unifi-flow-collector` and `Splunkd`, then took the `preshrink` snapshot at 1:59 PM with the guest agent freezing the filesystem.
2. I hot-added a blank 100G `scsi1` (`vm-109-disk-2`). `splunk-copy.sh` checked it was 100 GiB and blank, partitioned it with the same starts and types as the old disk, renamed the running VG `rl` to `rl_old`, and created a new `rl` on `/dev/sdb3` with `swap` at the old size and `root` at 91.54G. `mkswap -U` reused the old swap UUID `22959ff4-00d5-41f6-8e7b-0454fa5ada7b`, which the kernel `resume=` argument and `/etc/fstab` name.
3. `xfsdump -l 0 -J - / | xfsrestore -J - /mnt/newroot` ran from 1:59 to 2:33 PM. The dump was 67,400,280,248 bytes in 1,863 seconds, and both sides reported `SUCCESS`. `du --apparent-size` measured 64,009 MiB on both roots. xfsrestore placed one unreferenced inode in `/orphanage`. It was an empty file created at 2:28 PM during the dump, and I deleted it and the directory.
4. In the copy I pointed `/etc/fstab`'s `/` entry at the new filesystem UUID `06515b70-7ba8-4d2c-b7b8-9c61e0c69cbf`. I deleted `/etc/lvm/devices/system.devices`, which named the old PV by `/dev/sda3` and its PVID, so LVM would scan for the new PV. I ran `restorecon` on `fstab` and rebuilt all three kernels' initramfs with `dracut -f --regenerate-all` in a chroot. `/etc/shadow` kept `shadow_t` and `fstab` kept `etc_t`, so the SELinux labels came across.
5. With the VM shut down, `splunk-cutover.sh` on Grey copied partitions 1 and 2 by offset from the old LV to the new one, and `cmp` found both identical. It then gave the new disk the old disk GUID `A6650221-1CC6-4CB1-8873-AE3F684B1004` and the old partition GUIDs. The GRUB stub on the ESP finds `/boot` by filesystem UUID `50d36fee-27a9-43a1-b79e-3edcaad3659c`, which the byte copy kept. I kept the partition GUIDs because a UEFI boot entry names the ESP by its partition GUID; the ESP also carries the fallback `EFI/BOOT/BOOTX64.EFI`. It copies by offset rather than through `losetup -P`, so the guest's PV on partition 3 never appeared as a block device on Grey, where LVM could have activated `rl` or `rl_old` on the host. It then made `vm-109-disk-2` the `scsi0` and left the old disk as `unused0`.
6. After the first boot I recreated the devices file with `vgimportdevices -a`. It holds one entry, `IDTYPE=devname IDNAME=/dev/sda3`, with the new PVID. I rebuilt the initramfs again and did a second clean shutdown and start, so the state I left is the state that booted.
7. I removed the snapshot and destroyed the old 150G `vm-109-disk-1` with `qm disk unlink 109 --idlist unused0 --force`.

The ISO in `ide2` that the inventory listed was no longer attached.

## Verification

| VM | Checks after boot on the new disk |
|---|---|
| `HQ-WS001` | Disk 0 at 64 GiB, healthy. `Repair-Volume -Scan`: `NoErrorsFound`. WinRE enabled on `partition4`. Still joined to `ad.alphasecunited.com`. No disk, NTFS, volmgr or partmgr errors in the System log since boot. |
| `HQ-MGT01` | Disk 0 at 64 GiB, healthy. `NoErrorsFound`. WinRE enabled on `partition4`. Still joined. No storage errors since boot. |
| `HQ-DC02` | Disk 0 at 48 GiB, healthy. `NoErrorsFound`. WinRE enabled. NTDS, DNS, Netlogon, KDC, W32Time and DFSR running. `dcdiag /q` for Services, Advertising, FsmoCheck, NetLogons, SysVolCheck, Replications and KnowsOfRoleHolders printed nothing. `repadmin /showrepl` showed all five naming contexts from `HQ-DC01` with 0 failures, last success 1:36 to 1:37 PM. |
| `HQ-DC01` | Same checks as `HQ-DC02`, all passing. All five naming contexts from `HQ-DC02` with 0 failures, last success 1:41 to 1:42 PM. |
| `security-01` | `/` is 62G with 30G used. `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard` and `filebeat` active, and `systemctl --failed` empty. No ext4 or I/O errors in `dmesg`. `fstrim -v /` trimmed 32.3 GiB. 15 agents active, the same as before the shutdown. `hawser`, `cadvisor` and `wazuh-mcp-server` healthy. The dashboard answered `302` to its login page. |
| `splunk-siem` | Checked after both boots. `/` is `/dev/mapper/rl-root`, XFS, 92G with 65G used and 28G free. `rl` is the only VG, on the 97.41G `sda3`. Swap is on. SELinux enforcing, and `ausearch -m avc -ts boot` found no denials. `Splunkd`, `sc4s`, `unifi-flow-collector`, `rsyslog` and `node_exporter` active. Listening on TCP 514, 601, 8000, 8088, 8089, 9997 and 9100 and UDP 514 and 601. `splunk status`: `splunkd is running`. 150 hot-bucket files written in the first minutes after the first boot. The SC4S container's first health check after each boot fails because it runs before syslog-ng is up; its next run two minutes later passed and the container reported `healthy` with no failed units left. |

## Timeline

Times are Eastern, from Grey's task log.

| Time | Event |
|---|---|
| 1:17 PM | Started `HQ-WS001` |
| 1:20 PM | Shut down `HQ-WS001`, snapshot, cut to 64G, booted to verify |
| 1:24 PM | Shut down `HQ-WS001` and removed its snapshot. Started `HQ-MGT01` |
| 1:28 to 1:29 PM | Shut down `HQ-MGT01`, snapshot, cut to 64G, booted to verify |
| 1:32 PM | Shut down `HQ-MGT01` and removed its snapshot. Started `HQ-DC02` |
| 1:34 to 1:35 PM | Shut down `HQ-DC02`, snapshot, cut to 48G, booted to verify |
| 1:38 PM | Removed `HQ-DC02`'s snapshot, left it running |
| 1:40 to 1:41 PM | Shut down `HQ-DC01`, snapshot, cut to 48G, booted to verify |
| 1:44 PM | Removed `HQ-DC01`'s snapshot. Shut down `HQ-DC02`. Shut down `security-01` and took its snapshot |
| 1:53 PM | Started `security-01` after the filesystem shrink and cut |
| 1:56 PM | Removed `security-01`'s snapshot |
| 1:58 PM | Stopped `sc4s`, `unifi-flow-collector` and `Splunkd` on `splunk-siem` |
| 1:59 PM | Took `splunk-siem`'s snapshot and added the new 100G disk. The copy started |
| 2:33 PM | The copy finished |
| 2:35 PM | Shut down `splunk-siem`, ran the cutover, started it on the new disk |
| 2:39 to 2:40 PM | Recreated the LVM devices file and rebuilt the initramfs |
| 2:41 PM | Second clean shutdown and start of `splunk-siem` |
| 2:42 PM | Removed `splunk-siem`'s snapshot and destroyed its old 150G disk |

## Findings outside this change

- **`HQ-WS001`'s C: is encrypted with BitLocker but not protected.** `Get-BitLockerVolume` reports `FullyEncrypted`, protection `Off` and no key protectors, and AD holds no `msFVE-RecoveryInformation` object for the computer. The volume key sits in the clear on the disk. That is the state Windows device encryption leaves before it is turned on, and it is why no recovery prompt was possible during this change.
- **`HQ-DC02` was stopped** when I started, with a `qmshutdown` by `root@pam` at 1:01 PM. The [VM inventory](../../../../../Operations/Inventory/Galaxy/VMs.md) listed it as running.
- **`win11-dev` and `hermes-01` were stopped** at my readback afterwards, though the inventory listed both as running. This change did not touch either.

## Open items

- I still need to decide whether `HQ-WS001` gets a TPM protector with its recovery key escrowed to AD, or has its encryption turned off.
