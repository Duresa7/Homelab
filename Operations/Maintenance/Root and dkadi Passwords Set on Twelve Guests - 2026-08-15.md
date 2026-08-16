# Root and dkadi Passwords Set on Twelve Guests

**Created:** 2026-08-15  
**Last updated:** 2026-08-15

**Change date:** 2026-08-15  
**Status:** Complete and verified on all twelve guests  
**Scope:** `root` and `dkadi` account passwords on the twelve Linux guests in the host access model, plus a new `dkadi` account on `ansible-01`. The five Proxmox nodes, `ubuntu-dev`, `docker-main` and `supabase-01` are outside the model and were not touched

## Outcome

All twelve guests now report a usable root password, and both account passwords are proven to authenticate rather than merely proven to have landed in `/etc/shadow`. Eight of the twelve had root locked before this change, which is the condition that makes the next step dangerous: `Defaults rootpw` on a host with a locked root password locks every account out of sudo there, and the only way back is the Proxmox console.

`ansible-01` gained the `dkadi` account it never had, with home directory, `/bin/bash` and `sudo` group membership. It carries no sudoers drop-in, because group membership is the whole policy for that account under the model chosen on 2026-08-15.

`ai-agent` and `ansible` were deliberately left alone. `ai-agent` already carried the standard password on all twelve, and `ansible` is the key-only service account whose `NOPASSWD` grant is the route back in if anything later goes wrong.

The work is a new play, `playbooks/account-passwords.yml`, in the [host-access-baseline](../../Platforms/Ansible/Source/host-access-baseline/README.md) Ansible project. Doing it as a play rather than by hand is what makes it repeatable and what let the verification run on every host instead of a sample.

## State before the change

Root password status read through Ansible immediately before the run, where `P` is a usable password and `L` is locked:

| Kind | Hosts | root before |
| --- | --- | --- |
| LXC | `ansible-01` | `P` |
| LXC | `docker-blue`, `docker-network`, `game-01`, `media-01`, `monitor-01` | `L` |
| VM | `alpha-prod-01`, `app-01`, `edge-01` | `P` |
| VM | `kasm-01`, `security-01`, `splunk-siem` | `L` |

Eight hosts locked, four usable. `ansible-01` had no `dkadi` account at all. Every other host already had `dkadi` in its administrative group.

Two facts I checked before writing anything, because both would have changed the plan:

**No host permits password SSH.** `sshd -T` reports `passwordauthentication no` on all twelve, so giving root a password opened no new login path anywhere. `app-01` and `security-01` report `permitrootlogin without-password`, which is key-only and unaffected by a password. Had any host allowed password authentication for root, this change would have handed the internet a credential to guess.

**`splunk-siem` has no `sudo` group.** It is the one Rocky host in the model and uses `wheel`. The play reads the group database and asserts against whichever of the two exists rather than assuming Debian, so the Rocky host is handled by the same description as the other eleven.

## What I changed

One play, run from `ansible-01`, one host at a time, aborting the whole run on the first failure. Per host it sets root's password, creates `dkadi` where the account is absent, sets `dkadi`'s password where the account already exists, and then verifies its own work.

The two account tasks are separate on purpose. The creation task names the shell, home and group; the password task names only the password. That way setting a password on the eleven existing accounts can never change an existing account's shell or group membership as a side effect.

The play uses `update_password: always`, so it **reports `changed` on every run and always will**. Its job is to converge hosts that drifted between the credential item's two sudo password fields, so it has to overwrite whatever is already there, and a fresh salt produces a different hash each time. `on_create` would look idempotent and would skip every host that already had a password, which is every host the play exists to fix. That reasoning is written into the play, the project README and the validator, because it is the kind of thing a later reader corrects on sight.

An empty password variable hashes to a perfectly valid crypt string. The play therefore asserts both values are present before it touches an account, so a run without credentials fails on its first task instead of giving root an empty password on twelve hosts.

## The bug the first host caught

I ran the play against `media-01` alone before running the fleet. Every account task and both authentication proofs passed, and then the final check failed:

```text
fatal: [media-01]: FAILED! => {"cmd": ["sudo", "-n", "True"], "rc": 1,
"stderr": "sudo: True: command not found"}
```

`argv: [sudo, -n, true]` is not what it looks like. YAML reads the bare `true` as a boolean, Ansible renders it as the string `True`, and sudo goes looking for a command by that name. The check that was supposed to prove automation still worked was incapable of passing.

`playbooks/sudoers-nopasswd.yml` in the same project carried the identical mistake in its own `sudo -n true` check. That play has never been run, so nobody had hit it. I fixed both, quoted the argument, and added a validator rule so the bare boolean cannot come back. Fixing the second file is outside this ticket, and I did it anyway rather than leave a known broken check waiting for whoever runs that play next.

This is the argument for a single-host trial before a fleet run. The bug was in the verification rather than the change, so a twelve-host run would have set every password correctly and then failed at the last step on the first host.

## Verification

Every claim below was read back after the run, not assumed from the run reporting success.

**The play's own assertions.** Per host it asserts root reports a usable password, asserts `dkadi` exists and holds administrative group membership, proves both passwords authenticate, and confirms `sudo -n true` still exits `0` for `ansible`. All twelve hosts passed every assertion, `failed=0` across the recap.

**Proving the passwords rather than the hashes.** Reading a hash back only proves a hash landed. The play authenticates as each account through `su`, with the value passed through the become plugin rather than through any command string. `become` always escalates from the connection user, which is the unprivileged `ansible` account, so `su` really does have to answer a password prompt. If it ran as root instead, `su` would not prompt at all and the check would pass without testing anything.

Per-host result lines from the run:

```text
media-01:      root=P root_auth=ok dkadi_groups=dkadi sudo docker            dkadi_auth=ok
docker-network:root=P root_auth=ok dkadi_groups=dkadi sudo users docker      dkadi_auth=ok
monitor-01:    root=P root_auth=ok dkadi_groups=dkadi sudo docker            dkadi_auth=ok
kasm-01:       root=P root_auth=ok dkadi_groups=dkadi adm cdrom sudo dip lxd dkadi_auth=ok
edge-01:       root=P root_auth=ok dkadi_groups=dkadi cdrom floppy sudo ...  dkadi_auth=ok
app-01:        root=P root_auth=ok dkadi_groups=dkadi cdrom floppy sudo ...  dkadi_auth=ok
alpha-prod-01: root=P root_auth=ok dkadi_groups=dkadi cdrom floppy sudo ...  dkadi_auth=ok
security-01:   root=P root_auth=ok dkadi_groups=dkadi adm cdrom sudo dip ... dkadi_auth=ok
splunk-siem:   root=P root_auth=ok dkadi_groups=dkadi wheel                  dkadi_auth=ok
docker-blue:   root=P root_auth=ok dkadi_groups=dkadi sudo users docker      dkadi_auth=ok
ansible-01:    root=P root_auth=ok dkadi_groups=dkadi sudo                   dkadi_auth=ok
game-01:       root=P root_auth=ok dkadi_groups=dkadi sudo users             dkadi_auth=ok
```

**An independent sweep afterwards.** A separate read-only pass, not part of the play, confirms root reports `P` on all twelve, `dkadi` holds `/bin/bash` and a home directory on all twelve, and `dkadi` is in `sudo` on eleven and `wheel` on `splunk-siem`. The same pass lists `/etc/sudoers.d/` on each host and confirms `ansible-01` holds only `90-ansible`, so no drop-in was created for the new account.

**`ai-agent` still opens a session on all twelve**, tested from `ubuntu-dev` with the workstation key. Each host answered `ai-agent`:

| Host | `ssh ai-agent@host 'id -un'` |
| --- | --- |
| `media-01`, `docker-network`, `monitor-01`, `kasm-01` | `ai-agent` |
| `edge-01`, `app-01`, `alpha-prod-01`, `security-01` | `ai-agent` |
| `splunk-siem`, `docker-blue`, `ansible-01`, `game-01` | `ai-agent` |

**Automation was not disturbed.** `sudo -n true` as `ansible` exits `0` on all twelve, checked after the passwords were set. `sudo -n` exits non-zero rather than prompting, so a host whose grant had broken would have failed the run instead of hanging it.

## How the credentials were handled

Neither value entered a command string, an inventory, a playbook, a log or a repository file. Both were read out of the credential item into a JSON file written with `umask 077`, transferred into a mode-`0700` directory on `ansible-01`, tightened to mode `0600`, and consumed with `-e @file`. Every task that touches a password carries `no_log: true`.

Before the run I confirmed by SHA-256 digest, without reading or printing either value, that the staging file carried the two values I intended and that they were distinct from one another. I had renamed a field in the credential item shortly beforehand, so that check was worth making rather than assuming: it proved the rename had not moved this work onto the wrong value. Which fields those are stays in the unpublished [Linux Host Baseline Standard](../../Security/Hardening/Linux-Host-Baseline-Standard.md), which is the one file permitted to describe where a host account's credentials come from.

Both copies of the staging file are gone. The local copy and the copy on `ansible-01` were removed with `shred -u -z`, and the staging directory was removed. `ls` confirms neither path exists. Neither host keeps a credential from this work.

## What this unblocks, and the warning that goes with it

This was the prerequisite for making sudo ask for root's password with `Defaults rootpw`. That step is now safe to run against all twelve, because all twelve have a root password that is proven to authenticate.

It is only safe while that stays true. Any guest that joins the model later, including anything cloned from `debian13-template` or `ubuntu-cloud-template`, arrives with root locked. Writing `Defaults rootpw` to such a host locks every account out of sudo on it. The play is the check as much as the fix: run it against a new host, confirm it reports `root=P` and `root_auth=ok`, and only then apply the sudo policy.

## Left open

**The credential item still holds duplicate fields.** Three field names hold one value and two hold another. Collapsing them to two fields is deliberately the last step of this effort, because several steps still read fields by their current names, and renaming early breaks them.

**`ansible-01`'s `dkadi` account has no key.** It is password-only until a key is placed, which belongs to `ssh-key-automation` rather than to this project. Nothing depends on it today: the SSH Manager reaches that host as `ansible`.

**The ticket's own arithmetic was wrong.** It says seven hosts need root unlocked, and its table lists eight. The table matched the live state, and eight is the number I acted on.
