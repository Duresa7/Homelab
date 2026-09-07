# SSH Identity Registration for green-server, monitor-01, game-01 and ansible-01

**Created:** 2026-09-07  
**Last updated:** 2026-09-07

**Change date:** 2026-09-07  
**Status:** Complete. Every human identity audits `present` on every host in its allowlist, 17 hosts under management  
**Scope:** `ssh-key-automation` on `ansible-01`: `inventory/hosts.yml` and the `jedi-pc`, `mac` and `ubuntu-dev` identity files. One key file written on one host, `/home/dkadi/.ssh/authorized_keys` on `ansible-01`, which did not exist before. No key was removed anywhere

## Outcome

The project's inventory had drifted behind the fleet in two ways. `green-server` joined the inventory on 2026-08-15 but the `jedi-pc` and `mac` allowlists still listed only the four older nodes, so the audit never looked at Green for either identity. And `monitor-01`, `game-01` and `ansible-01` were not in the inventory at all, so no identity could be audited against them. Both gaps are closed, and the audit found one real defect on the way: `ansible-01`'s `dkadi` account, created on 2026-08-15, had no `authorized_keys` file, so none of the human keys could log in there.

| Identity | Allowlist before | Added | Audit after |
| --- | --- | --- | --- |
| `jedi-pc` | 13 hosts | `green-server`, `monitor-01`, `game-01`, `ansible-01` | `present` on 17 of 17 |
| `mac` | 13 hosts | `green-server`, `monitor-01`, `game-01`, `ansible-01` | `present` on 17 of 17 |
| `ubuntu-dev` | 14 hosts | `monitor-01`, `game-01`, `ansible-01` | `present` on 17 of 17 |
| `ansible-control` | 9 guests | nothing | `present` on 9 of 9 |

## Why ansible-control did not get green-server

The root `TODO.md` said `ansible-control` needed `green-server` on its allowlist too. It cannot express that. The identity overrides the key store to the `ansible` account at `/home/ansible/.ssh/authorized_keys`, and the override applies to every host in its list, so adding a node would point the audit at a home directory that does not exist there. The controller's key does reach the nodes, through the cluster-backed `/etc/pve/priv/authorized_keys` as root, and that file is managed as one unit by the Proxmox group in this same project. Its presence there is the 2026-08-15 tidy's business, not this identity's. I left the allowlist alone and dropped that part of the claim.

## State before the change

Read on `ansible-01` at 1:13 AM Eastern, filtering the key material out of the identity files:

- `inventory/hosts.yml` listed five nodes and nine guests. The validator reported `4 identities, 14 supported hosts, 0 unknown hosts, 17 Semaphore templates`.
- Allowlists as in the table above. `ubuntu-dev` already listed `green-server`.
- The audit for all four identities reported `present` on every host it was allowed to look at.
- `/home/dkadi/.ssh/` did not exist on `ansible-01`.

## What I changed

1. Added `monitor-01` (`192.168.73.2`), `game-01` (`192.168.80.30`) and `ansible-01` (`192.168.40.36`, `ansible_connection: local`) to `linux_ssh_key_hosts`, each connecting as `ansible` with `dkadi`'s `authorized_keys` as the key store, matching the nine guests already there. The same block went into the repository copy of the inventory, which is versioned.
2. Appended the missing hosts to the three human identities' `target_hosts`. The identity files stay on the controller and are not published.
3. Ran the validator: `4 identities, 17 supported hosts, 0 unknown hosts, 17 Semaphore templates`.
4. Ran the audit for all four identities. Every host reported `present` except `ansible-01`, which reported `missing` for all three human identities.
5. Ran `ssh-identity-onboard.yml` for `jedi-pc`, `mac` and `ubuntu-dev` with `ssh_target_hosts` limited to `ansible-01`. Each reported `changed=1 failed=0`; the play creates the directory and file and adds one key line without touching anything else.
6. The play had created `/home/dkadi/.ssh` as `755 root:root`, because it runs as `ansible` and escalates to root for a file in another account's home. I set it to `700 dkadi:dkadi` by hand. The file itself was already `600 dkadi:dkadi`.

## Verification

At 1:16 AM Eastern:

| Check | Result |
| --- | --- |
| Audit, `jedi-pc`, `mac`, `ubuntu-dev` on `ansible-01` | `current_key: present` for all three |
| `ssh-keygen -lf /home/dkadi/.ssh/authorized_keys` on `ansible-01` | three ED25519 fingerprints |
| `stat` on `/home/dkadi`, `.ssh`, `authorized_keys` | `700 dkadi:dkadi`, `700 dkadi:dkadi`, `600 dkadi:dkadi` |
| `sshd -T` on `ansible-01` | `permitrootlogin no`, `passwordauthentication no`, unchanged |
| Validator | passes at 17 hosts |
| Full audit, all four identities | `present` on every allowlisted host, nothing `missing`, nothing unreachable |

I did not test a login to `ansible-01` from the Jedi PC or the Mac; the fingerprints match the identities' recorded material, which is what the audit checks.

## Found along the way

The onboarding play leaves a newly created `.ssh` directory owned by root when it has to create it. That never showed before because every other host had the directory from its baseline build. Worth fixing in `ensure-key-present-posix.yml` so the next new host does not need the by-hand correction; the [Ansible TODO](../TODO.md) carries it.
