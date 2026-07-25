# Dedicated Ansible Account and Fleet Expansion

**Created:** 2026-07-25  
**Last updated:** 2026-07-25

**Implementation date:** 2026-07-25  
**Systems:** `ansible-01` and nine running Linux workload guests  
**Status:** Implementation complete; independent audit pending

## Scope

I created one dedicated `ansible` account on the controller and these nine guests: docker-main, docker-network, docker-blue, media-01, alpha-prod-01, app-01, edge-01, security-01, & splunk-siem. I expanded OS updates to those nine hosts and Compose updates to five hosts with sixteen projects.

I left `kasm-01`, the four Proxmox nodes, Windows systems, stopped Supabase, stopped `ai-bravo-02`, package versions, & running container definitions outside this rollout. I did not power on a stopped guest, install an update, pull an image, or recreate a container.

## Starting State

- Fleet updates connected through several root or workload-owner accounts. Some needed an interactive sudo password.
- The controller key lived beside human keys in the former root or administrative-user authorized-keys files.
- docker-blue and media-01 were absent from the fleet update inventory.
- The active OS inventory included stopped or retired guests.
- The controller had an invalid `fedora-dev` identity file containing placeholder key data.

## Decisions

1. **Use one automation account.** The same account name, console-recovery password, sudo rule, & controller key policy now apply across the active fleet.
2. **Keep SSH key-only.** The shared password is for local or Proxmox console recovery. TCP 22 rejects password and keyboard-interactive authentication.
3. **Restrict the controller key.** Each authorized-key line accepts only source `192.168.40.36` and disables agent forwarding, port forwarding, X11 forwarding, & PTY allocation.
4. **Use passwordless sudo for automation.** `/etc/sudoers.d/90-ansible` grants `NOPASSWD: ALL` and passes `visudo -cf`.
5. **Keep human identities separate.** SSH identity automation resolves `ansible-control` to `/home/ansible/.ssh/authorized_keys`; other identities continue to use their original root or administrative-user files.
6. **Become root for Compose updates.** The account remains in the `docker` group on all five Compose hosts, but the playbook becomes root so it can read protected project `.env` files without widening their permissions.

## Actions and Results

| Step | Action | Observed result | Evidence |
|---|---|---|---|
| S01 | Created the console credential in 1Password | Login item `the console login entry` exists in the `the managed vault` vault; the concealed value passed the 32-character letters, digits, & symbols recipe | [Account and SSH verification](../../Evidence/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25/Logs/S01-Account-and-SSH-Verification-2026-07-25.md) |
| S02 | Bootstrapped the controller and nine guests one at a time | Every account has an active password, restricted controller key, validated sudo rule, key-only SSH, & the expected administrative group; the five Compose hosts also have Docker access | [Account and SSH verification](../../Evidence/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25/Logs/S01-Account-and-SSH-Verification-2026-07-25.md) |
| S03 | Removed the controller key from former root or admin files after each new login passed | Exact old-key match count is zero on all nine guests; the restricted key remains present under `ansible` | [Account and SSH verification](../../Evidence/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25/Logs/S01-Account-and-SSH-Verification-2026-07-25.md) |
| S04 | Expanded and deployed both automation projects | Validators report 9 OS hosts, 5 Compose hosts, 16 projects, 16 supported SSH hosts, 2 unknown hosts, & 4 valid live identities | [Automation verification](../../Evidence/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25/Logs/S02-Automation-and-Service-Verification-2026-07-25.md) |
| S05 | Ran live identity, ping, privilege, & check-mode tests | All nine hosts passed identity audit, ping, root UID, OS check mode, & Compose check mode | [Automation verification](../../Evidence/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25/Logs/S02-Automation-and-Service-Verification-2026-07-25.md) |
| S06 | Verified the new Compose targets and media VPN path | RustDesk has `hbbs` and `hbbr` running; media has eight running services, healthy Jellyfin and Gluetun, working endpoints, & qBittorrent in Gluetun's namespace | [Automation verification](../../Evidence/Dedicated%20Ansible%20Account%20and%20Fleet%20Expansion%20-%202026-07-25/Logs/S02-Automation-and-Service-Verification-2026-07-25.md) |

## Resulting Fleet

`os_update_targets` contains docker-main, docker-network, docker-blue, media-01, alpha-prod-01, app-01, edge-01, security-01, & splunk-siem. Eight use apt and splunk-siem uses dnf.

`docker_compose_targets` contains:

| Host | Projects |
|---|---|
| docker-main | booklore, forgejo, homelab-dashboard-aio, immich, portainer, termix |
| docker-network | netbird, nginx-proxy-manager |
| docker-blue | rustdesk |
| media-01 | media-stack with profile `vpn` |
| alpha-prod-01 | playit-agent, portainer-edge-agent, teamspeak, teamspeak-02, teamspeak-03, ts3-manager |

## Credential Handling

I retrieved the generated value only through the 1Password CLI. I wrote it to a one-user ACL staging file, transferred it without putting the value in a command, applied it through `chpasswd`, & removed each remote copy before moving to the next host. I overwrote and deleted the local staging file after the final controller check.

splunk-siem blocks Guest Agent command execution. I used its existing 1Password sudo credential through a separate restricted staging file, completed the same root-owned setup over SSH, & shredded both remote credential files. No password value entered a transcript, repository file, evidence record, or shell command.

## Findings During Rollout

- media-01 allowed only `<YOUR_ADMIN_USERNAME>` through SSH. I added `ansible`; its socket-activated daemon then failed during reload and returned 19 seconds later after I restarted the socket and service together. The [troubleshooting record](../../../Media%20Stack/Documentation/Troubleshooting/SSH%20Reload%20Failed%20During%20Ansible%20Account%20Onboarding%20-%202026-07-25.md) holds the cause and checks.
- security-01 loaded `PasswordAuthentication yes` from `50-cloud-init.conf` before the main-file `no`. I added an earlier hardening drop-in, validated it, reloaded SSH, & confirmed the effective value is `no`.
- Compose check mode first failed on protected `.env` files. I changed the play to use the account's validated passwordless sudo, reran syntax and project checks, & completed all sixteen dry-run project checks.
- The live `fedora-dev` identity contained placeholder public-key and fingerprint values. I preserved it under the controller's private `identities/Archive/` folder and left the four valid identities active.
- The deployed project directories were mode `0777`. I removed group and other write permission, set both roots to `0755`, and kept live identity files at `0600` under a `0700` directory.

## Verification Boundary

The OS and Compose playbooks ran with `--check`. Their `changed=True` results mean work would be required during a real run. No package, image, or container changed during onboarding. The first real update remains an explicit operating action.

## Rollback

1. Restore the controller key to the former root or administrative-user authorized-keys file and test that path before removing an `ansible` key or account.
2. Restore the previous inventory from Git if a host must leave the active fleet.
3. Remove `/etc/sudoers.d/90-ansible`, the account, & its home only after another verified administration path exists.
4. Keep the 1Password item until every account using the shared console password is disabled or rotated.
5. Re-run the identity audit, fleet ping, root UID check, & both check-mode playbooks after any rollback.
