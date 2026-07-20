# Ansible SSH Identity Automation Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

## What This Guide Covers

I use Ansible to audit, add, rotate, & retire SSH public keys across Linux, Proxmox, & Windows targets. This walkthrough follows the same project from its inventory and identity files through direct playbook runs and Semaphore.

## Current Status and Verified Versions

The controller is CT 100 `ansible-01` at `192.168.40.36`. The recorded stack runs Ansible 14.2.0, ansible-core 2.21.2, & Semaphore 2.18.27 on TCP 3000. The project has 18 Semaphore templates across six views.

## What You Need

- A Linux controller with Python 3, Ansible, Git, & SSH access to each managed target.
- One execution account; I use `ansible`.
- A public key, SHA-256 fingerprint, & approved target list for each identity.
- Console access to a target in case an SSH change needs recovery.

## How the Pieces Fit Together

> Diagram placeholder

## Walkthrough

### Step 1: Place and Validate the Project

I keep the working copy at `/home/ansible/ssh-key-automation`. From that directory, I install the declared collections and run the project validator before contacting a host.

```sh
ansible-galaxy collection install -r requirements.yml
python3 tests/validate_project.py
```

The validator checks the inventory, identity schema, target references, template manifest, & playbook structure. The public copy can pass without live identity files because it includes only the schema example.

### Step 2: Build the Inventory

I assign each host to the groups used by its connection method and key policy. The four Proxmox nodes share a cluster-backed authorization file, so `grey-server` is the only writer while the other nodes verify the result.

I leave a host in `ssh_key_unknown` until I know its account, path, & connection method. Those hosts can't be selected by the key playbooks.

### Step 3: Define One Identity

I copy `identities/_new-device-template.yml.example` to `identities/<YOUR_DEVICE_ID>.yml`, then replace the sample ID, owner label, public key, fingerprint, & target allowlist. The example is invalid until edited, so it can't deploy its sample value.

### Step 4: Audit Before Writing

I run the audit against one identity first.

```sh
export LANG=C.utf8 LC_ALL=C.utf8
ansible-playbook playbooks/ssh-key-audit.yml -e ssh_identity=<YOUR_DEVICE_ID>
```

I compare the reported state with the identity's allowlist before I run an additive playbook.

### Step 5: Onboard or Stage a Key

For a new identity, I run `ssh-identity-onboard.yml`. For a replacement, I add the new public key to `rotation.replacement_public_key` and run `ssh-key-stage.yml`. Both paths add a key without deleting unrelated entries.

```sh
ansible-playbook playbooks/ssh-identity-onboard.yml \
  -e ssh_identity=<YOUR_DEVICE_ID> \
  -e ssh_target_group=<YOUR_TARGET_GROUP>
```

### Step 6: Verify from the Key Owner

I run `ssh-key-verify.yml`, then connect from the device that owns the private key to every assigned target. I set `rotation.operator_verified: true` only after those direct connections work.

### Step 7: Retire the Old Key

Retirement requires a staged replacement, successful prechecks, the verified flag, & an exact confirmation phrase.

```sh
ansible-playbook playbooks/ssh-key-retire.yml \
  -e ssh_identity=<YOUR_DEVICE_ID> \
  -e 'ssh_retire_confirmation=RETIRE <YOUR_DEVICE_ID>'
```

Afterward, I promote the replacement to `current_public_key`, update the fingerprint, clear the replacement field, & reset the verified flag.

### Step 8: Add Semaphore

I use `semaphore/task-templates.yml` to create the same audit, onboard, stage, verify, & retire jobs in Semaphore. Every template points to the same repository, inventory, identity files, & playbooks used by the direct commands.

## What I Checked After Each Step

- The project validator completed without an error.
- The inventory resolved only approved target groups.
- Audit jobs reported state without writing it.
- Onboarding and staging preserved existing keys.
- Retirement stopped unless all four gates passed.
- Semaphore exposed 18 templates across six views after the recorded upgrade.

## Troubleshooting and Recovery

If a playbook loses access, stop the run and recover the affected account from its console. Re-add the last working public key, rerun the audit for that identity, & don't start retirement until the owner-device test succeeds on every target.

## Known Limits

The public project omits live identity files. `ws-dc-2-secondary` and `obi-pc` remain in `ssh_key_unknown`, so the automation intentionally leaves them alone.

## Source Records

- [Project instructions](../Platforms/Ansible/Source/ssh-key-automation/README.md)
- [Architecture](../Platforms/Ansible/Documentation/Architecture.md)
- [SSH identity automation change record](../Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
- [Ansible and Semaphore upgrade](../Platforms/Ansible/Documentation/Change%20Records/Ansible%20and%20Semaphore%20Upgrade%20-%202026-07-14.md)
- [Controller key distribution report](../Platforms/Ansible/Documentation/ansible-01-key-distribution-report.md)
