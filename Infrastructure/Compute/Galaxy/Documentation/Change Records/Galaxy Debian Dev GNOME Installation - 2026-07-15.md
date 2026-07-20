# Galaxy Debian Dev GNOME Installation

**Created:** 2026-07-15  
**Last updated:** 2026-07-20

**Status:** Complete  
**Target:** Galaxy VM 102 on `grey-server`  
**Guest hostname:** `debian-dev`  
**Address:** `192.168.40.135/24`

## Scope

I added the renamed Debian development VM to SSH Manager with the existing Jedi-PC identity. I then installed the newest GNOME desktop available from Debian 13 stable, enabled the graphical login, & checked the key fingerprint and system health.

## Starting State

- Proxmox reported VM 102 running with the object name `db-13-dev`; the guest reported hostname `debian-dev`.
- The guest ran Debian GNU/Linux 13.6 with 4 vCPU, 4 GiB RAM, a 60 GiB disk, and 51 GiB free.
- SSH listened on TCP/22 and the documented Jedi-PC public key was already authorized, but the guest was absent from SSH Manager.
- No GNOME desktop, GNOME Shell, or GDM package was installed.
- Debian 13 stable offered `gnome-shell 48.7-0+deb13u2`, `gdm3 48.0-2`, and `task-gnome-desktop 3.81`.

## Decisions

- I made `debian_dev` the canonical SSH Manager name, matching the guest hostname. The old requested name remains as compatibility alias `db_13_test`.
- I selected the complete Debian `task-gnome-desktop` task because I wanted a GNOME desktop environment, not only the shell, and I used Debian's supported packages instead of mixing unstable or third-party repositories.
- I created Proxmox snapshot `pre-gnome-20260715` before package installation because removing a full desktop task is not a clean inverse operation.
- I held the reboot until I was ready to watch it. Post-boot validation had to prove SSH recovery and automatic graphical startup before I closed the change.

## Actions and Results

1. I confirmed the Jedi-PC public-key fingerprint matched the private-key path already used by SSH Manager for `<YOUR_ADMIN_USERNAME>` hosts.
2. I added `debian_dev` at `192.168.40.135` to the SSH Manager environment, hot-reloaded the configuration, and completed an authenticated health check.
3. I refreshed APT metadata, simulated the full desktop installation, verified guest and thin-pool capacity, and created the pre-change snapshot.
4. I installed `task-gnome-desktop`, selected `graphical.target`, and started GDM.
5. I verified package integrity, the active Wayland greeter, GNOME Shell and Xwayland processes, active SSH, zero failed systemd units, 47 GiB remaining disk space, and an overall healthy SSH Manager health result.
6. I rebooted VM 102 through Proxmox and verified a new boot ID, restored SSH access, active GDM and GNOME greeter processes, clean package state, zero failed units, and a cleared reboot-required marker.
7. I repaired GNOME's wired-network question mark by moving `ens18` from legacy ifupdown/dhcpcd ownership to a native NetworkManager profile while preserving address `192.168.40.135` and the existing gateway/DNS.
8. I added a Polkit rule that grants all Polkit-controlled actions to `<YOUR_ADMIN_USERNAME>` only from the active local GNOME session, eliminating graphical authentication prompts without extending the rule to remote SSH sessions.
9. I removed a redundant legacy 1Password APT `.list` entry while retaining the package-maintained deb822 `.sources` definition and signing key.
10. I diagnosed Claude Desktop's non-persistent sign-in warning as a first-run ordering edge case: GNOME Keyring and PAM were healthy, but Claude created `login.keyring` after the current authenticated session began and Chromium disabled libsecret when the new collection object was not yet exported.
11. I added `<YOUR_ADMIN_USERNAME>` to the `kvm` group for Claude Cowork. I verified the persistent account membership, `/dev/kvm` ownership, AMD virtualization flag, and loaded `kvm_amd` module; activation and end-to-end Claude checks await the required GNOME sign-out/sign-in.

My SSH Manager client timed out after five minutes, but the package transaction kept running. Process and log checks showed active `apt-get` and `dpkg` work. The transaction finished with every requested package in the `ii` state.

## Resulting Configuration

| Setting | Result |
| --- | --- |
| SSH Manager target | `debian_dev` |
| Compatibility alias | `db_13_test` |
| SSH account | `<YOUR_ADMIN_USERNAME>` |
| Identity | Jedi-PC Ed25519 key; fingerprint verified |
| Desktop task | `task-gnome-desktop 3.81` |
| GNOME metapackage | `gnome 1:48+2` |
| GNOME Shell | `48.7-0+deb13u2` |
| GDM | `48.0-2`, active |
| Default boot target | `graphical.target` |
| Graphical session | GDM Wayland greeter with GNOME Shell and Xwayland observed |
| Wired network owner | NetworkManager profile `Wired connection 1`, autoconnect enabled |
| IPv4 configuration | Static `192.168.40.135/24`; gateway and DNS `192.168.40.1` |
| Connectivity probe | Disabled; Debian's packaged probe endpoint did not resolve from this network |
| GNOME Polkit policy | `/etc/polkit-1/rules.d/49-<YOUR_ADMIN_USERNAME>-gnome-nopasswd.rules`; `<YOUR_ADMIN_USERNAME>` + active + local only |
| 1Password APT source | `/etc/apt/sources.list.d/1password.sources`; stable/main AMD64 with the vendor keyring |
| Claude credential backend | GNOME Keyring 48 / Secret Service; login collection created on Claude's first launch and pending a fresh authenticated session |
| Claude Cowork virtualization | `/dev/kvm` via supplementary group `kvm`; `<YOUR_ADMIN_USERNAME>` is a persistent member, with `svm`, `kvm_amd`, and `kvm` present |
| Rollback point | `pre-gnome-20260715` |

## Verification

- `dpkg --audit` returned no findings and `apt-get check` completed successfully.
- GDM was active with main PID 36722; the Wayland greeter, GNOME Shell, and Xwayland were running.
- `systemctl --failed --no-legend` returned no units.
- SSH remained active, and the SSH Manager health check returned `overall_status: healthy`.
- Root filesystem use increased from 1.4 GiB to 5.8 GiB and remained at 12% used.
- The controlled reboot changed the boot ID from `<BOOT_ID_BEFORE_REBOOT>` to `<BOOT_ID_AFTER_REBOOT>`.
- After reboot, SSH and `qemu-guest-agent` were active, GDM automatically entered the active state, the Wayland greeter stack was present, and `/run/reboot-required` was absent.
- After the network repair, NetworkManager reported global state `connected` and `ens18:ethernet:connected:Wired connection 1` three consecutive times.
- A NetworkManager service restart proved the profile autoconnected while preserving `.135`, the default route, DNS, HTTPS internet access, and SSH.
- Polkit approved PackageKit install and system reboot actions without prompting when checked against the active local GNOME Shell subject.
- The same PackageKit Polkit action remained denied from the remote SSH shell, while the existing `sudo -n` path remained passwordless.
- Two consecutive APT metadata refreshes completed without duplicate-source warnings; 1Password `8.12.28` remained installed and available from the retained vendor repository.
- GNOME Keyring packages, the enabled user daemon, Secret Service D-Bus ownership, GDM PAM hooks, and the active local Wayland session all passed inspection. Claude's journal captured the missing login collection object and Chromium's explicit restart/reboot remediation.
- The account database now reports `kvm:x:993:<YOUR_ADMIN_USERNAME>`; `/dev/kvm` remains `root:kvm` mode `0660`, and nested AMD virtualization is available through the loaded KVM modules.

## Rollback

If GNOME causes a regression, I'll place VM 102 in maintenance, restore Proxmox snapshot `pre-gnome-20260715`, then check the hostname, SSH, networking, & package state. The post-reboot checks passed, so I can remove the snapshot when I no longer need the short-term rollback point.

To restore GNOME's ordinary Polkit authentication prompts without rolling back the VM, remove `/etc/polkit-1/rules.d/49-<YOUR_ADMIN_USERNAME>-gnome-nopasswd.rules` and restart `polkit.service`. The prior state had no file at that path.

To restore the retired legacy 1Password source for troubleshooting, copy `/root/apt-source-backups/1password.list.pre-dedup-20260715` back to `/etc/apt/sources.list.d/1password.list` with mode 0644. Doing so while `1password.sources` remains enabled will intentionally restore the duplicate warnings.

To remove Claude Cowork's KVM permission, run `gpasswd -d <YOUR_ADMIN_USERNAME> kvm` and start a new login session. The keyring diagnosis did not delete or rewrite any stored keyring data.

## Remaining Work

- Optional housekeeping: remove snapshot `pre-gnome-20260715` when its short-term rollback value is no longer needed.
- Save any desktop work, sign out of GNOME, sign back in with the normal account password, and relaunch Claude. Then verify the new GNOME process contains group 993, the login Secret Service collection is exported, Claude no longer logs `isEncryptionAvailable=false`, and Cowork can open `/dev/kvm`.

## Step Verification

| Step | Work | Verified result |
| --- | --- | --- |
| S01 | Preflight and identity | Guest identity, repository candidate, capacity, and passwordless sudo confirmed |
| S02 | SSH registration and snapshot | New target authenticated and rollback snapshot appeared in Proxmox |
| S03 | GNOME package installation | GNOME task, Shell, session, and GDM packages configured |
| S04 | Final verification | Package, display-manager, SSH, systemd, disk, and health checks passed |
| S05 | Controlled reboot and post-boot verification | A new boot completed with SSH, GDM, GNOME greeter, graphical target, and system health restored |
| S06 | NetworkManager indicator repair | GNOME-facing wired state and NetworkManager autoconnect passed while address, route, DNS, and SSH remained stable |
| S07 | GNOME Polkit passwordless policy | Active local GNOME actions were approved without a prompt while remote Polkit remained denied |
| S08 | 1Password APT source deduplication | Duplicate warnings cleared twice while repository signing and package visibility remained intact |
| S09 | Claude keyring and KVM repair | Root cause and persistent KVM membership confirmed; final Secret Service and `/dev/kvm` checks await a fresh GNOME login |
