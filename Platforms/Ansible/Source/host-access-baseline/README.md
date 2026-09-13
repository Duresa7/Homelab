# Host Access Baseline

**Created:** 2026-08-15  
**Last updated:** 2026-09-12

I use this project to own accounts and sudo policy on the Linux guests. Semaphore can launch these files, but the same commands work directly through Ansible.

It exists because `ssh-key-automation` should keep meaning what its README says. That project places and rotates keys for registered identities. Creating a POSIX account and writing a sudoers file are a different job, so they live here instead of being bolted onto it. The one key file this project writes belongs to the `ai-agent` account it creates.

## Change Boundaries

- Every host connects as `ansible`, which already holds passwordless root on all of them. `ansible-01` runs through a local connection guarded by a hostname assertion.
- The Proxmox nodes are absent. Node root access is the cluster-backed key file that `ssh-key-automation` owns, not a POSIX account.
- `ubuntu-dev` and `docker-main` are outside the model by decision and appear in no group. `ubuntu-dev` is the single-account workstation, and `docker-main` stays root-login only. The validator fails if either turns up in a target group.
- The Wazuh host is `security-01`, matching the other Ansible projects and SSH Manager.
- `ai_agent_key_only` is empty after Game 01’s retirement on 2026-09-12.
- The `ai-agent` key carries **no** restriction prefix: no `from=`, no forwarding limits, no `no-pty`. That is a decision taken on 2026-08-14, not an omission. The validator fails if a restriction appears, so a later reader cannot quietly "fix" it.
- The key itself lives in `vars/ai-agent-key.yml`, which is gitignored. The repository publishes only `vars/ai-agent-key.yml.example`, following `ssh-key-automation/identities/`. The validator fails if a real key reaches the example, if the playbook hardcodes one, or if the gitignore entry disappears. See [vars/PUBLICATION-NOTICE.md](vars/PUBLICATION-NOTICE.md).
- The console password is only ever applied at account creation. A run without the credential will not lock an account that already has one.
- Every playbook here runs one host at a time and aborts the whole play on the first failure. A broken sudoers file is the one mistake here that removes an account's own route to root, so it must never reach a second host.
- Sudoers files are written through `visudo -cf` against a temp path and moved into place only on exit 0. `ansible.builtin.copy` with `validate` does exactly that, so the rule is enforced by the module rather than by hand.
- `sudoers-rootpw.yml` writes `/etc/sudoers.d/00-rootpw` holding `Defaults rootpw`, which makes every sudo prompt on the host ask for **root's** password instead of the invoking user's. Stock sudo authenticates the invoking user's own password, so this is the only mechanism that makes the login password and the sudo password two different values. The `00-` prefix keeps the file first in the lexical order `/etc/sudoers.d` is read in.
- That play will not write to a host it has not cleared. `Defaults rootpw` where root's password is locked removes sudo from every account at once, and the way back is the Proxmox console, so the play proves root's password **authenticates** on the host in front of it before writing anything there, and stops the whole run on the first host that cannot prove it. A status letter from `passwd -S` is not that proof: it says a hash is present, not that the hash is the value you hold.
- It reads the resulting policy with `sudo -l -U <user>` as root rather than `sudo -l` as the user. Once `rootpw` is in force, `sudo -l` authenticates too, so a password-gated account cannot run it unattended. This caught the play out on the first host it ran against, and the replacement is the better check anyway: `sudo -l -U` reports the Defaults sudo actually resolved, so finding `rootpw` there proves the setting is in force where a file that parses only proves a file that parses.
- Its negative proof reports `untestable` rather than passing on any host where `dkadi` still holds a `NOPASSWD` drop-in, which was four hosts on 2026-08-20 and none since 2026-09-07, when the last four came off by hand. The branch stays in the play for any host that arrives with a drop-in. `NOPASSWD` skips authentication entirely, so the login password would be "refused" there only in the sense that it was never read. The play detects the grant by testing it, not by looking for a filename: `media-01` calls its drop-in `dkadi` where the others use `90-dkadi`, so a filename sweep reports that host as compliant when it is not.
- `account-passwords.yml` is the only play here that writes to `/etc/shadow`. It owns `root` and `dkadi` on all ten and touches nothing else: `ai-agent` already carries the standard password everywhere, and `ansible` is a key-only service account that keeps its `NOPASSWD` grant and stays the route back in.
- That play **reports `changed` on every run, by design.** It uses `update_password: always` because its job is to converge hosts that drifted between the credential item's two sudo password fields, and a fresh salt produces a new hash each time. Reverting it to `on_create` to make the run look idempotent would skip every host that already has a password, which is every host it exists to fix. The validator fails if the setting changes.
- An empty password variable hashes to a perfectly valid crypt string, so the play asserts both values are present before it touches an account. A run without credentials fails on the first task instead of giving root an empty password on ten hosts.
- Reading a hash back only proves a hash landed. The play proves both passwords **authenticate**, by becoming the account through `su` with the value passed via the become plugin rather than any command string. `become` always escalates from the connection user, so this really is `su` from the unprivileged `ansible` account and really does answer a password prompt.
- `splunk-siem` is the one Rocky host and has no `sudo` group; its administrative group is `wheel`. The play reads the group database and asserts against whichever of the two exists, rather than assuming Debian.
- Nothing here writes to sshd. The account playbook reads `sshd -T` and reports the effective `PasswordAuthentication` value, so a run proves the setting was left alone rather than assuming it.
- It also fails the host if sshd carries an `AllowUsers` or `AllowGroups` list that does not admit `ai-agent`. media-01 had `AllowUsers dkadi ansible` on 2026-08-15: the account and key installed correctly, the play reported success, and the login was still refused before sshd ever read the key. A run that looks clean while the account is unreachable is the worst outcome available here, so it is now a hard failure with the fix spelled out in the message. Adding the account to that list is a manual step: validate with `sshd -t`, reload, and keep a second session open. The pre-edit copy of that file is committed at `Backups/media-01-sshd-60-hardening-2026-08-15.conf`, verbatim because it holds no withheld values, and the copy on media-01 is deleted. The file is now `60-media-01-hardening.conf` and its `AllowUsers` line reads `dkadi ansible ai-agent`.

## Inventory Groups

| Group | Hosts | What happens |
|---|---|---|
| `ai_agent_targets` | media-01, docker-network, monitor-01, edge-01, app-01, alpha-prod-01, security-01, splunk-siem, docker-blue, ansible-01 | Account created, key installed |
| `ai_agent_key_only` | None | Reserved for key-only onboarding |
| `dkadi_nopasswd_targets` | edge-01, app-01, alpha-prod-01, security-01, splunk-siem, docker-blue | **Superseded.** Would have given `dkadi` a NOPASSWD drop-in |

The six `dkadi` hosts are the ones that still authenticate for sudo, and under the 2026-08-15 model they stay that way. The group is kept because the superseded play still refers to it, not because anything should be run against it.

`sudoers-rootpw.yml` targets all ten, `ai_agent_targets` and `ai_agent_key_only` together, because the sudo prompt changes everywhere, not only where `dkadi` authenticates.

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

**`sudoers-nopasswd.yml` is superseded and refuses to run.** It writes NOPASSWD grants for `dkadi` and `ai-agent`, which the 2026-08-15 decision reverses: `dkadi` is password-gated, with a sudo prompt that asks for root's password by way of `Defaults rootpw`, and `ai-agent` holds no sudo at all on the guests as of 2026-09-07. The play is kept as the record of what was planned, and it asserts on its first task unless `sudoers_nopasswd_acknowledged=true` is passed. Do not pass it without re-reading the fleet access priority in the root [TODO](../../../../TODO.md).

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

`RP` is root's password and `SP` is the standard login password, both read straight out of the credential item rather than typed. Which fields those are is in the unpublished Linux Host Baseline Standard, the one file allowed to say where a host account's credentials come from. JSON is what makes the file safe to build from a value containing quotes or backslashes.

Point sudo at the root password. Same staging pattern, and both values are required: root's because it is what the prompt will ask for, the login password because the play proves it is now refused. Run one host first and read the result before the rest:

```bash
ansible-playbook playbooks/sudoers-rootpw.yml -e @~/.hab-run/vars.json -e target=docker-blue
ansible-playbook playbooks/sudoers-rootpw.yml -e @~/.hab-run/vars.json
```

A host whose root password is locked is refused rather than written to, so this is also the safe way to bring a newly provisioned guest onto the policy: run `account-passwords.yml` against it first, confirm `root=P` and `root_auth=ok`, then run this.

One host or one group:

```bash
ansible-playbook playbooks/ai-agent-account.yml -e target=media-01
ansible-playbook playbooks/account-passwords.yml -e @~/.hab-run/vars.json -e target=media-01
```

## Verification

Every playbook verifies its own work and fails the host rather than reporting success.

`ai-agent-account.yml` reads back `ssh-keygen -lf` on the file it wrote and asserts exactly one key, matching the expected comment. `sudoers-nopasswd.yml` runs `visudo -c` before and after, then proves each granted account with `sudo -n true`, which exits non-zero instead of prompting. It is superseded and guarded, so none of that runs without an explicit acknowledgement.

`sudoers-rootpw.yml` parses the sudoers configuration before and after, proves root's password authenticates before it writes, then proves what the prompt accepts and refuses afterwards by feeding each value to `sudo -S` on stdin. It asserts `rootpw` appears among the Defaults `sudo -l -U` resolves, and reconfirms `sudo -n true` for `ansible` on every host. A second run reports no changes.

`account-passwords.yml` asserts `passwd -S root` reports a usable password, asserts `dkadi` holds administrative group membership, then proves both passwords by authenticating as the account through `su`. It also confirms `sudo -n true` still works for `ansible` on every host, so a run that disturbed automation fails instead of finishing quietly.

A second run of the first two playbooks reports no changes. `account-passwords.yml` always reports changed, for the reason in the change boundaries above.

## Semaphore

`semaphore/task-templates.yml` defines the UI. Every password is a `secret` survey variable, and the validator fails if any of them ever changes to a plain one.
