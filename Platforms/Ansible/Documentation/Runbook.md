# SSH Identity Automation Runbook

**Created:** 2026-07-14  
**Last updated:** 2026-07-30

I run these commands on `ansible-01` as the `ansible` account from `/home/ansible/ssh-key-automation`.

## Start Every Session

```bash
cd /home/ansible/ssh-key-automation
export LANG=C.utf8 LC_ALL=C.utf8
python3 tests/validate_project.py
```

The validator contacts no host. It checks key fingerprints, identity allowlists, the retired-host exclusion, playbook paths, and the Semaphore manifest.

## Runtime Health

Run inside `ansible-01`:

```bash
export LANG=C.utf8 LC_ALL=C.utf8
ansible-community --version
ansible --version
semaphore version
systemctl is-enabled semaphore
systemctl is-active semaphore
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/
```

The expected release baseline is Ansible 14.2.0, ansible-core 2.21.2, and Semaphore 2.18.27. The service checks should return `enabled`, `active`, and HTTP `200`.

The state checker compares the live database with the pre-upgrade copy and reports structural differences:

```bash
python3 /opt/homelab/ansible-tools/verify_semaphore_state.py \
  /root/database.sqlite \
  /root/semaphore-backups/upgrade-2026-07-14/database.sqlite
```

For a future online SQLite backup, use the native tool with a new destination path; it refuses to overwrite an existing file, sets mode 0600, and removes a failed output:

```bash
python3 /opt/homelab/ansible-tools/backup_semaphore_sqlite.py \
  /root/database.sqlite \
  /root/semaphore-backups/<change-name>/database.sqlite
```

On `grey-server`, confirm that the controller itself is configured to return after a Proxmox-node boot:

```bash
pct config 100 | grep -E '^(hostname|onboot):'
```

Expected: `hostname: ansible-01` and `onboot: 1`.

## Audit One Identity

```bash
ansible-playbook playbooks/ssh-key-audit.yml -e ssh_identity=jedi-pc
```

Substitute `mac` or `ansible-control` as needed. Audit is read-only and reports `present`, `missing`, or `unreachable` without printing key material.

To audit a safe subset, supply either an inventory group or a JSON host list:

```bash
ansible-playbook playbooks/ssh-key-audit.yml \
  -e ssh_identity=jedi-pc \
  -e ssh_target_group=ssh_key_missing
```

## Add an Existing Key to Missing Machines

Preview first:

```bash
ansible-playbook playbooks/ssh-identity-onboard.yml --check \
  -e ssh_identity=jedi-pc \
  -e ssh_target_group=ssh_key_missing
```

When the machines are reachable and I'm ready to test from the device itself, I remove `--check`. Onboarding is additive: it does not remove the Mac, Ansible Control, Jedi PC, or any unrelated authorized key.

## Add a New SSH-Capable Device

1. Generate the key on the new device.
2. Copy `identities/_new-device-template.yml.example` to `identities/<device-id>.yml`.
3. Put only the public key and its verified SHA256 fingerprint in the new file.
4. Replace the example target list with the approved hosts.
5. Run the validator and syntax check.
6. Preview onboarding with `--check`.
7. Run onboarding without `--check`.
8. Test SSH from the new device itself.

Example:

```bash
python3 tests/validate_project.py
ansible-playbook --syntax-check playbooks/ssh-identity-onboard.yml
ansible-playbook playbooks/ssh-identity-onboard.yml --check -e ssh_identity=new-device
ansible-playbook playbooks/ssh-identity-onboard.yml -e ssh_identity=new-device
```

The example identity file is deliberately invalid until edited, so its placeholder can never be deployed accidentally. New valid identity files are allowed; the validator requires the four baseline identities but does not limit the inventory to only four.

## Rotate One Identity

This example rotates Jedi PC without touching the other identities.

1. Generate the replacement key on Jedi PC.
2. Put its public key in `identities/jedi-pc.yml` under `rotation.replacement_public_key`.
3. Leave `operator_verified: false`.
4. Stage the replacement beside the old key:

```bash
ansible-playbook playbooks/ssh-key-stage.yml -e ssh_identity=jedi-pc
```

5. Verify both keys:

```bash
ansible-playbook playbooks/ssh-key-verify.yml -e ssh_identity=jedi-pc
```

6. From Jedi PC, manually test every assigned machine.
7. Set `operator_verified: true` only after those tests pass.
8. Retire the old Jedi PC key:

```bash
ansible-playbook playbooks/ssh-key-retire.yml \
  -e ssh_identity=jedi-pc \
  -e 'ssh_retire_confirmation=RETIRE jedi-pc'
```

9. Promote the replacement to `current_public_key`, update `fingerprint`, clear `replacement_public_key`, set `operator_verified: false`, and rerun the validator and audit.

Do not retire while a selected target is offline. The precheck deliberately blocks the entire removal gate.

## Semaphore

Semaphore is a convenience layer over three ordinary Ansible projects. The repository, inventory, environment, views, & task templates for each project are defined in that project's `semaphore/task-templates.yml`.

| Project | Templates | Views |
|---|---:|---:|
| `Server-SSH` | 13 | 5 |
| `Fleet-Updates` | 6 | 3 |
| `Monitoring-Exporters` | 4 | 3 |

`All` is Semaphore's aggregate view. `Server-SSH` keeps focused views for onboarding & the three current identities. `Fleet-Updates` separates package work from Compose work. `Monitoring-Exporters` separates node_exporter from cAdvisor.

I check manifest drift with a short-lived API token. The default command is read-only:

```bash
sudo sh -c 'umask 077; semaphore --config /root/config.json users token create \
  --login <YOUR_SEMAPHORE_LOGIN> --name ansible-manifest-check --ttl 15m \
  > /root/semaphore-api-token.tmp'

sudo python3 /opt/homelab/ansible-tools/reconcile_semaphore.py \
  --token-file /root/semaphore-api-token.tmp \
  /home/ansible/ssh-key-automation/semaphore/task-templates.yml \
  /home/ansible/fleet-updates/semaphore/task-templates.yml \
  /home/ansible/monitoring-exporters/semaphore/task-templates.yml
```

The final line should report 3 projects & 0 actions. To apply reviewed drift, add `--apply --expire-token --private-key-file /home/ansible/.ssh/id_ed25519`. The private-key option is used only when a project credential is missing or when I explicitly add `--refresh-credential`. Absent templates & views are retained unless I add `--prune`; I review that deletion list before applying it. I remove `/root/semaphore-api-token.tmp` after the command. The token never belongs in this repository or an evidence transcript.

The monitoring playbooks don't have Semaphore dry-run templates. Ansible check mode doesn't create the node_exporter staging archive & skips the verification modules, so the command-line preview exits with errors even when the installed exporters answer. The exact limitation is in [Monitoring exporter check mode cannot complete](Troubleshooting/Monitoring%20exporter%20check%20mode%20cannot%20complete%20-%202026-07-30.md).

If Semaphore is unavailable, I run the same playbooks directly; no automation depends on the UI.

## Recovery

- Controller project before deployment: [Legacy Controller Project](../../../Archive/Platforms/Ansible/Legacy%20Controller%20Project%20-%202026-07-29/README.md) in this repository. The `/home/ansible/backups/` tarball it replaces is gone as of 2026-07-29; every file inside it was byte-identical to the archived copies, which carry the admin username as a placeholder.
- Controller known-hosts before deployment: a redacted copy sits beside that archive as a record. It is not a restore source, and it doesn't need to be: none of its 24 host keys were missing from the live `known_hosts`. Re-accept a host key from the host itself if one is ever needed.
- Semaphore project export before UI changes: `/root/semaphore-backups/server-ssh-before-identity-automation-2026-07-14.json`
- Runtime-upgrade backup set: `/root/semaphore-backups/upgrade-2026-07-14`

The runtime backup set contains the pre-upgrade Semaphore 2.17.33 binary, SQLite database, configuration, package inventory, installed Ansible Python packages, verified 2.18.27 installer, & `SHA256SUMS`.

To roll back Ansible, repoint `/opt/ansible-current` and the `/usr/local/bin/ansible*` command links to a retained versioned runtime. If no upstream runtime is usable, remove only those shadowing command links to expose the still-installed Debian packages in `/usr/bin`, then validate the project before running a playbook.

To roll back Semaphore, stop `semaphore.service`, restore the saved 2.17.33 binary plus the saved `/root/config.json` and `/root/database.sqlite`, reload systemd if its unit changed, and start the service. Verify SQLite integrity and HTTP 200 before allowing tasks to run.

For a mistaken additive onboarding, remove only that identity's exact public-key material after another administrative path is verified. For a partial retirement, reinstall the recorded old public key through a surviving credential, then rerun the audit before continuing.
