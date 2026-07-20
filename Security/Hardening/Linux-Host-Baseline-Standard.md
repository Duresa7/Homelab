# Linux Host Baseline Standard

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

Every Linux VM or LXC I provision gets this baseline before it carries a workload or is added to the SSH Manager inventory. It defines the required end state and my reasoning behind each choice; the exact commands live in the deploying project's step evidence. Windows hosts are out of scope and follow their own records under `Platforms/Windows Servers/`.

Work terms & evidence mechanics are defined in the [Documentation Standard](../../Governance/Documentation-Standard.md#work-terms).

## Required Baseline

1. **Patch on first boot.** Bring the host fully current before anything else: `apt update && apt upgrade -y` on the Debian/Ubuntu family, or the distribution's equivalent (`dnf upgrade -y` on RHEL-family). *Why: a host should never enter service behind on security updates.*
2. **Administrative user `<YOUR_ADMIN_USERNAME>`.** Create the user, add it to the `sudo` group, and grant passwordless sudo via a validated `/etc/sudoers.d/90-<YOUR_ADMIN_USERNAME>` drop-in (`<YOUR_ADMIN_USERNAME> ALL=(ALL:ALL) NOPASSWD: ALL`). *Why: NOPASSWD keeps the SSH Manager and Ansible automation working without a stored sudo password, which is the fleet's operating model; see the note below.*
3. **Console recovery.** Set a console password for `<YOUR_ADMIN_USERNAME>` after creating the account. SSH remains key-only, so this path is available from the hypervisor console rather than TCP/22.
4. **Authorized keys.** Install exactly these three public keys into `/home/<YOUR_ADMIN_USERNAME>/.ssh/authorized_keys` (file `0600`, dir `0700`, owned by `<YOUR_ADMIN_USERNAME>`):

   ```text
   <YOUR_ADMIN_KEY_ONE_PUBLIC_KEY>
   <YOUR_ADMIN_KEY_TWO_PUBLIC_KEY>
   <YOUR_ADMIN_KEY_THREE_PUBLIC_KEY>
   ```

   *Why: these are the three approved administrative endpoints (my two admin machines and the Ansible control node); public keys are safe to record here.*
5. **SSH hardening drop-in.** Write `/etc/ssh/sshd_config.d/99-hardening.conf` with:

   ```text
   PermitRootLogin no
   PubkeyAuthentication yes
   PasswordAuthentication no
   KbdInteractiveAuthentication no
   ```

   Validate with `sshd -t` before restarting the service. *Why: key-only SSH with no root login removes password brute-forcing and direct root access as attack paths.*
6. **Lock root.** Leave the `root` account password-locked; administration is via `<YOUR_ADMIN_USERNAME>` and sudo. *Why: no interactive root login means no shared root credential to leak or rotate.*
7. **Locale and timezone.** Set the timezone to `America/New_York` and ensure `en_US.UTF-8` is generated and active. *Why: consistent timestamps across the fleet make logs and evidence comparable.*

## Verification Checklist

Confirm and capture each as step evidence before declaring the host ready:

- `id <YOUR_ADMIN_USERNAME>` shows membership in `sudo`; `sudo -n true` succeeds (NOPASSWD works).
- `sudo sshd -T` reports `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no`.
- `ssh-keygen -lf /home/<YOUR_ADMIN_USERNAME>/.ssh/authorized_keys` lists all three expected fingerprints.
- `passwd -S root` shows the root password locked (`L`).
- The host is reachable over SSH as `<YOUR_ADMIN_USERNAME>` using a key, and not with a password.
- Timezone and locale are correct.

## Notes

- **Passwordless sudo is a deliberate fleet decision.** SSH Manager & `ansible-control` run unattended privileged commands. An interactive sudo prompt would stop those jobs, so NOPASSWD is the fleet default. I record any host-level exception in that host's record.
- **Reference implementation.** I built the `docker-network` LXC (CTID 107) to this baseline, capturing step evidence for every command in that deployment.
- **Automation is the natural next step.** I currently perform these actions per host. A cloud-init snippet or Ansible playbook that enforces this baseline would belong under `Engineering/Automation/` and reference this standard as its specification.
