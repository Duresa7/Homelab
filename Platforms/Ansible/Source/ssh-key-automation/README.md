# SSH Identity Automation

**Created:** 2026-07-14  
**Last updated:** 2026-07-18

This is the Ansible project I use to onboard and rotate SSH public-key identities. Semaphore is an optional launcher over these files; it is not required to operate them.

## Safety Model

- Private keys never enter this repository or Ansible.
- Every identity has its own file and target allowlist under `identities/`.
- This repository omits live identity files and retains only the schema example plus `identities/PUBLICATION-NOTICE.md`; the validator detects the notice and validates without them.
- Onboarding and staging use additive operations and never delete other keys.
- Retirement requires a staged replacement, `operator_verified: true`, successful prechecks on every selected target, and the confirmation phrase `RETIRE <identity-id>`.
- The four Proxmox nodes share one cluster-backed file. Only `grey-server` writes it; the other nodes independently verify the resulting state.
- `ws-dc-2-secondary` and `obi-pc` remain in the `ssh_key_unknown` inventory group and cannot be selected by these playbooks.

## Direct Ansible Commands

Run commands from this directory on `ansible-01`.

```bash
export LANG=C.utf8 LC_ALL=C.utf8
python3 tests/validate_project.py
ansible-playbook playbooks/ssh-key-audit.yml -e ssh_identity=termix
```

Add the existing Termix key only to the currently missing candidate group:

```bash
ansible-playbook playbooks/ssh-identity-onboard.yml \
  -e ssh_identity=termix \
  -e ssh_target_group=termix_candidate_targets
```

I don't run that onboarding command until I'm ready to test the new Termix host records.

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

Copy `identities/_new-device-template.yml.example` to `identities/<device-id>.yml`. Replace its sample values with the public key, verified fingerprint, and approved target list, then run the project validator and `ssh-identity-onboard.yml` with that identity ID.

The template is intentionally invalid until edited so an example key can never be deployed by accident.

## Semaphore

`semaphore/task-templates.yml` is the reproducible UI manifest. Every template points to the same repository, inventory, identity files, and playbooks used by the direct commands above. Semaphore holds the existing `ansible-key` execution credential in its encrypted Key Store; the credential is not exported into this project.
