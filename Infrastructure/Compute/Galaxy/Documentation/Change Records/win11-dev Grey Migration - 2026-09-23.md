# win11-dev Grey Migration

**Created:** 2026-09-23  
**Last updated:** 2026-09-23

**Status:** Complete.

I moved VM 103 `win11-dev` from `green-server` to `grey-server`, with its 120 GiB system disk, 4 MiB EFI volume and 4 MiB TPM state on Grey's NVMe-backed `local-lvm`. I kept four host-model vCPUs, 8 GiB fixed memory, automatic startup, `vmbr0` VLAN 40 and `192.168.40.117/24`.

## Preflight

At 7:01 PM Eastern, VM 103 was already stopped on Green. SSH returned `EHOSTUNREACH`. Galaxy held quorum with five votes. Grey had 17,444 MiB available memory and 612,198,096 KiB available in `local-lvm`; its pool was 26.45% used. Grey had no VM 103 volumes. Its VLAN-aware `vmbr0` allowed VLAN 40. HA had no configured resources.

The guest uses `cpu: host`; Green is Intel and Grey is AMD. I kept the guest stopped for the move and verified Windows after a fresh start on Grey. Green's previously documented [memory fault](../Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md) remains unresolved.

## Migration

At 7:01:49 PM Eastern, the first migration aborted before copying disks with `local:iso/win11-dev-unattend.iso: content type 'iso' is not available on storage 'local-lvm'`. `qm config 103` had shown the intended disc-free configuration, but the raw configuration still held three installer attachments and a `[PENDING]` section removing them. The answer ISO was already absent. `qm listsnapshot 103` showed no snapshots.

I applied the intended cleanup while the VM was stopped with `qm set 103 --delete ide0,ide2,sata0 --boot order=scsi0`. `qm pending 103` then showed only current settings, system-disk-only boot and no optical drives. At 7:02 PM Eastern I retried independently of the SSH session:

```sh
systemd-run --unit=win11-dev-grey-migration-retry --collect /usr/sbin/qm migrate 103 grey-server --targetstorage local-lvm --online 0
```

The EFI import completed and the system disk began transferring at about 116 MB/s. At 7:09:50 PM Eastern, after about 48 GiB, the SSH connection reset. Grey's SSH log reported `Corrupted MAC on input` and `message authentication code incorrect`. There was no configured SSH channel timeout, no host restart, and no matching kernel fault in the inspected Green log. Green's known memory fault is a possible cause, but these observations do not isolate the hardware responsible.

The failed migration left all three original volumes and the stopped guest configuration on Green. Proxmox removed the completed destination EFI volume; the incomplete 120 GiB destination volume remained. I verified no guest configuration or active migration on Grey, removed only that incomplete destination volume, and confirmed its VM 103 volume list was empty.

I then locked the stopped guest with `qm set 103 --lock migrate` and ran separate `pvesm export` / `pvesm import` streams through Zstandard level 1 and the same authenticated, encrypted cluster SSH connection. All three imports completed at 7:18:44 PM Eastern. I kept the original disks until verification.

I replaced the slow sequential source checksum pass with parallel direct-I/O SHA-256 reads: thirty 4 GiB blocks cover the 120 GiB system disk, plus one complete read each of the 4 MiB EFI and TPM volumes. Two source passes produced identical manifests, completing at 7:23:31 PM Eastern. The destination matched 28 of the 32 entries. Four system-disk blocks differed: offsets 0, 8, 20 and 116 GiB. Both small volumes matched.

I retained the [stable source manifest](../../Evidence/win11-dev%20Grey%20Migration%20-%202026-09-23/Logs/Source-Direct-Read-SHA256.txt) and [destination manifest before repair](../../Evidence/win11-dev%20Grey%20Migration%20-%202026-09-23/Logs/Destination-Before-Repair-SHA256.txt). Each label records a disk number, offset and count in 4 MiB units. These are checksum artifacts, not terminal transcripts. The copied data differed despite the encrypted transfer completing, so transfer success alone was insufficient verification on this source host.

I recopied those four 4 GiB ranges with `dd iflag=direct`, Zstandard and authenticated SSH. Destination writes used `iflag=fullblock`, `oflag=direct` and `conv=notrunc` at the matching offsets. All four completed at 7:26:11 PM Eastern. A fresh checksum pass across the complete destination finished at 7:27:04 PM Eastern; all 32 entries matched both stable source passes. I retained the [destination manifest after repair](../../Evidence/win11-dev%20Grey%20Migration%20-%202026-09-23/Logs/Destination-After-Repair-SHA256.txt).

I then confirmed the guest was still stopped, compared the two source manifests and the destination manifest again, and moved `/etc/pve/nodes/green-server/qemu-server/103.conf` to `/etc/pve/nodes/grey-server/qemu-server/103.conf`. This was a manual offline relocation after the failed native migration, not a successful `qm migrate` task. I verified the configuration existed only on Grey, removed the migration lock, updated its description and started VM 103 on Grey. Proxmox recorded startup `OK` and preserved the existing TPM state.

## Verification and cleanup

At 7:29 PM Eastern I connected through the existing SSH Manager entry at `192.168.40.117`. Windows returned hostname `WIN11-DEV`, Windows 11 Pro build 26200, Grey's AMD Ryzen 7 3700X processor, 7.93 GiB usable RAM, standalone `WORKGROUP` membership and no device configuration errors. Secure Boot was enabled, TPM was present and ready, and `sshd` and `QEMU-GA` were running with automatic startup. The Proxmox guest-agent ping also succeeded. I retained the filtered [Windows readback](../../Evidence/win11-dev%20Grey%20Migration%20-%202026-09-23/Exports/Windows-After-Migration.json).

Grey held all three volumes and VM 103 was running with `onboot=1`, the same VLAN and no optical drives or migration lock. The EFI logical volume remains 4 MiB; after startup Proxmox reports its firmware-image size as `528K`. Grey had 9,099 MiB available memory and 574,076,175 KiB free in `local-lvm`, which was 31.03% used. Galaxy remained quorate with five votes.

After confirming the cluster reported VM 103 running only on Grey, I deleted the three original VM 103 volumes from Green. At 7:29:53 PM Eastern its VM 103 volume list was empty and its thin pool reported 0.00% used, with 148,086,784 KiB available. The source configuration was absent. I removed the temporary transfer and checksum scripts and manifests from both hosts after retaining the evidence here.

No migration work remains open. Windows activation and Green's hardware repair remain separate backlog items. The [SSH corruption investigation](../Troubleshooting/Corrupted%20SSH%20Packet%20During%20win11-dev%20Migration%20-%202026-09-23.md) records the unresolved cause of the failed transfer; the [installer-reference record](../Troubleshooting/Pending%20Installer%20Removal%20Blocked%20win11-dev%20Migration%20-%202026-09-23.md) records the first abort.

These observations are summarized from live tool results. Apart from the linked checksum manifests and filtered Windows readback, the steps have no separately retained terminal captures. No snapshot or backup was created.
