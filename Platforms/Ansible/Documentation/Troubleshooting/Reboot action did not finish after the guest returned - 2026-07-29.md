# Reboot action did not finish after the guest returned

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Investigated:** 2026-07-29

## Symptom

The approved security-01 run reached `ansible.builtin.reboot`, rebooted the guest, & stayed on that task until the SSH Manager call reached its five-minute timeout. The remote Ansible process remained in the reboot action afterward.

security-01 was already reachable. Its uptime showed a new boot, `/var/run/reboot-required` was gone, all four Wazuh and Docker units were active, cAdvisor was healthy, & systemd reported no failed unit.

## Failed attempt

The playbook relied on `ansible.builtin.reboot` with `reboot_timeout: 600`. That action did not return after this guest completed its reboot. The retained S08 transcript ends at the reboot task because the calling session timed out before Ansible produced a recap.

I did not issue a second reboot while the first action was still waiting.

## Hypotheses and tests

I tested the guest from a separate Ansible command. SSH ping succeeded, `/proc/uptime` showed the new boot, and service checks passed. That ruled out a guest that was still offline or stuck during startup.

The action process remained in its retry sleep even though a separate connection worked. The retained output does not show which internal boot-time check failed, so I did not assign a narrower cause.

## Root cause

The confirmed failure mode was the action plugin failing to finish its post-reboot verification on security-01. The guest reboot itself succeeded. The available evidence does not identify why the plugin did not accept the new boot.

## Corrective action

I replaced the action plugin with explicit remote steps:

1. Read the guest boot ID.
2. Schedule `systemctl reboot` through a transient systemd timer outside the SSH session.
3. Wait for a new SSH connection.
4. Read the boot ID again & require it to differ.
5. Retry the systemd state until startup checks settle.

The play still runs one automatic reboot at a time. It refuses `reboot=auto` through a local connection, so the controller cannot reboot itself through its local inventory entry.

## Verification

The corrected path rebooted splunk-siem, reconnected over SSH, & proved a changed boot ID before continuing. Its final check-mode pass reported `reboot_required=False` on security-01 and splunk-siem.

The final readback returned `system_state=running` and zero failed units on all 11 in-scope guests. security-01 retained active Wazuh services, healthy cAdvisor, HTTP 302 from the dashboard, & the expected unauthenticated HTTP 401 from the API.

Evidence: [security-01 reboot attempt](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S08-security-01-reboot.log), [splunk-siem corrected reboot path](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S09-splunk-siem-reboot.log), [post-reboot final readback](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S10-post-reboot-final-verification.log), & [final reboot-automation check](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S10c-final-reboot-automation-check.log)

## Follow-up correction on 2026-07-29

Reviewing the replacement afterward, I found a race in step 3. The timer fires `systemctl reboot` at `--on-active=2s` and `wait_for_connection` waits `delay: 5` before its first attempt. If sshd is still answering at that five-second mark, the reconnect succeeds against the guest that hasn't gone down yet, step 4 reads the boot ID it started with, and the assertion fails on a guest that then reboots correctly. The failure points the wrong way: a loud error on a healthy reboot, with the play abandoned while the guest is on its way down.

It didn't happen on either guest. security-01 and splunk-siem both proved a changed boot ID, which is why the review caught this rather than a failed run.

I added a step between the timer and the reconnect that waits for the guest to stop answering on TCP 22, delegated to the controller with a 120-second `reboot_drop_timeout`. A guest that reboots faster than that check samples never appears down, so I set `failed_when: false` on it. The boot ID comparison stays the actual proof of a new boot; the drop wait only stops the reconnect from racing the shutdown.

I deployed the corrected playbook to `/home/ansible/fleet-updates/playbooks/os-update.yml` and confirmed it matches the repository copy at SHA-256 `5153edc3556d14eac5676548668c56ca88a500e27f7918d767da38146fd283b4`. The validator returned `Validation passed: 11 OS-update hosts, 6 compose hosts, 22 projects.`, both plays passed `--syntax-check`, and `--list-tasks` shows the new wait between the boot-ID read and the reconnect. A check-mode run against splunk-siem and docker-network returned `ok=6 changed=0 unreachable=0 failed=0` on both, covering the dnf and apt branches.

The new wait itself is unexercised. No guest currently reports `reboot_required=True`, and the reboot block is skipped under `--check`, so the next guest that genuinely needs a reboot is the first real test of this path.
