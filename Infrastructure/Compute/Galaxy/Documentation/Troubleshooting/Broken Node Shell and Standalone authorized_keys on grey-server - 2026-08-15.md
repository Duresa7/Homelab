# Broken Node Shell and Standalone `authorized_keys` on `grey-server`

**Created:** 2026-08-15  
**Last updated:** 2026-08-15

**Investigated:** 2026-08-15  
**Owner:** Galaxy / Proxmox node access  
**Status:** Resolved

## Symptom and impact

Signed into `grey-server`'s web interface at `192.168.70.10:8006`, opening **Shell** on any of the other four nodes returned `Permission denied (publickey)`. Shell on `grey-server` itself worked, because that path is local rather than proxied. I hit this on 2026-08-15, hours after the cluster root key file was cleaned up that morning.

No guest was affected and the cluster never lost a vote. `pvecm status` reported Quorate with 5 of 5 before, during, and after the repair.

The Shell button is not cosmetic. Proxmox opens a remote node's shell by running `ssh` as root from the node serving the page, and the failing call names its own command line:

```text
/usr/bin/ssh -e none -o 'BatchMode=yes' -o 'HostKeyAlias=purple-server' -o 'UserKnownHostsFile=/etc/pve/nodes/purple-server/ssh_known_hosts' -o 'GlobalKnownHostsFile=none' -t root@192.168.70.11 --' failed: exit code 1
```

So the same break also blocks any cluster operation that depends on root SSH out of Grey.

## What I measured

Root SSH out of Grey failed to all four peers, and Grey was the only node whose `/root/.ssh/authorized_keys` was not a symlink to the cluster file:

| Node | `/root/.ssh/authorized_keys` | Keys | Unidentified key present | Root SSH to peers |
|---|---|---:|---|---|
| `grey-server` | regular file, 5399 bytes, 2026-08-13 22:12 | 23 | yes | all four fail |
| `purple-server` | symlink to `/etc/pve/priv/authorized_keys` | 9 | no | all four succeed |
| `blue-server` | symlink | 9 | no | all four succeed |
| `red-server` | symlink | 9 | no | all four succeed |
| `green-server` | symlink | 9 | no | all four succeed |

Two separate defects, both confined to Grey.

## Root cause

**Grey's own node key had been removed from the file its peers read.** The morning's cleanup dropped an RSA key commented `root@Kadi` as belonging to no current cluster node. `Kadi` is the hostname this machine carried before it was renamed, and `/root/.ssh/id_rsa.pub` on Grey carries that exact key and that exact comment. It was Grey's node key the whole time. The four peers authorise root by reading the cluster file, so removing Grey's key from it is precisely what stops Grey authenticating outward, and the Shell button was the first place I noticed.

**Grey's inbound file was never the cluster file.** On the other four nodes `/root/.ssh/authorized_keys` is a symlink to `/etc/pve/priv/authorized_keys`, which pmxcfs replicates. On Grey it was a standalone regular file holding content last written on 2026-08-13 at 22:12: 28 lines, 23 key lines, 11 unique keys, with the five duplicated blocks the cleanup was meant to collapse and the unidentified commentless key the cleanup was meant to remove. Inbound root SSH to Grey read that file, so none of the cleanup applied here.

That deviation was deliberate when it was made. [Galaxy Artifact Cleanup and Green SSH Parity](../../../../../Operations/Maintenance/Galaxy%20Artifact%20Cleanup%20and%20Green%20SSH%20Parity%20-%202026-07-31.md) records the reason on 2026-07-31: a standalone file is what scoped the `galaxy-pxe-join` key to Grey alone, and that record states the key appeared zero times in the cluster-wide store. That is no longer true. `galaxy-pxe-join` was already in `/etc/pve/priv/authorized_keys` when I took the baseline for this repair, so it already reached all five nodes and the scoping the standalone file existed to provide had stopped existing. What remained was the cost: a hand-maintained file that silently diverges from the cluster.

**Why the earlier verification passed anyway.** The cleanup was checked by comparing the md5 of `/etc/pve/priv/authorized_keys` from all five nodes and finding one hash. That was true and it was the wrong question. Matching a file's hash across five nodes proves the file is consistent; it does not prove any node reads it.

## Corrective action

I held a second root session open on Grey for the whole job and confirmed it as uid 0 before touching anything, then closed it only after the final verification passed.

**Recorded the file, then removed it from the host.** Grey's standalone file is preserved as a redacted structural rendering at [`Backups/grey-server-root-authorized_keys-2026-08-15`](../../../../../Backups/grey-server-root-authorized_keys-2026-08-15), built from a fingerprint-to-token map so no key data was copied off the host at any point. The file itself is gone from Grey, replaced by the symlink below.

**Reinstated Grey's node key, under the right comment.** I appended the key from Grey's `/root/.ssh/id_rsa.pub` to the cluster file with the comment field rewritten from `root@Kadi` to `root@grey-server`, so the next reader is not invited to repeat the misidentification. The key data is unchanged; only the comment moved.

The candidate was built in `/tmp` and had to pass five guards or the run aborted without installing it: exactly 10 parsed keys, 10 unique fingerprints, 10 lines so no unparseable or blank line could hide, the key this session authenticates with still present, and no occurrence of the unidentified key. All five passed.

`/etc/pve` is pmxcfs, a FUSE filesystem, so a `mv` from `/tmp` would cross filesystems and would not be atomic. I overwrote the existing path in place at 11:44:58 AM and let pmxcfs replicate. Mode and ownership came through unchanged at `600 root:www-data`, and the file went from 3450 to 4192 bytes.

**Replaced the standalone file with the symlink.** At 11:45:13 AM I created the symlink under a temporary name inside `/root/.ssh` and moved it into place with `mv -T`, a same-directory rename. That leaves no window in which the path is missing or half-written, which matters because the file being replaced is the one authorising the connection doing the replacing. The guard before it re-checked that the cluster file still held this session's key.

The working copy in `/tmp` was removed. Grey holds no copy of either file outside the live paths.

## Verification

Every node was checked over its own fresh SSH connection, which is itself proof that the node still authenticates against the new file:

| Node | `authorized_keys` | Keys | Unique | Unidentified key | `root@grey-server` | `root@Kadi` | Cluster file md5 | Mode |
|---|---|---:|---:|---|---|---|---|---|
| `grey-server` | symlink | 10 | 10 | 0 | 1 | 0 | `ef598c94…` | `600 root:www-data` |
| `purple-server` | symlink | 10 | 10 | 0 | 1 | 0 | `ef598c94…` | `600 root:www-data` |
| `blue-server` | symlink | 10 | 10 | 0 | 1 | 0 | `ef598c94…` | `600 root:www-data` |
| `red-server` | symlink | 10 | 10 | 0 | 1 | 0 | `ef598c94…` | `600 root:www-data` |
| `green-server` | symlink | 10 | 10 | 0 | 1 | 0 | `ef598c94…` | `600 root:www-data` |

- `ssh -o BatchMode=yes root@<peer> hostname` from Grey returns the peer's own hostname for `purple-server`, `blue-server`, `red-server` and `green-server`. All four failed before the change.
- `ssh -o BatchMode=yes root@grey-server hostname` from `green-server` returns `grey-server` on a fresh connection.
- `ssh-keygen -lf /root/.ssh/authorized_keys` on Grey returns 10 keys and no unidentified key.
- `test -L /root/.ssh/authorized_keys` is true on all five nodes.
- `pvecm status` reports Quorate, 5 expected votes, 5 total votes, all five members.

**The Shell button itself.** This is the symptom that opened the issue, so I closed it on the same path rather than on an equivalent. I authenticated to the API as `root@pam`, created a `termproxy` session on each of the four peers, and connected the `vncwebsocket` the browser connects to, then sent a command into the shell and read its answer back. All four returned `101 Switching Protocols` and answered from the target node:

```text
purple-server  websocket=101 Switching Protocols  shell answered: purple-server
blue-server    websocket=101 Switching Protocols  shell answered: blue-server
red-server     websocket=101 Switching Protocols  shell answered: red-server
green-server   websocket=101 Switching Protocols  shell answered: green-server
```

## One signal that looks like a failure and is not

Running `pvesh create /nodes/<node>/termproxy` from a shell always ends in `failed: exit code 1`, because no browser client ever connects and termproxy kills its child on the client timeout. I checked it against Grey's own node, whose Shell is a local `/bin/login -f root` and was working throughout, and it returns the identical error. The exit code says nothing about whether the SSH underneath it succeeded. Reproducing the exact `ssh` command line, or connecting a real websocket client as above, is what actually distinguishes the two.

## Follow-up

`galaxy-pxe-join` now reaches root on all five nodes rather than on Grey alone, which is a widening that happened before this repair and was not caused by it. Whether that key is re-scoped is now an open decision in the [Galaxy TODO](../TODO.md), and this repair removed the mechanism that used to enforce the narrower scope.

## Related records

- [SSH Authorized Key Cleanup](../../../../../Operations/Maintenance/SSH%20Authorized%20Key%20Cleanup%20-%202026-07-14.md), the earlier pass over these files
- [SSH Key Comment Normalization](../../../../../Operations/Maintenance/SSH%20Key%20Comment%20Normalization%20-%202026-08-15.md), same day, same wave of work
- [Galaxy Artifact Cleanup and Green SSH Parity](../../../../../Operations/Maintenance/Galaxy%20Artifact%20Cleanup%20and%20Green%20SSH%20Parity%20-%202026-07-31.md), which records why Grey's file was standalone
- [Node Root Password Reset](../Change%20Records/Node%20Root%20Password%20Reset%20-%202026-08-15.md), the other node-level access change of 2026-08-15
- [`Backups/grey-server-root-authorized_keys-2026-08-15`](../../../../../Backups/grey-server-root-authorized_keys-2026-08-15), the redacted structural copy of the removed file
