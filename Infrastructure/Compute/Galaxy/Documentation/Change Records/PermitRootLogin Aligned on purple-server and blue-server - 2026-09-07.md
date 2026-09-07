# PermitRootLogin Aligned on purple-server and blue-server

**Created:** 2026-09-07  
**Last updated:** 2026-09-07

**Change date:** 2026-09-07  
**Status:** Complete and verified. All five nodes resolve `permitrootlogin without-password`  
**Scope:** Line 33 of `/etc/ssh/sshd_config` on `purple-server` and `blue-server`. No other node, file or setting changed

## Outcome

`purple-server` and `blue-server` had carried `PermitRootLogin yes` since they were built on 2026-05-27, where `grey-server`, `red-server` and `green-server` resolve `prohibit-password`. Nothing was exposed by the difference, because `PasswordAuthentication no` was already in force on all five, so root accepted keys only either way. The setting said something untrue about intent, and now it does not.

| Node | Before | After | Where it is set |
| --- | --- | --- | --- |
| `grey-server` | `prohibit-password` | unchanged | `sshd_config` line 33 |
| `purple-server` | **`yes`** | `prohibit-password` | `sshd_config` line 33 |
| `blue-server` | **`yes`** | `prohibit-password` | `sshd_config` line 33 |
| `red-server` | `prohibit-password` | unchanged | `sshd_config` line 33 |
| `green-server` | `prohibit-password` | unchanged | `sshd_config.d/99-galaxy-proxmox.conf`, overriding a `yes` on line 33 |

`no` is not an option on any node. Proxmox needs root SSH between nodes for migrations and the web interface **Shell** button, which is what broke on 2026-08-15 when `grey-server`'s own key was removed from the cluster file.

## State before the change

Read through the SSH Manager as root on all five, at 1:11 AM Eastern: `sshd -T` and the `PermitRootLogin` lines in `/etc/ssh/sshd_config` and `/etc/ssh/sshd_config.d/`. All five reported `passwordauthentication no`, `kbdinteractiveauthentication no` and `pubkeyauthentication yes`. All five run `pve-manager/9.2.11` with `ssh.service` active and `ssh.socket` inactive, so sshd is not socket-activated on the nodes and a restart hands over cleanly. Each of the two changed nodes had exactly one `PermitRootLogin` line in the main file, at line 33, reading `yes`.

`green-server`'s pattern is worth noting: its main file still says `yes` at line 33 and a drop-in overrides it. I did not copy that pattern. Editing the line the other two nodes already use keeps four of five nodes identical, and the drop-in on Green is the odd one out rather than the model.

## What I changed

On each node, in this order, `purple-server` first and `blue-server` only after Purple passed:

1. Opened a persistent SSH Manager session as root and kept it open.
2. Confirmed line 33 read exactly `PermitRootLogin yes` and that it was the only such line in the file.
3. Replaced it in place with `PermitRootLogin prohibit-password`, ran `sshd -t`, then `systemctl restart ssh`.
4. Read `sshd -T` back and opened a fresh root connection through the SSH Manager.
5. Closed the held session.

No copy of `sshd_config` was taken. The change is one word on one line, and the before and after are both in this record.

## Verification

At 1:12 AM Eastern, on each of the two nodes:

| Check | Result |
| --- | --- |
| `sed -n 33p /etc/ssh/sshd_config` | `PermitRootLogin prohibit-password` |
| `sshd -t` | exit 0, no output |
| `systemctl is-active ssh` after restart | `active` |
| `sshd -T` | `permitrootlogin without-password`, `passwordauthentication no` |
| Fresh `ssh_execute` as root | hostname and `root`, exit 0 |

`without-password` is the name `sshd -T` prints for `prohibit-password`; they are the same setting.

## Left open

The [Galaxy TODO](../TODO.md) still carries the `galaxy-pxe-join` key question, which is about scope rather than sshd and is not touched here.
