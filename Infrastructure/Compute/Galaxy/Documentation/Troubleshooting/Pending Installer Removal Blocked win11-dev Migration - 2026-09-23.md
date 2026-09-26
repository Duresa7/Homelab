# Pending Installer Removal Blocked win11-dev Migration

**Created:** 2026-09-23  
**Last updated:** 2026-09-23

**Status:** Resolved; the retry passed disk discovery and began copying.

At 7:01:49 PM Eastern I tried moving stopped VM 103 from Green to Grey's `local-lvm`. Proxmox aborted before copying disks:

```text
local:iso/win11-dev-unattend.iso: content type 'iso' is not available on storage 'local-lvm'
```

`qm config 103` showed no optical drives and `boot: order=scsi0`. I read the raw `/etc/pve/nodes/green-server/qemu-server/103.conf` after the abort. Its current section still attached the Windows installer at `ide0`, VirtIO media at `ide2`, and the answer ISO at `sata0`. A `[PENDING]` section held their deletion and the new boot order. The answer ISO no longer existed on disk. `qm listsnapshot 103` showed only the current state, ruling out a snapshot reference.

The earlier installer cleanup was pending in Proxmox rather than applied to the current configuration. Disk discovery during migration still encountered the ISO reference, and mapping all storage to an image-only thin pool failed the content-type check.

With `qm status 103` confirmed stopped, I ran:

```sh
qm set 103 --delete ide0,ide2,sata0 --boot order=scsi0
qm pending 103
```

The readback showed only current settings, no optical drives and system-disk-only boot. The [migration retry](../Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md) passed disk discovery, imported the EFI volume and began copying the system disk. I did not recreate the deleted answer ISO or change the target storage.

These observations are summarized from live tool results; I did not retain separate full terminal transcripts.
