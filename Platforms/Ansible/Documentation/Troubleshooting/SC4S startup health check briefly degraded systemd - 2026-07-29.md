# SC4S startup health check briefly degraded systemd

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Investigated:** 2026-07-29

## Symptom

The corrected reboot path proved that splunk-siem completed a new boot, then `systemctl is-system-running --wait` returned `degraded`. One transient Podman health-check service had failed for the SC4S container.

Splunkd and `sc4s.service` were active. SC4S was running with health state `starting`, and Splunk already returned HTTPS 303.

## Failed attempt

The first post-reboot gate sampled systemd once. `systemctl is-system-running --wait` returned as soon as systemd reached `degraded`, so it did not allow SC4S's next scheduled health check to settle the state.

## Hypotheses and tests

The failed transient unit showed this health-check output:

`Error connecting control socket, socket='/var/lib/syslog-ng/syslog-ng.ctl', error='Connection refused'`

The container health configuration uses a 120-second interval and 6 retries. I kept the guest online and inspected the next timer result. That check reached the syslog-ng control socket, returned exit code 0, changed SC4S to healthy, cleared the transient failed unit, & returned systemd to `running`.

## Root cause

The first Podman health timer ran before SC4S had opened its syslog-ng control socket. The one-shot systemd gate treated that expected startup race as a final state.

## Corrective action

I changed the post-reboot gate to retry `systemctl is-system-running` every 10 seconds for up to 30 attempts. A guest with a real failed unit still stops the play after the bounded window, while a startup health timer has time to recover.

## Verification

The next scheduled SC4S health check returned healthy with a failing streak of 0. systemd then returned `running` with zero failed units. The final readback confirmed the new Rocky Linux kernel, active Splunkd and SC4S services, healthy SC4S, an empty dnf update queue, & Splunk HTTPS 303.

The updated playbook passed YAML parsing, its local validator, and Ansible syntax check after deployment.

Evidence: [splunk-siem reboot and first startup sample](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S09-splunk-siem-reboot.log) & [post-reboot final readback](../../Evidence/Fleet%20Maintenance%20-%202026-07-28/Logs/S10-post-reboot-final-verification.log)
