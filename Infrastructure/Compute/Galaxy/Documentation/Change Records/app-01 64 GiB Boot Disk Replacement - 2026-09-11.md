# app-01 64 GiB Boot Disk Replacement

**Created:** 2026-09-11  
**Last updated:** 2026-09-25

**Status:** Complete. VM 116 runs on its verified 64 GiB replacement disk on Grey. I removed the original 200 GiB volume after service verification. The pre-existing Wazuh connection failure remains open.

I chose a 64 GiB system disk after the [sizing assessment](app-01%20Disk%20Sizing%20Assessment%20-%202026-09-11.md). This change replaces app-01's disk on `grey-server`. The move to Purple remains separate.

## Preflight

VM 116 had no snapshots, pending changes, or additional system disks. Its system disk was `ssd-lvm1:vm-116-disk-1`, 200 GiB; its 4 MiB EFI variables disk was `ssd-lvm1:vm-116-disk-0`. Grey's SATA thin pool had 1,642,412,826 KiB available before allocation. All seven containers were healthy, PostgreSQL accepted connections, and both guest-local and edge-01 requests returned HTTP 302 for the Coolify dashboard and HTTP 404 for the proxy's unmatched route.

I allocated `ssd-lvm1:vm-116-disk-2` at exactly 68,719,476,736 bytes. I issued `qm shutdown 116 --timeout 60` at 12:19:25 AM Eastern; the subsequent status was stopped. No force stop was used.

## Replacement method

The [bounded copy script](../../Scripts/app-01-replace-boot-disk.py) checks VM identity, stopped state, the source attachment, both volume sizes, a blank destination, and the exact source partition layout before writing. It maps the original disk read-only, checks its ext4 filesystem, and creates a 64 GiB destination GPT layout with the same disk and partition identifiers. The EFI system partition retains its size and location; root becomes smaller and the existing-size swap partition moves to the end of the new disk.

I copy the EFI partition byte-for-byte and compare it, create a new ext4 filesystem and swap area with the existing UUIDs, and copy root with `rsync -aHAXSx --numeric-ids`. The source mount is read-only with journal replay disabled. A second checksum pass checks file contents, metadata, hardlinks, ACLs, extended attributes, and unexpected destination paths. The script also compares `fstab` and GRUB configuration, checks the destination filesystem after unmounting it, and verifies all three filesystem UUIDs match. It detaches its loop devices and removes its mount directories before returning.

Preserving the identifiers keeps the existing EFI boot entry, GRUB root search, `fstab`, and swap/resume references usable without changing guest configuration. Only one of the two disks will be attached when the VM boots. The original remains available until replacement boot and service checks pass, then it will be removed as part of this change. No snapshot was created.

## Verification and cleanup

The copy finished at 12:30:01 AM Eastern. The checksum pass returned no differences across 302,171 entries, the destination passed `e2fsck -f -n`, and EFI, root, and swap UUIDs matched. The copy service reported `ExecMainStatus=0`. I retained the original copy log and pre-change Wazuh errors. The partition-table reread warning on the logical volume did not prevent the new loop mapping or filesystem verification. The source's third GPT partition type was preserved as reported, although its content is swap; the guest successfully activates it by UUID.

I detached the original `scsi0` and attached `ssd-lvm1:vm-116-disk-2`. Proxmox removed `scsi0` from the boot order during detachment, so the first start remained in firmware. I restored `boot: order=scsi0;net0` and restarted. This boot-switch sequence is recovered from the preceding work's messages and tool history; I did not retain a separate raw transcript for it.

At 2:31 AM Eastern I verified that the VM was running with the 64 GiB volume attached, the guest agent answered, root was mounted read-write, and ext4 reported zero errors. The guest showed exactly 68,719,476,736 bytes for `/dev/sda`, 13 GiB used and 44 GiB available on root, and active 2 GiB swap. Docker, QEMU guest agent, Wazuh agent, and node exporter were active, with no failed systemd units. All seven containers were healthy and PostgreSQL accepted connections. The first unqualified `swapon` check failed because it was outside the SSH account's PATH; `/sbin/swapon --show` succeeded.

Wazuh's process is active but its manager connection is not healthy. Its state was `pending`, with a TCP connection in `SYN-SENT` to `192.168.72.2:1514`. The same connection and enrollment errors appear at 12:01 AM through 12:13 AM Eastern, before the 12:19 AM shutdown. I therefore did not treat this as a disk-copy regression or change the network during this task. Wazuh reachability remains a separate open item.

At 2:32 AM Eastern I verified the exact new attachment and old `unused0` identity, then ran `qm disk unlink 116 --idlist unused0`. Proxmox reported removal of `vm-116-disk-1`; its device path and unused configuration entry were absent afterward. The 64 GiB disk remained present and the running guest answered. I stopped the exited temporary copy service and deleted its temporary script and log after retrieving the log. No loop mappings or copy mount directory remained. No snapshot was created and no source-disk backup remains. The cleanup transcript retains the checks and result.

The final checks at 2:33 AM Eastern again showed seven healthy containers, active swap, an accepting database, and no failed units. Requests from edge-01 returned HTTP 302 for the dashboard and HTTP 404 for the proxy's unmatched route, matching preflight.

I updated the living VM, node, service, and inventory records and the migration backlog. The LXC inventory needs no change because no container allocation changed. The move of app-01 and edge-01 to Purple remains proposed, with live VLAN verification and a shutdown migration window still required.
