# Termix Semaphore Templates

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Captured:** 2026-07-29

Termix was destroyed on 2026-07-28, but five of its Semaphore templates outlived it on `ansible-01`. I exported them here and deleted them from Semaphore on 2026-07-29. This is the whole definition of each, so the set can be rebuilt if Termix ever comes back.

Every one ran a playbook from the `ssh-key-automation` repository with `-e ssh_identity=termix`. That identity file is already gone, so each template would have failed on a missing identity rather than done anything. They were dead weight in the UI, not a working path into a destroyed host.

## What I removed

| Semaphore id | Name | Playbook | View |
|---:|---|---|---:|
| 3 | Termix, Add Current Key to Missing Candidates | `playbooks/ssh-identity-onboard.yml` | 6 |
| 16 | Termix, Audit | `playbooks/ssh-key-audit.yml` | 2 |
| 17 | Termix, Stage Replacement | `playbooks/ssh-key-stage.yml` | 2 |
| 18 | Termix, Verify Staged Key | `playbooks/ssh-key-verify.yml` | 2 |
| 19 | Termix, Retire Old Key | `playbooks/ssh-key-retire.yml` | 2 |

The names above use commas where Semaphore stored an em dash, so the table stays readable in this repository. The export below keeps the exact stored strings.

## Exact export

Taken from `project__template` and `project__template_environment` in `/root/database.sqlite`. Fields left at their defaults are omitted. Each template pointed at project 1, inventory 1, repository 1, ran under `app: ansible`, and had `environment_id: 1` attached.

```yaml
templates:
  - id: 3
    name: "Termix — Add Current Key to Missing Candidates"
    playbook: playbooks/ssh-identity-onboard.yml
    arguments: '["-e","ssh_identity=termix","-e","ssh_target_group=termix_candidate_targets"]'
    view_id: 6
    survey_vars: null
  - id: 16
    name: "Termix — Audit"
    playbook: playbooks/ssh-key-audit.yml
    arguments: '["-e","ssh_identity=termix"]'
    view_id: 2
    survey_vars: null
  - id: 17
    name: "Termix — Stage Replacement"
    playbook: playbooks/ssh-key-stage.yml
    arguments: '["-e","ssh_identity=termix"]'
    view_id: 2
    survey_vars: null
  - id: 18
    name: "Termix — Verify Staged Key"
    playbook: playbooks/ssh-key-verify.yml
    arguments: '["-e","ssh_identity=termix"]'
    view_id: 2
    survey_vars: null
  - id: 19
    name: "Termix — Retire Old Key"
    playbook: playbooks/ssh-key-retire.yml
    arguments: '["-e","ssh_identity=termix"]'
    view_id: 2
    survey_vars: >-
      [{"name":"ssh_retire_confirmation","title":"Type RETIRE termix",
      "required":true,"description":"Exact confirmation phrase required
      before the old key can be removed."}]

template_environment:
  - {project_id: 1, template_id: 3, environment_id: 1}
  - {project_id: 1, template_id: 16, environment_id: 1}
  - {project_id: 1, template_id: 17, environment_id: 1}
  - {project_id: 1, template_id: 18, environment_id: 1}
  - {project_id: 1, template_id: 19, environment_id: 1}
```

Common to all five: `project_id: 1`, `inventory_id: 1`, `repository_id: 1`, `app: ansible`, `type: ""`, `tasks: 0`, `task_params: {}`, and zero for `autorun`, `allow_override_args_in_task`, `suppress_success_alerts`, `allow_override_branch_in_task`, and `allow_parallel_tasks`. `description`, `start_version`, `build_template_id`, `git_branch`, and `runner_tag` were all null.

## What I checked before deleting

Nothing else in Semaphore referenced them. Counting rows for template ids 3, 16, 17, 18, and 19 across every table that carries a `template_id`: five in `project__template_environment` and none anywhere else. No task history, no schedules, no integrations, no vault or role attachments, and no other template used one as a `build_template_id`. So the deletion was those five environment rows and the five templates, with nothing orphaned.

Semaphore's single repository is `/home/ansible/ssh-key-automation` and 13 templates remain, covering the Mac, Jedi PC, and Ansible Control identities plus the onboard template. The `ssh-key-automation` project in this repository never listed the Termix templates, so no source file needed changing.

## Related records

- [Termix decommission](../Documentation/Change%20Records/Termix%20Decommission%20-%202026-07-28.md)
- [Termix SSH host onboarding](../Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md)
- [SSH Identity Automation](../../../../Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md)
