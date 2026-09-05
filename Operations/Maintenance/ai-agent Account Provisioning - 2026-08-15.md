# ai-agent Account Provisioning

**Created:** 2026-08-15  
**Last updated:** 2026-08-19

**Change date:** 2026-08-15  
**Status:** Complete. Re-verified 2026-08-19 against the eleven guests that remain after the Kasm retirement  
**Scope:** Create the `ai-agent` account and install its key on the Linux guests. No sudo policy was written

## Outcome

`ai-agent` exists on every Linux guest in the model, each with exactly one authorised key, a `/bin/bash` shell, and a key file at mode `600` owned by the account. An SSH session opens as `ai-agent` on all of them using this workstation's key. A second run of the playbook reports no changes.

The account has **no sudo** anywhere except `game-01`, where a `NOPASSWD` drop-in already existed before this work. That drop-in is not something this change created and it comes off in the sudo policy work that follows.

This is the account the automation on this workstation uses. Before it existed, that work ran as `dkadi`, which is my own account, so nothing in a log distinguished a command I typed from a command a tool issued.

## What built it

A new Ansible project, [host-access-baseline](../../Platforms/Ansible/Source/host-access-baseline/README.md), deployed to `/home/ansible/host-access-baseline` on `ansible-01`. It exists because `ssh-key-automation` should keep meaning what its README says: that project places and rotates keys for registered identities, and creating a POSIX account is a different job. The one key file this project writes belongs to the account it creates.

Every host connects as `ansible`, which already holds passwordless root on each of them. `ansible-01` runs through a local connection guarded by a hostname assertion, so a run from the wrong machine fails rather than configuring the wrong host.

## media-01 refused the login, and the play did not notice

This is the finding worth carrying forward.

The playbook reported `account=present keys=1` on `media-01` and looked completely clean. `ssh ai-agent@media-01` returned `Permission denied (publickey)`. The account, the key, the ownership and the modes were all correct. The cause was `AllowUsers dkadi ansible` in `/etc/ssh/sshd_config.d/60-media-01-hardening.conf`: sshd refused the account before it ever read the key.

A run that installs a key onto an account sshd will not admit is the worst outcome available here, because it looks like success.

A fleet sweep found `media-01` is the **only** host with an account allowlist. Every other guest has no `AllowUsers` or `AllowGroups` at all.

I fixed it by adding `ai-agent` to that line, validating with `sshd -t` before touching the service, and reloading with a second `dkadi` session held open. The pre-edit copy is at `Backups/media-01-sshd-60-hardening-2026-08-15.conf`, verbatim because it holds no withheld values, and the copy on the host is deleted. The file's `AllowUsers` line now reads `dkadi ansible ai-agent`.

**The playbook now catches this class of failure.** It reads `sshd -T`, collects `AllowUsers` and `AllowGroups`, and fails the host with an explicit message if an allowlist exists that does not admit the account. The per-host line ends in `sshd_allowlist=none` or `sshd_allowlist=admits ai-agent`, so the check is visible in a passing run and not only in a failing one.

The reload had a side effect. `ssh.service` went to `failed` because the running `sshd -D` could not re-exec on `HUP` once `/run/sshd` had been cleaned out from under it. `media-01` uses socket activation, so `ssh.socket` kept listening on port 22 throughout and connectivity never dropped; the next connection re-triggered the service, `RuntimeDirectory=sshd` recreated the directory, and the unit came back on its own. The same trap bit `ansible-01` later the same day, where the fatal error was `Cannot bind any address` and the fix is `restart` rather than `reload`. That is written up in [Root SSH Disabled on ansible-01 and security-01](Root%20SSH%20Disabled%20on%20ansible-01%20and%20security-01%20-%202026-08-15.md), and it is the version to read: it names the cause correctly, where my first reading here blamed the missing directory that was actually a symptom.

## Check mode earned its keep

The first `--check` run failed on `media-01` with a message claiming it was a key-only host. That was a real bug rather than a check-mode artefact: the "account is missing on a key-only host" assertion had no `when`, so it fired on every host, and under `--check` the account is never actually created.

I scoped the assertion to the key-only group and gated the key tasks on a recorded fact for whether the account is present. Under `--check` those tasks now skip with an explicit message saying check mode cannot validate what depends on an account it did not create. That is honest rather than a false pass.

## The credential and the key

The account's password is set at creation only, for console recovery, and comes from the standard login field of the credential item the unpublished Linux Host Baseline Standard names. A run without the credential creates a key-only account with a locked password rather than failing, and a run against an account that already has a password will not lock it.

The value never entered a command string, an inventory, a playbook or a log. It was read into a variable, JSON-escaped into a mode-`0600` file so any character survived intact, transferred over SFTP, consumed as `-e @file`, then destroyed with `shred -u -z` on both ends. Every task handling it carries `no_log: true`.

The public key itself lives in `vars/ai-agent-key.yml`, which is gitignored. It was moved there from the playbook before this work finished, because this repository publishes no key material. The repository carries only the example file. The project validator fails if a real key reaches the example, if a playbook hardcodes one, or if the gitignore entry disappears.

## Verification

Read back on 2026-08-15 and again on 2026-08-19, through Ansible as `ansible`:

| Check | Result |
| --- | --- |
| `ai-agent` account present | every guest |
| Keys in `/home/ai-agent/.ssh/authorized_keys` | exactly 1, ED25519, on every guest |
| Key file mode and owner | `600`, `ai-agent:ai-agent`, on every guest |
| `.ssh` directory mode | `700` |
| Shell | `/bin/bash` on every guest |
| SSH session as `ai-agent` with this workstation's key | opens on every guest |
| `sshd -T` `passwordauthentication` | `no` on every guest |
| Second playbook run | `changed=0` |

Password authentication was never enabled anywhere as part of this work.

`game-01` was a special case throughout: its account and its `/etc/sudoers.d/90-ai-agent` already existed, and its `authorized_keys` was 0 bytes, which is the only reason the account was unreachable. This work wrote that one file and created nothing there.

## Fleet change since

The account was provisioned across twelve guests on 2026-08-15. `kasm-01` was retired on 2026-08-19, so eleven remain, and the 2026-08-19 re-verification above covers those eleven. Nothing about the account model changed with that retirement.

## What this deliberately did not do

No sudoers file was written. `ai-agent` logs in everywhere and holds no privilege except on `game-01`, through a grant that predates this work.

That was correct for the model in force on 2026-08-15 and it is still correct now, for a different reason. The plan that day was to give the account passwordless sudo fleet-wide; I reversed that on 2026-08-15 and the account is password-gated instead, with a sudo prompt that asks for root's password. The remaining steps, and the reason the order among them is not negotiable, are in the fleet access priority in the root [TODO](../../TODO.md).
