# Host Access Baseline

**Created:** 2026-08-15  
**Last updated:** 2026-08-15

I use this project to own accounts and sudo policy on the Linux guests. Semaphore can launch these files, but the same commands work directly through Ansible.

It exists because `ssh-key-automation` should keep meaning what its README says. That project places and rotates keys for registered identities. Creating a POSIX account and writing a sudoers file are a different job, so they live here instead of being bolted onto it. The one key file this project writes belongs to the `ai-agent` account it creates.

## Change Boundaries

- Every host connects as `ansible`, which already holds passwordless root on all of them. `ansible-01` runs through a local connection guarded by a hostname assertion.
- The Proxmox nodes are absent. Node root access is the cluster-backed key file that `ssh-key-automation` owns, not a POSIX account.
- `ubuntu-dev`, `docker-main` and `supabase-01` are outside the model by decision and appear in no group. `ubuntu-dev` is the single-account workstation, `docker-main` stays root-login only, and `supabase-01` is powered off. The validator fails if any of them turns up in a target group.
- The Wazuh host is `security-01` here. The effort spec calls it `wazuh-01`; this name matches every other Ansible project and the SSH manager.
- `game-01` is in `ai_agent_key_only`. Its `ai-agent` account and `/etc/sudoers.d/90-ai-agent` already exist, and its `authorized_keys` was 0 bytes, which is the only reason the account was unreachable. This project writes that one file and creates nothing there.
- The `ai-agent` key carries **no** restriction prefix: no `from=`, no forwarding limits, no `no-pty`. That is a decision taken on 2026-08-14, not an omission. The validator fails if a restriction appears, so a later reader cannot quietly "fix" it.
- The key itself lives in `vars/ai-agent-key.yml`, which is gitignored. The repository publishes only `vars/ai-agent-key.yml.example`, following `ssh-key-automation/identities/`. The validator fails if a real key reaches the example, if the playbook hardcodes one, or if the gitignore entry disappears. See [vars/PUBLICATION-NOTICE.md](vars/PUBLICATION-NOTICE.md).
- The console password is only ever applied at account creation. A run without the credential will not lock an account that already has one.
- Both playbooks run one host at a time and abort the whole play on the first failure. A broken sudoers file is the one mistake here that removes an account's own route to root, so it must never reach a second host.
- Sudoers files are written through `visudo -cf` against a temp path and moved into place only on exit 0. `ansible.builtin.copy` with `validate` does exactly that, so the rule is enforced by the module rather than by hand.
- `account-passwords.yml` is the only play here that writes to `/etc/shadow`. It owns `root` and `dkadi` on all twelve and touches nothing else: `ai-agent` already carries the standard password everywhere, and `ansible` is a key-only service account that keeps its `NOPASSWD` grant and stays the route back in.
- That play **reports `changed` on every run, by design.** It uses `update_password: always` because its job is to converge hosts that drifted between the credential item's two sudo password fields, and a fresh salt produces a new hash each time. Reverting it to `on_create` to make the run look idempotent would skip every host that already has a password, which is every host it exists to fix. The validator fails if the setting changes.
- An empty password variable hashes to a perfectly valid crypt string, so the play asserts both values are present before it touches an account. A run without credentials fails on the first task instead of giving root an empty password on twelve hosts.
- Reading a hash back only proves a hash landed. The play proves both passwords **authenticate**, by becoming the account through `su` with the value passed via the become plugin rather than any command string. `become` always escalates from the connection user, so this really is `su` from the unprivileged `ansible` account and really does answer a password prompt.
- `splunk-siem` is the one Rocky host and has no `sudo` group; its administrative group is `wheel`. The play reads the group database and asserts against whichever of the two exists, rather than assuming Debian.
- Nothing here writes to sshd. The account playbook reads `sshd -T` and reports the effective `PasswordAuthentication` value, so a run proves the setting was left alone rather than assuming it.
- It also fails the host if sshd carries an `AllowUsers` or `AllowGroups` list that does not admit `ai-agent`. media-01 had `AllowUsers dkadi ansible` on 2026-08-15: the account and key installed correctly, the play reported success, and the login was still refused before sshd ever read the key. A run that looks clean while the account is unreachable is the worst outcome available here, so it is now a hard failure with the fix spelled out in the message. Adding the account to that list is a manual step — validate with `sshd -t`, reload, and keep a second session open. The pre-edit copy of that file is committed at `Backups/media-01-sshd-60-hardening-2026-08-15.conf`, verbatim because it holds no withheld values, and the copy on media-01 is deleted. The file is now `60-media-01-hardening.conf` and its `AllowUsers` line reads `dkadi ansible ai-agent`.

## Inventory Groups

| Group | Hosts | What happens |
|---|---|---|
| `ai_agent_targets` | media-01, docker-network, monitor-01, kasm-01, edge-01, app-01, alpha-prod-01, security-01, splunk-siem, docker-blue, ansible-01 | Account created, key installed |
| `ai_agent_key_only` | game-01 | Key file written, nothing created |
| `dkadi_nopasswd_targets` | edge-01, app-01, alpha-prod-01, security-01, splunk-siem, docker-blue | **Superseded.** Would have given `dkadi` a NOPASSWD drop-in |

The six `dkadi` hosts are the ones that still authenticate for sudo, and under the 2026-08-15 model they stay that way. The group is kept because the superseded play still refers to it, not because anything should be run against it.

## Direct Ansible Commands

Run these from this directory on `ansible-01`. On a fresh checkout, put the key in place first:

```bash
cp vars/ai-agent-key.yml.example vars/ai-agent-key.yml
# replace the placeholder with the real public key, then
chmod 600 vars/ai-agent-key.yml
```

```bash
export LANG=C.utf8 LC_ALL=C.utf8
python3 tests/validate_project.py
ansible-playbook playbooks/ai-agent-account.yml --check
```

Create the accounts and install the key. Read the password out of the credential item into the environment so it never reaches the command line, a log, or the shell history:

```bash
ansible-playbook playbooks/ai-agent-account.yml \
  -e "ai_agent_password=$AI_AGENT_PASSWORD"
```

Leave `ai_agent_password` unset to create a key-only account with a locked password. That is the supported outcome when no console credential is available, not a failure.

**`sudoers-nopasswd.yml` is superseded and refuses to run.** It writes NOPASSWD grants for `dkadi` and `ai-agent`, which the 2026-08-15 decision reverses: both accounts are password-gated now, and a sudo prompt asks for root's password by way of `Defaults rootpw`. The play is kept as the record of what was planned, and it asserts on its first task unless `sudoers_nopasswd_acknowledged=true` is passed. Do not pass it without re-reading the fleet access priority in the root [TODO](../../../../TODO.md).

Hold a second root session open on any host you are about to change, and keep it open until the new configuration has been proven.

Set the `root` and `dkadi` passwords. Neither value may reach a command string, the inventory, a log or a tracked file, so they go into a mode-`0600` vars file that is destroyed afterwards:

```bash
install -d -m 700 ~/.hab-run
umask 077
python3 -c 'import json,os; print(json.dumps({
  "root_password": os.environ["RP"], "dkadi_password": os.environ["SP"]}))' \
  > ~/.hab-run/vars.json

ansible-playbook playbooks/account-passwords.yml -e @~/.hab-run/vars.json
shred -u -z ~/.hab-run/vars.json && rmdir ~/.hab-run
```

`RP` is root's password and `SP` is the standard login password, both read straight out of the credential item rather than typed. Which fields those are is in the unpublished [Linux Host Baseline Standard](../../../../Security/Hardening/Linux-Host-Baseline-Standard.md), the one file allowed to say where a host account's credentials come from. JSON is what makes the file safe to build from a value containing quotes or backslashes.

One host or one group:

```bash
ansible-playbook playbooks/ai-agent-account.yml -e target=kasm-01
ansible-playbook playbooks/account-passwords.yml -e @~/.hab-run/vars.json -e target=kasm-01
```

## Verification

Every playbook verifies its own work and fails the host rather than reporting success.

`ai-agent-account.yml` reads back `ssh-keygen -lf` on the file it wrote and asserts exactly one key, matching the expected comment. `sudoers-nopasswd.yml` runs `visudo -c` before and after, then proves each granted account with `sudo -n true`, which exits non-zero instead of prompting. It is superseded and guarded, so none of that runs without an explicit acknowledgement.

`account-passwords.yml` asserts `passwd -S root` reports a usable password, asserts `dkadi` holds administrative group membership, then proves both passwords by authenticating as the account through `su`. It also confirms `sudo -n true` still works for `ansible` on every host, so a run that disturbed automation fails instead of finishing quietly.

A second run of the first two playbooks reports no changes. `account-passwords.yml` always reports changed, for the reason in the change boundaries above.

## Semaphore

`semaphore/task-templates.yml` defines the UI. Every password is a `secret` survey variable, and the validator fails if any of them ever changes to a plain one.
