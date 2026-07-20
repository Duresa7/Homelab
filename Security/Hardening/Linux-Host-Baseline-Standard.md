# Linux Host Baseline Standard

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

Every Linux VM or LXC I provision gets this baseline before it carries a workload or enters the SSH Manager inventory. This file defines the required end state. Windows hosts are out of scope and follow their records under `Platforms/Windows Servers/`.

Work terms & evidence mechanics are defined in the [Documentation Standard](../../Governance/Documentation-Standard.md#work-terms).

## Required Baseline

1. **Patch on first boot.** Run `apt update && apt upgrade -y` on Debian or Ubuntu, or the distribution's equivalent such as `dnf upgrade -y` on RHEL-family systems. A host doesn't enter service with pending security updates.
2. **Administrative user `<YOUR_ADMIN_USERNAME>`.** Create the user, add it to the `sudo` group, and grant passwordless sudo through a validated `/etc/sudoers.d/90-<YOUR_ADMIN_USERNAME>` drop-in (`<YOUR_ADMIN_USERNAME> ALL=(ALL:ALL) NOPASSWD: ALL`). SSH Manager & Ansible need unattended privilege escalation, so an interactive sudo prompt would stop the fleet jobs.
3. **Console recovery.** Set a console password for `<YOUR_ADMIN_USERNAME>` after creating the account. SSH remains key-only, so this path is available from the hypervisor console rather than TCP/22.
4. **Authorized keys.** Install exactly these three public keys into `/home/<YOUR_ADMIN_USERNAME>/.ssh/authorized_keys` (file `0600`, dir `0700`, owned by `<YOUR_ADMIN_USERNAME>`):

   ```text
   <YOUR_ADMIN_KEY_ONE_PUBLIC_KEY>
   <YOUR_ADMIN_KEY_TWO_PUBLIC_KEY>
   <YOUR_ADMIN_KEY_THREE_PUBLIC_KEY>
   ```

   These keys represent my two administrative machines and the Ansible control node.
5. **SSH hardening drop-in.** Write `/etc/ssh/sshd_config.d/99-hardening.conf` with:

   ```text
   PermitRootLogin no
   PubkeyAuthentication yes
   PasswordAuthentication no
   KbdInteractiveAuthentication no
   ```

   Validate with `sshd -t` before restarting the service. Key-only SSH removes password authentication from TCP/22, and `PermitRootLogin no` blocks direct root access.
6. **Lock root.** Leave the `root` account password-locked. Administration runs through `<YOUR_ADMIN_USERNAME>` and sudo.
7. **Locale and timezone.** Set the timezone to `America/New_York` and ensure `en_US.UTF-8` is generated and active. Matching timestamps let me compare events across hosts without converting time zones.

## Verification Checklist

Confirm each result before declaring the host ready:

- `id <YOUR_ADMIN_USERNAME>` shows membership in `sudo`; `sudo -n true` succeeds (NOPASSWD works).
- `sudo sshd -T` reports `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no`.
- `ssh-keygen -lf /home/<YOUR_ADMIN_USERNAME>/.ssh/authorized_keys` lists all three expected fingerprints.
- `passwd -S root` shows the root password locked (`L`).
- The host is reachable over SSH as `<YOUR_ADMIN_USERNAME>` using a key, and not with a password.
- Timezone and locale are correct.

## Operating Decisions

- NOPASSWD is the fleet default because SSH Manager & `ansible-control` run unattended privileged commands. I record a host-level exception with that host.
- `docker-network` LXC CTID 107 is the reference implementation for this baseline.
- I still apply these controls per host. A future cloud-init snippet or Ansible playbook belongs under `Engineering/Automation/` and must use this file as its specification.
