# SSH Key Comment Normalization

**Created:** 2026-08-15  
**Last updated:** 2026-08-15

**Change date:** 2026-08-15  
**Status:** Complete, with one check I could not run from this workstation  
**Scope:** The three `authorized_keys` entries whose `jedi-pc` comment had drifted, on `edge-01` and `docker-blue`

## Outcome

Every installed key is supposed to end in the identity that owns it, so that a reader of an `authorized_keys` file can tell whose key each line is. A fleet audit found my PC's key carrying a drifted comment in three places: `jedi-pc` with a `-dkadi-nopass` suffix. That suffix names a sudo policy I am in the middle of reversing, so leaving it would have pointed the next reader at a rule that no longer holds.

I rewrote the comment field on those three lines and changed nothing else on them. The key type, the key data and the absence of an options prefix are all as they were. A rescan of every readable `authorized_keys` scope in the environment now finds zero copies of the old comment.

## What changed

| Host | Account | File | Keys before and after | Mode before | Mode after |
|---|---|---|---|---|---|
| `edge-01` | `root` | `/root/.ssh/authorized_keys` | 2 | `664` | `0600` |
| `docker-blue` | `root` | `/root/.ssh/authorized_keys` | 3 | `700` | `0600` |
| `docker-blue` | `dkadi` | `/home/dkadi/.ssh/authorized_keys` | 3 | `600` | `0600` |

Ownership is unchanged: `root:root` on the two root files, `dkadi:dkadi` on the third.

`edge-01`'s root file was group-writable at `664`. `sshd -T` reports `strictmodes yes` there, and strict mode refuses a group-writable `authorized_keys`, so that file's keys would not have been accepted. Nothing depended on it, because `sshd -T` also reports `permitrootlogin no` on both hosts, but I brought all three files to `0600` rather than preserve a mode that was wrong.

`docker-blue`'s root file is wrapped in `# --- BEGIN PVE ---` and `# --- END PVE ---` markers, written when CT 108 was created. `/etc/pve/lxc/108.conf` on `blue-server` carries no `ssh-public-keys` entry, so Proxmox has nothing to rewrite that block from and the edit will hold.

## How I made the edit

Each file was rebuilt through a temporary file in its own directory and moved into place with a same-filesystem rename, so no reader ever saw a partial file. `sed` matched the drifted comment only at end of line, which leaves an options prefix alone if one is ever present.

Before the rename the temporary file had to pass three checks, or the run aborted and discarded it: `ssh-keygen -lf` had to report the same number of keys as the original, the old comment had to appear zero times, and the canonical `jedi-pc` entry had to appear exactly once at its known fingerprint. Ownership was then copied from the original with `chown --reference` and the mode set to `0600`.

I ran all three edits as root through Ansible from `ansible-01`, over the `ansible` account. That account keeps its `NOPASSWD` grant throughout this wave of work on purpose, which makes it the route back in if a change to a human account's key file goes wrong.

For the `dkadi` file, the only one of the three that could have locked me out, I held a second `dkadi` shell open on `docker-blue` for the whole edit and confirmed it was still alive afterward.

## Verification

- `ssh-keygen -lf` on all three files reports the canonical `jedi-pc` comment at the same fingerprint the identity is registered under. The fingerprint is a hash of the key blob, so it being unchanged is the proof that only the comment moved.
- Key counts are unchanged: 2, 3 and 3, matching the pre-change counts in the table above.
- A fresh SSH session opened as `dkadi@docker-blue` after the edit, and `sshd` logged the accepted public key.
- The rescan covers all twelve guests over `/root/.ssh` and `/home/*/.ssh`, `docker-main`'s root account, this workstation, and all five Proxmox nodes over both `/etc/pve/priv/authorized_keys` and their own `/root/.ssh/authorized_keys`. Zero matches for the old comment anywhere.
- No temporary file was left behind in either `.ssh` directory, and the helper script was removed from `ansible-01`.

## The check I could not run

The ticket asks for an SSH session opened with the Jedi PC key itself. That private key lives on my PC and not on this workstation, so I could not authenticate as it from here. What I can show is that the entry is intact and that the file works: the fingerprint is unchanged, and `sshd` accepted a public key from that same file on a fresh connection. A login from the PC would close the last of it.

## Related

Part of the fleet access model change being carried out through 2026-08-14 and 2026-08-15. The earlier pass over these files is [SSH Authorized Key Cleanup](SSH%20Authorized%20Key%20Cleanup%20-%202026-07-14.md), which normalized the three approved identities but did not catch this drift.
