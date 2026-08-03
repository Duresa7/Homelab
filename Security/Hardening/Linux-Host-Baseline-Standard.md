# Linux Host Baseline Standard

**Created:** 2026-07-11  
**Last updated:** 2026-08-03

Every Linux VM or LXC I provision gets this baseline before it carries a workload or enters the SSH Manager inventory. This file defines the required end state. Windows hosts are out of scope and follow their records under `Platforms/Windows Servers/`.

## Required Baseline

1. **Patch on first boot.** Run `apt update && apt upgrade -y` on Debian or Ubuntu, or the distribution's equivalent such as `dnf upgrade -y` on RHEL-family systems. A host doesn't enter service with pending security updates.
2. **Administrative user `dkadi`.** Create the user, add it to the `sudo` group, and apply the host's human-administration sudo policy. SSH Manager uses this account for direct maintenance.
3. **Console recovery.** Set a console password for `dkadi` after creating the account. SSH remains key-only, so this path is available from the hypervisor console rather than TCP/22.
4. **Human authorized keys.** Install the approved human public keys into `/home/dkadi/.ssh/authorized_keys` (file `0600`, dir `0700`, owned by `dkadi`):

   ```text
   <YOUR_ADMIN_KEY_ONE_PUBLIC_KEY>
   <YOUR_ADMIN_KEY_TWO_PUBLIC_KEY>
   ```

   The Ansible controller key doesn't belong in this file.
5. **Dedicated automation account.** Create `ansible` with a home directory & `/bin/bash`, add it to the platform's administrative group, and write `/etc/sudoers.d/90-ansible` as `ansible ALL=(ALL:ALL) NOPASSWD: ALL`. Validate the file with `visudo -cf`. Set its shared console-recovery password, but never enable SSH password authentication.
6. **Restricted controller key.** Put only the controller public key in `/home/ansible/.ssh/authorized_keys`, with directory mode `0700`, file mode `0600`, & ownership `ansible:ansible`. Prefix the key with `from="<CONTROLLER_ADDRESS>",no-agent-forwarding,no-port-forwarding,no-X11-forwarding,no-pty`. Add `ansible` to the `docker` group only on hosts where Compose automation must reach the Docker socket.
7. **SSH hardening drop-in.** Write `/etc/ssh/sshd_config.d/99-hardening.conf` with:

   ```text
   PermitRootLogin no
   PubkeyAuthentication yes
   PasswordAuthentication no
   KbdInteractiveAuthentication no
   ```

   Validate with `sshd -t` before restarting the service. Key-only SSH removes password authentication from TCP/22, and `PermitRootLogin no` blocks direct root access.
8. **Lock root.** Leave the `root` account password-locked. Administration runs through `dkadi` or `ansible` and sudo.
9. **Locale and timezone.** Set the timezone to `America/New_York` and ensure `en_US.UTF-8` is generated and active. Matching timestamps let me compare events across hosts without converting time zones.

## Verification Checklist

Confirm each result before declaring the host ready:

- `id dkadi` shows the expected administrative-group membership.
- `id ansible` shows the platform's administrative group; `sudo -n true` succeeds as `ansible`.
- `sudo sshd -T` reports `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no`.
- `ssh-keygen -lf /home/dkadi/.ssh/authorized_keys` lists the approved human fingerprints without the controller key.
- `ssh-keygen -lf /home/ansible/.ssh/authorized_keys` lists only the controller fingerprint, and the authorized-key line carries every required restriction.
- `passwd -S root` shows the root password locked (`L`).
- The host is reachable over SSH as `dkadi` and `ansible` using their assigned keys, and not with a password.
- `docker info` succeeds as `ansible` only on approved Compose hosts.
- Timezone and locale are correct.

## Operating Decisions

- NOPASSWD is required for the dedicated `ansible` account because controller jobs run unattended. I keep human sudo policy separate from automation access.
- The controller password exists for local or Proxmox console recovery. Ansible playbooks, inventory, logs, & repository files never contain it.
- `docker-network` LXC CTID 107 is the first rollout host for this automation baseline.
- I still apply these controls per host. A future cloud-init snippet or Ansible playbook belongs under `Engineering/Automation/` and must use this file as its specification.
