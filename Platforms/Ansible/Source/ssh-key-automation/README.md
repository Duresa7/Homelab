# SSH Identity Automation

**Created:** 2026-07-14  
**Last updated:** 2026-07-27

I use this project to onboard and rotate SSH public-key identities. Semaphore can launch these files, but the same commands work directly through Ansible.

## Change Boundaries

- Every identity has its own file and target allowlist under `identities/`.
- An identity may select its own POSIX account, authorized-keys path, & OpenSSH restrictions. Other identities keep the host's default key store.
- The public source includes the schema example and `identities/PUBLICATION-NOTICE.md` instead of the environment-specific identity files. The validator detects that layout.
- Onboarding and staging use additive operations and never delete other keys.
- Retirement requires a staged replacement, `operator_verified: true`, successful prechecks on every selected target, and the confirmation phrase `RETIRE <identity-id>`.
- The four Proxmox nodes share one cluster-backed file. Only `grey-server` writes it; the other nodes independently verify the resulting state.
- The nine running workload guests connect as `ansible`. Human identities still resolve to their original `root` or administrative-user key stores through passwordless privilege escalation.
- `docker-blue` & `media-01` are supported Linux targets. Their identity allowlists remain explicit, like every other host.
- I removed the retired domain controllers and `obi-pc` from the inventory on 2026-07-27. No Windows host remains in this project.

## Direct Ansible Commands

Run commands from this directory on `ansible-01`.

```bash
export LANG=C.utf8 LC_ALL=C.utf8
python3 tests/validate_project.py
ansible-playbook playbooks/ssh-key-audit.yml -e ssh_identity=jedi-pc
```

Add an existing key only to the hosts currently missing it:

```bash
ansible-playbook playbooks/ssh-identity-onboard.yml \
  -e ssh_identity=jedi-pc \
  -e ssh_target_group=ssh_key_missing
```

I don't run that onboarding command until I'm ready to test the new host records.

## Rotation Workflow

1. Generate the replacement key on its owner device.
2. Put only the public key in that identity's `rotation.replacement_public_key` field.
3. Stage it with `ssh-key-stage.yml`.
4. Run `ssh-key-verify.yml`, then manually test SSH from the owner device to every assigned target.
5. Set `rotation.operator_verified: true` only after those owner-device tests pass.
6. Retire the old key with `ssh-key-retire.yml` and the phrase `RETIRE <identity-id>`.
7. After successful retirement, promote the replacement into `current_public_key`, update `fingerprint`, clear `replacement_public_key`, and reset `operator_verified` to `false`.

Example retirement command:

```bash
ansible-playbook playbooks/ssh-key-retire.yml \
  -e ssh_identity=jedi-pc \
  -e 'ssh_retire_confirmation=RETIRE jedi-pc'
```

## Adding a New SSH Device

Copy `identities/_new-device-template.yml.example` to `identities/<device-id>.yml`. Replace its sample values with the public key, verified fingerprint, and approved target list. Set `posix_account`, `authorized_keys_path`, & `authorized_key_options` only when that identity needs a different account or restrictions. Then run the project validator and `ssh-identity-onboard.yml` with that identity ID.

The template is intentionally invalid until edited so an example key can never be deployed by accident.

## Semaphore

`semaphore/task-templates.yml` defines the UI. Every template points to the same repository, inventory, identity files, & playbooks used by the direct commands above.
