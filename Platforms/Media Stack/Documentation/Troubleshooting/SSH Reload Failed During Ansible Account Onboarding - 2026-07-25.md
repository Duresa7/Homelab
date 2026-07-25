# SSH Reload Failed During Ansible Account Onboarding

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

**Affected system:** Galaxy CT 842 `media-01`  
**Observed window:** 2026-07-25 18:45:14 through 18:45:33 UTC  
**Status:** Resolved

## Symptom

The first controller login as `ansible` was rejected because `/etc/ssh/sshd_config.d/60-media-01-hardening.conf` allowed only `<YOUR_ADMIN_USERNAME>`. I added `ansible` to that `AllowUsers` line and validated the configuration with `sshd -t`.

The following `systemctl reload ssh` sent SIGHUP to the socket-activated daemon. The daemon exited with `fatal: Cannot bind any address`, and `ssh.service` entered the failed state. Proxmox console access remained available throughout the 19-second listener interruption.

## Cause

`media-01` runs both `ssh.socket` and `ssh.service`. Reloading the daemon caused it to reopen a port still held by the socket unit. The diagnostic check also found `/run/sshd` absent after the failed reload. The `AllowUsers` edit itself was valid; the service handoff caused the failure.

## Correction

I recreated `/run/sshd` as root with mode `0755`, stopped the failed service, restarted `ssh.socket`, cleared the failed service state, & started `ssh.service`. I kept `AllowUsers <YOUR_ADMIN_USERNAME> ansible` because both accounts require key-only access.

## Verification

- `sshd -t` returned exit code 0.
- `ssh.socket` and `ssh.service` both returned `active`.
- TCP 22 listened on all configured addresses.
- The controller logged in as `ansible` with its restricted key.
- `sudo -n id -u` returned `0`, Docker access passed, & password-only SSH was rejected.
- I removed the controller key from `/home/<YOUR_ADMIN_USERNAME>/.ssh/authorized_keys` only after the new login passed.

## Future Handling

For this socket-activated host, I restart the socket and service together after a validated SSH configuration change. I keep Proxmox console access open until the new listener and a fresh key login both pass.
