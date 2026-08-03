# Package Hold Task Failed Before Wazuh Agent Installation

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

## Symptom

The first fleet play stopped on `alpha-prod-01`, `docker-blue`, & `media-01` before installing `wazuh-agent`:

```text
Failed to find package 'wazuh-agent' to perform selection 'install'.
```

The Ansible command exited `2`. `ansible-01` never entered its serial batch.

## Failed Attempt

I placed `ansible.builtin.dpkg_selections` before the APT install to clear a possible package hold. These were new installs. No local `wazuh-agent` package record existed, & APT hadn't refreshed metadata after I created the Wazuh source file.

## Hypotheses and Tests

1. **The repository or signing key failed.** The signing-key download, dearmor, & repository-file tasks all returned success, so that didn't explain a `dpkg_selections` lookup failure.
2. **The requested `4.14.6-1` package was unavailable.** The failure happened before `ansible.builtin.apt` ran, so package-version resolution hadn't occurred.
3. **`dpkg_selections` requires an existing package record.** All three hosts reported the agent absent in preflight, & the module's error named the missing package record. This matched the task boundary.

## Root Cause

The play tried to change a hold before the package existed in dpkg's selections database. The step was unnecessary because the APT task already sets `allow_change_held_packages: true` for later version changes.

## Corrective Action

I removed the pre-install `dpkg_selections selection=install` task. I kept the post-install hold, exact version pin, & disabled repository.

## Verification

The corrected play installed all four reachable hosts and exited `0`. A second run returned `changed=0`, `failed=0`, & `unreachable=0` for each host. The retained transcript is [S03 Reachable Host Deployment](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S03%20Reachable%20Host%20Deployment%20-%202026-08-03.md).

