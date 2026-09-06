# CT 110 Phantom Unused Volume Removed

**Created:** 2026-09-06  
**Last updated:** 2026-09-06

**Implementation date:** 2026-09-06  
**Status:** Complete  
**Affected systems:** CT 110 `docker-main` configuration on `grey-server`

## Why

The [2026-09-06 audit](../../../../../Operations/Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md) found `unused0: hddpool:subvol-110-disk-0` in `/etc/pve/nodes/grey-server/lxc/110.conf`. The storage ID `hddpool` is not defined in `/etc/pve/storage.cfg`; the pool is `hddpool-1`, and `pvesm list hddpool-1` returns exactly one volume, `subvol-110-disk-0`, which `mp0` already mounts at `/data`. The line was a leftover from before the pool carried its current storage ID, and Proxmox showed it as a phantom unused disk on the container.

## What I did

I did not use `pct set 110 --delete unused0`. Removing an `unusedN` entry through the API frees the volume it names, and although the named storage does not exist and the call would have failed rather than deleted anything, the volume behind the real `mp0` holds about 1.5 TiB of Immich data on a pool with no backup, so I was not going to let a storage operation near it. I copied the configuration first, redacted its MAC address, and stored it as [grey-server-lxc-110.conf-2026-09-06](../../../../../Backups/grey-server-lxc-110.conf-2026-09-06); the host keeps no copy. Then I deleted the one line with `sed` on the pmxcfs file, matched against the full exact line.

## Verification

- `pct config 110` shows `mp0` and `rootfs` and no `unused` key.
- `red-server` reads the same file through pmxcfs with no `unused` line, so the change replicated.
- CT 110 stayed `running` throughout; `df -h /data` inside the container still shows `hddpool-1/subvol-110-disk-0` at 1.8T with 1.5T used.
- `pvesm list hddpool-1` still returns the one volume.

The LXC inventory now records the line as removed rather than as an open leftover.
