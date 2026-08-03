# Galaxy Host Backup Artifact Purge

**Created:** 2026-07-26  
**Last updated:** 2026-07-26

**Change date:** 2026-07-26  
**Status:** Complete  
**Scope:** Removal of every host-side backup artifact on the four Galaxy Proxmox nodes, including config snapshots, an orphaned guest image, and two SSH recovery files

## Outcome

I deleted every operator-created backup artifact sitting on `grey-server`, `purple-server`, `blue-server`, and `red-server`. That covers 12 `cluster.fw` snapshots, a host firewall and storage snapshot, four config directories, a 2.2 GB orphaned guest image, two SSH recovery files on Red, and a second pass through `/etc` and `/usr/share`.

Grey's rootfs went from 77 percent to 75 percent, reclaiming the 2.2 GB the guest image held. Nothing else on any node was large enough to move the number.

I ran this in two passes because the first scan only covered `/root` and `/var/lib/vz/dump`. Widening it to `/etc`, `/usr/share`, `/var/backups`, and `/opt` turned up a second tranche, most of which had to be left alone.

This purge deliberately voids rollback points that six committed change records still name. Those records are annotated to point here rather than being rewritten, because the deletion is the newer fact and the original records stay accurate about what happened on their own dates.

## What I Removed

| Node | Path | Items |
|---|---|---|
| grey | `/root` | 12 `cluster.fw` snapshots dated 2026-05-30 through 2026-07-26, `grey-host.fw.bak.20260530-175359`, `storage.cfg.bak.2025-08-26-0001` |
| grey | `/root` | `apt-backups/`, `proxmox-gpu-backups/`, `consolidate-70.10-backup-20260526-195529/`, `sith-cleanup-backup-20260526-193347/` |
| grey | `/root` | Two misnamed SSH Manager files & five `.claude.json.backup.*` snapshots |
| grey | `/var/lib/vz/dump` | `vzdump-qemu-100-2025_08_26-15_59_13.vma.zst` (2.2 GB) with its `.log` & `.notes`, an orphaned `vzdump-lxc-101` log, & the empty `internal-https-2026-07-22-prechange` directory |
| purple | `/root` | `sources.list.d.bak.20260530-024816/` |
| blue | `/root` | `sources.list.d.bak.20260530-024817/` |
| red | `/root` | `apt-sources.bak.matched-grey-20260707-105436/`, `interfaces.bak`, `sshd_config.bak.pre-keyonly-20260707-105303`, two misnamed SSH Manager files |
| red | `/var/lib/vz/dump` | Empty `internal-https-2026-07-22-prechange` directory |
| grey | `/etc`, `/usr/share` | `default/grub.bak.20260429-093836`, `lvm/lvm.conf.bak`, `network/interfaces.bak.20260710_084826`, three `nut/*.conf.bak.20260722_081158` |
| purple | `/etc`, `/usr/share` | `lvm/lvm.conf.bak`, `network/interfaces.bak`, `network/interfaces.bak.20260710_085149`, both `proxmox-widget-toolkit/proxmoxlib.js.bak*` |
| blue | `/etc`, `/usr/share` | `lvm/lvm.conf.bak`, both `proxmox-widget-toolkit/proxmoxlib.js.bak*` |
| red | `/etc`, `/usr/share` | `lvm/lvm.conf.bak`, `nut/nut.conf.bak.20260722_081157`, `nut/ups.conf.bak.20260722_081158`, `proxmoxlib.js.bak.no-sub-popup-20260707-110856` |

## What I Deliberately Left

A `find` for `*.bak`, `*.old`, and `*backup*` returns far more than operator snapshots, and most of those hits must stay:

- `/etc/lvm/backup` is LVM's live volume-group metadata, not a stale copy. It's how a VG gets recovered. Grey reports 2 volume groups and the other three report 1, unchanged after the purge.
- `/etc/pve/authkey.pub.old` is managed by `pve-cluster` across ticket-key rotation.
- `dpkg-db-backup.timer` is an active systemd timer.
- Package-shipped paths that merely contain the word: `man/man1/proxmox-backup-client.1.gz`, the `bash-completion` and `zsh` completions, `pve-docs/images/screenshot/gui-cluster-backup-*.png`, `nmap/scripts/http-backup-finder.nse`, and the `/usr/share/doc/proxmox-backup-*` trees. Deleting any of these corrupts an installed package.

Every deletion was a copy sitting beside a live file, and I confirmed the live file still existed immediately after. `proxmoxlib.js` keeps the applied no-subscription-popup patch; removing its `.bak` twin only removes the ability to revert by copy, and `apt install --reinstall proxmox-widget-toolkit` restores the stock file.

## The Guest Image Was an Orphan

The 2.2 GB archive was `vzdump-qemu-100`, and its `.notes` file read `truenas-scale`. VMID 100 today is the running `ansible-01` LXC, so the ID had been reused after the original VM was deleted. `qm config 100` confirms no QEMU guest 100 exists: `Configuration file 'nodes/grey-server/qemu-server/100.conf' does not exist`. Deleting the archive removed the last copy of a TrueNAS Scale VM retired sometime after 2025-08-26, and touched nothing belonging to `ansible-01`.

I checked for other copies first. `find /var/lib/vz /mnt/pve -name "*qemu-100*"` returned only the three files in that one directory.

## Two Recovery Files I Removed Anyway

Red held `sshd_config.bak.pre-keyonly-20260707-105303` and `interfaces.bak`. The first is the SSH daemon config from before key-only authentication went in on 2026-07-07; the second is a network config snapshot from the same window. Both are lockout and network-recovery fallbacks on a hypervisor, and I flagged them as worth keeping. I was told to remove them regardless, so they're gone.

Recovering either now means rebuilding from the [Linux Host Baseline Standard](../../Security/Hardening/Linux-Host-Baseline-Standard.md) and the [Red server expansion record](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Cluster%20Red%20Server%20Expansion%20-%202026-07-07.md) rather than restoring a file. Console access through the Proxmox GUI remains the path back in if SSH ever refuses on Red.

## Rollback Points This Voids

| Record | Named artifact |
|---|---|
| [PeaNUT UPS Dashboard Deployment - 2026-07-22](../../Platforms/PeaNUT/Documentation/Change%20Records/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22.md) | `cluster.fw.bak.peanut-20260722` & both `pre-peanut-nut-config` SSH Manager files |
| [Kasm Lab Proxmox Teardown - 2026-07-23](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Kasm%20Lab%20Proxmox%20Teardown%20-%202026-07-23.md) | `cluster.fw.bak-20260723` |
| [Galaxy Cluster Red Server Expansion - 2026-07-07](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Cluster%20Red%20Server%20Expansion%20-%202026-07-07.md) | `cluster.fw.bak.pre-red-20260707-105114` |
| [Security-A Migration - 2026-07-12](../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md) | `cluster.fw.bak.security-a-20260712-213729` & `cluster.fw.bak.security-a-cleanup-20260712-215806` |
| [Termix SSH Host Onboarding - 2026-07-14](../../Archive/Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md) | `cluster.fw.pre-termix-2026-07-14` |

The firewall state itself is not lost. [Galaxy Data Center Firewall](../../Infrastructure/Compute/Galaxy/Configuration/Datacenter-Firewall.md) carries the IPSets, the full `pve_mgmt` rule table, and the ordering constraint, so the live 49-line file is reconstructable from git without any snapshot. What's gone is the ability to restore a specific earlier state in one copy.

## Verification

All four nodes report `pve-firewall status` as `enabled/running` and hold `cluster.fw` at SHA256 `6847426ae1a940607714f89bae45763341ad7aa6c96f6f007f6364e845c60341`, unchanged by this purge. `pveproxy` is active on all four, `pvecm status` reports 4 nodes and `Quorate: Yes` against 4 expected votes, and LVM still enumerates its volume groups on every node. The cluster reports 12 running and 10 stopped guests, matching the state before the purge.

`nut-server` stays active on Red and Grey, so both UPS units keep reporting. The live `/etc/network/interfaces`, `/etc/default/grub`, `/etc/lvm/lvm.conf`, the three `/etc/nut/*.conf` files, and `proxmoxlib.js` are all present on the nodes that had them.

## A Note on Where These Came From

Two of the removed files were named `\var\backups\ssh-manager\...` with literal backslashes, sitting in `/root` on Grey and Red. Those are the `pre-peanut-nut-config` backups from 2026-07-22: the SSH Manager backup helper wrote Windows-style paths as single filenames instead of creating `/var/backups/ssh-manager/`. Any future use of that helper's backup feature will drop files in the same wrong place, so the retention claim in the 2026-07-22 PeaNUT record was never going to hold the way it read.
