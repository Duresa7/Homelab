# SSH Identity Automation

**Created:** 2026-07-14  
**Last updated:** 2026-07-20

**Implementation date:** 2026-07-14  
**Status:** Complete  
**Primary owner:** Platforms/Ansible  
**Affected systems:** `ansible-01`; Semaphore; 15 supported SSH targets; controller known-hosts

## Scope

I implemented a reusable Ansible workflow that can onboard a new SSH public-key identity or rotate exactly one existing identity without replacing unrelated keys. Semaphore stays as an optional click-to-run interface over ordinary Ansible files. I rotated, replaced, added, and removed no current key during implementation.

The four baseline identities are Mac, Ansible Control, Jedi PC, & Termix. Each replacement begins on the device that owns it.

## Starting State

- `ansible-01` used a non-Git legacy directory at `/home/ansible/ansible`.
- One playbook hard-coded three public keys into broad host groups; it had no per-identity rotation lifecycle or safe old-key retirement gate.
- The inventory was stale and still named the retired `nas-family` LXC.
- Semaphore 2.17.33 pointed at the legacy directory and exposed one `Distribute SSH Keys` template.
- The controller trusted only part of the managed fleet's host keys.
- `ws-dc-2-secondary` and `obi-pc` had not been safely inventoried and needed to remain out of scope.

## Automation Boundaries

- I keep one identity file per SSH origin. This is the boundary that prevents a Jedi PC operation from changing Mac, Ansible Control, or Termix.
- Onboarding and staging are additive. Deletion exists only in the dedicated retirement playbook after all preconditions pass.
- Retirement requires a distinct replacement, presence of both keys on every target, an owner-device login test, `operator_verified: true`, an exact confirmation phrase, and full reachability.
- I let target accounts manage their own authorized-key files instead of introducing sudo solely for this workflow.
- I gave `grey-server` sole write responsibility for the Proxmox cluster-backed key file while all four nodes independently verify it.
- Unknown Windows machines stay non-selectable until their actual authorized-key store and connectivity are verified.
- I treat Semaphore as a launcher, not the source of truth. The project continues to work with normal `ansible-playbook` commands when Semaphore is unavailable.
- I kept the existing Semaphore project because its CLI export couldn't reproduce the working execution configuration in a second project.

## Actions and Observed Results

1. Inventoried the controller, Ansible collections, legacy project, Semaphore process, SQLite configuration, project objects, & existing key records.
2. Created recovery copies of the legacy Ansible directory and Semaphore project export.
3. Built `/home/ansible/ssh-key-automation` with a YAML inventory, four identity files, a deliberately invalid new-device template, five playbooks, POSIX and Windows task implementations, a validator, and an 18-template Semaphore manifest.
4. Added allowlist validation and non-selectable unknown targets. The retired `nas-family` name is rejected by the validator and absent from inventory.
5. Implemented exact algorithm-plus-key-material comparison, so public-key comments remain labels rather than identity boundaries.
6. Added a multi-stage retirement gate that stays closed when any selected host is missing either key or is unreachable.
7. Added Windows check-mode support with `SupportsShouldProcess`; predicted writes are never persisted during preview.
8. Corrected the initial key parser after a read-only audit exposed false missing results.
9. Independently compared controller scans with authenticated target ED25519 fingerprints before updating `ansible-01` known-hosts. I retained a rollback copy.
10. Determined that UniFi allowed the remaining SSH attempts. I added no firewall policy; four supported hosts and both unknown Windows machines were offline or host-side unreachable.
11. Ran the validator and syntax checks for all five playbooks successfully.
12. Proved the safety gates: missing replacement, retirement, and unknown-host tests all failed on localhost before mutation; Termix onboarding check mode predicted two additions and a following audit proved neither was written.
13. Ran final read-only audits for all four identities. Every reachable host completed with `changed=0`; no current key was added, removed, or rotated.
14. Reconfigured the existing Semaphore project in the authenticated UI: retained `ansible-key`, updated the repository, inventory, and locale variable group, created 18 focused templates, added a separate Onboarding view, and removed the obsolete `Distribute SSH Keys` template without launching a task.

## Resulting Project

| Component | Result |
|---|---|
| Supported hosts | 15 |
| Unknown, non-selectable hosts | 2 (`ws-dc-2-secondary`, `obi-pc`) |
| Baseline identities | 4 |
| Direct playbooks | Audit, Onboard, Stage, Verify, Retire |
| Semaphore templates | 18 across five focused views, plus the aggregate `All` view |
| Privilege escalation | None required by this workflow |

## Final Key-State Audit

- Mac, Ansible Control, and Jedi PC were present on all 11 reachable supported targets.
- Termix was present on its nine existing targets.
- Termix remained missing on `security-01` and `splunk-siem`; the check-mode test changed neither host.
- `supabase-01`, `ai-alpha-01`, `ai-bravo-02`, and `ws-dc-1-main` were unreachable.
- `ws-dc-2-secondary` and `obi-pc` timed out and remain unknown/out of scope.

## Verification

| Check | Observed result |
|---|---|
| Project validator | Exit 0: four identities, 15 supported, two unknown, 18 Semaphore templates |
| Playbook syntax | All five playbooks passed |
| Replacement gate | Stage and retire blocked when replacement data was empty |
| Retirement gate | Requires owner verification, exact phrase, both keys, and full reachability |
| Unknown target | `obi-pc` rejected before contact |
| Check mode | Predicted Termix additions; following audit showed both still missing |
| Final audits | Reachable hosts `changed=0`, `failed=0`; offline hosts explicitly unreachable |
| Network diagnosis | UniFi flows allowed controller SSH; no policy change made |
| Semaphore UI | 18 templates total; four in each identity view, two in Onboarding, 18 in aggregate All; all remained Not launched |

## Rollback

1. Stop using the new playbooks and fall back to the archived legacy project only if immediate recovery is necessary.
2. Restore `/home/ansible/backups/ansible-before-ssh-identity-automation-2026-07-14.tar.gz` to recover the legacy directory.
3. Restore `/home/ansible/backups/known_hosts-before-ssh-identity-automation-2026-07-14` if a controller known-host entry must be rolled back.
4. Use `/root/semaphore-backups/server-ssh-before-identity-automation-2026-07-14.json` as the supported Semaphore project-level recovery reference.

No authorized-key rollback is necessary for this implementation because all live key operations were audits, rejected gate tests, or check-mode previews.

## Remaining Work

- Re-run the full audits when the four offline supported hosts return.
- Classify `ws-dc-2-secondary` and `obi-pc` only after their SSH service, account, and actual authorized-key location are verified.
- Add the existing Termix key to candidate hosts only when I'm ready to test those connections from Termix itself.
