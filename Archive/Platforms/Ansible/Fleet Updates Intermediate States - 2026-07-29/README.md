# Fleet Updates Intermediate States

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Captured:** 2026-07-29

These nine files are working copies the controller wrote while I changed the `fleet-updates` project during [fleet maintenance](../../../../Platforms/Ansible/Documentation/Change%20Records/Fleet%20Maintenance%20-%202026-07-28.md). Each one is a file as it stood immediately before the next edit. They lived in the deployed project's `playbooks/` directory and in `/home/ansible/fleet-update-backups/`, neither of which should hold old copies. I archived them here on 2026-07-29 and deleted them from `ansible-01`.

Nothing here is live. The current project is [fleet-updates](../../../../Platforms/Ansible/Source/fleet-updates/README.md) in this repository, and the deployed copy on `ansible-01` matches it.

## Reboot rework, in order

Four backups from the evening of 2026-07-29, while I replaced `ansible.builtin.reboot` with explicit steps.

| File | Bytes | State |
|---|---:|---|
| `os-update.yml.bak.20260729_051933` | 4940 | The original path, using `ansible.builtin.reboot`. This is the version that never returned on security-01. 10 tasks. |
| `os-update.yml.bak.20260729_052021` | 7526 | First replacement: a transient `systemd-run` timer, a boot-ID comparison, and `wait_for_connection` instead of the action plugin. 19 tasks. |
| `os-update.yml.bak.20260729_052422` | 8055 | Adds the `rpm -q kernel` fallback so a Rocky guest whose `needs-restarting` helpers don't answer can still prove a pending reboot from a running-versus-installed kernel mismatch. |
| `os-update.yml.bak.20260729_053331` | 8278 | Last in-place state before the committed version. |

The first of those is redundant. Its hash is byte-identical to the version committed in `e85c89c`, so git already held it. The other three were never committed and exist nowhere else, which is why I kept the set whole instead of saving only what was missing. None matches the 8625-byte version committed in `acb8b2c`, so the last capture is one edit short of what shipped.

## Final review pass

Five copies taken before the final review changed the Compose health guard and the pull-retry behavior. These came out of `/home/ansible/fleet-update-backups/2026-07-28-pre-maintenance/`, alongside four other files that turned out to be exactly the `e85c89c~1` state already in git.

| File | Bytes |
|---|---:|
| `README.md.pre-final-review` | 6853 |
| `docker-compose-update.yml.pre-final-review` | 3454 |
| `hosts.yml.pre-final-review` | 3996 |
| `os-update.yml.pre-final-review` | 4411 |
| `validate_project.py.pre-final-review` | 9331 |

None of these five matches any committed version, so this is the only copy of that intermediate state.

## Why the rest of that backup directory went

`/home/ansible/fleet-update-backups/2026-07-28-pre-maintenance/` also held `README.md`, `inventory/hosts.yml`, `semaphore/task-templates.yml`, and `tests/validate_project.py`. I compared all four against git before deleting anything. Every one is byte-identical to the version committed at `e85c89c~1`, which is the pre-maintenance state. `hosts.yml` matches after substituting the admin username for the placeholder, which is the same substitution the project's publication note already describes.

So git is the rollback path, and a better one than an unversioned directory on the host. `git show e85c89c~1:Platforms/Ansible/Source/fleet-updates/<file>` returns any of them.

## Redaction

I replaced the admin username with `dkadi` in `hosts.yml.pre-final-review`. Nothing else needed changing, and no file here holds a key, token, or password. Every download was hash-checked against the controller before I removed the original.
