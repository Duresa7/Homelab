# Root Filesystem Expansion

**Created:** 2026-08-29  
**Last updated:** 2026-08-29

## Date

I completed this change on 2026-08-29.

## Scope

I reclaimed the unused `rl-home` logical volume on `splunk-siem` and gave its space to `/`. The root filesystem went from 70 GB with 24 GB free to 141.5 GB with 94.9 GB free. This was the prerequisite for forwarding Wazuh alerts into Splunk, which needed headroom the machine appeared to have but did not.

I did not change the virtual disk, the volume group, the swap volume, or any Splunk configuration. `splunk-siem` is VM 109 on `grey-server`.

## The problem

I had already grown the virtual disk to 150 GB in Proxmox and assumed Splunk had the space. It did not, and the reason was one layer down.

Rocky's default installer had carved `sda3` into three logical volumes and left nothing spare:

| Volume | Size | Mounted | Used |
|---|---|---|---|
| `rl-root` | 70.00 GB | `/` | 45.5 GB, 65% |
| `rl-swap` | 5.87 GB | swap | none |
| `rl-home` | 71.54 GB | `/home` | **192 KB** |

The volume group reported `VFree 0`. Every byte I added to the virtual disk landed in a group that was already fully allocated, so there was nowhere for it to go. Meanwhile half the disk sat under `/home` holding 192 KB, three user directories, of which only `dkadi` had anything in it at all.

`df` made `/home` look busier than it was, reporting 1.5 GB used. That is XFS metadata for a 71 GB filesystem, not data.

**XFS cannot be shrunk.** There is no path that trims `rl-home` and hands back the difference. The volume had to be destroyed and the space given to `rl-root`.

## Why I took a snapshot, and why it is gone

I keep no snapshots and no backups. This is the exception the rule allows: destroying a mounted filesystem on the machine that holds all my UniFi security data is exactly the kind of change that earns a rollback point.

`ssd-lvm1` is `lvmthin`, so the snapshot cost almost nothing and took seconds. I created `pre-home-rebuild` before the first destructive step and deleted it after verification, in the same session. `qm listsnapshot 109` is back to `current` only.

## What I did

The obvious sequence, unmount `/home`, delete it, then grow root, does not work here, and the way it fails is worth writing down. `fuser -vm /home` showed `dkadi`'s login shell, a `dbus-broker` user session, and my own SSH command chain all holding a working directory on it. Forcing them off would have cut the session doing the work.

Rebooting first does not help either, and would have been the dangerous move. `/home/dkadi/.ssh/authorized_keys` is what my key authenticates against. Remove the fstab entry, reboot, and `/home` comes back as the bare empty directory underneath the old mount, with no `authorized_keys` and no way back in.

So I put the data on the root filesystem **before** the reboot, by bind-mounting `/` somewhere the `/home` mount does not cover it:

```console
# mkdir -p /mnt/rootfs && mount --bind / /mnt/rootfs
# ls -la /mnt/rootfs/home
total 0
drwxr-xr-x. 2 root root 6 Jun 28 18:01 .          ← the empty directory under the mount
# rsync -aXAH --numeric-ids /home/ /mnt/rootfs/home/
# diff <(cd /home && find . | sort) <(cd /mnt/rootfs/home && find . | sort) && echo IDENTICAL
IDENTICAL
# ls -l /mnt/rootfs/home/dkadi/.ssh/authorized_keys
-rw-------. 1 dkadi dkadi 286 Aug 13 22:12 ...
# umount /mnt/rootfs && rmdir /mnt/rootfs
```

`-X` carries the SELinux contexts, which matters on Rocky. With the copy in place under the mount, the rest was safe:

1. Removed the `/home` line from `/etc/fstab`, `systemctl daemon-reload`.
2. Rebooted. `/home` came up on the root filesystem with all three user directories and the key intact.
3. `lvremove -f /dev/rl/home`
4. `lvextend -l +100%FREE /dev/rl/root`, 70.00 GB → 141.54 GB
5. `xfs_growfs /`, data blocks 18,350,080 → 37,104,640
6. `restorecon -RF /home`

I stopped `Splunkd` cleanly before the snapshot so the indexes were not mid-write. It started itself on boot.

The pre-change `/etc/fstab` is committed at [Backups/splunk-siem-fstab-2026-08-29](../../../../../Backups/splunk-siem-fstab-2026-08-29) and I deleted the host's copy once the new file worked.

## Verification

**The filesystem is bigger and Splunk can see it.**

```console
$ df -hT /
Filesystem          Type  Size  Used Avail Use% Mounted on
/dev/mapper/rl-root xfs   142G   48G   94G  34% /
```

`| rest /services/server/status/partitions-space` inside Splunk agrees: `/` at 141.5 GB capacity, 46.5 GB used, **94.9 GB free**. Splunk reads this itself for its disk-space guard, so this is the number that governs whether it keeps indexing.

**No data was lost.** Index event counts read back through the management API after the reboot:

| Index | Events | Size |
|---|---|---|
| `_internal` | 70,526,865 | 8,966 MB |
| `_audit` | 16,715,002 | 4,198 MB |
| `_introspection` | 6,518,251 | 8,993 MB |
| `netfw` | 359,396 | 91 MB |
| `netops` | 20,687 | 8 MB |

`netfw` and `netops` are the UniFi pipelines and both carried straight through. The counts kept climbing during verification, which is the collector still running.

**`/home` is intact and correctly labelled.** Three directories, `user_home_dir_t` on each, `dkadi`'s key in place, proven by the fact that every command in this record after the reboot went over that key.

**Splunk is healthy.** `Splunkd` active, listening on 8000, 8088, 8089 and 1514.

Captures are in [Evidence](../../Evidence/Root%20Filesystem%20Expansion%20-%202026-08-29/).

## What this turned up

**Splunk's own internal logs are the biggest thing on the disk.** `_internal`, `_audit` and `_introspection` together hold 22.1 GB. The UniFi security data I actually collect, `netfw` and `netops`, is 99 MB. Internal telemetry outweighs real data by more than 200 to 1.

That is normal for Splunk's defaults and it was not a problem while it was invisible, but it is now the thing that will consume the 94 GB I just recovered. Their retention is governed by `frozenTimePeriodInSecs` in `$SPLUNK_HOME/etc/system/default/indexes.conf`, and the defaults are generous. Trimming them is a separate change with its own trade-off, since `_audit` is the record of who searched for what.

I did not change them here.
