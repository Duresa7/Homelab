# Galaxy Debian Dev GNOME Installation

**Created:** 2026-07-15  
**Last updated:** 2026-07-17

**Status:** Complete  
**Target:** Galaxy VM 102 on `grey-server`  
**Guest hostname:** `debian-dev`  
**Address:** `192.168.40.135/24`

## Scope

Add the renamed Debian development VM to SSH Manager with the existing Jedi-PC identity, install the newest GNOME desktop supported by the VM's Debian 13 stable repositories, activate the graphical login, and verify system health without exposing key material.

## Starting State

- Proxmox reported VM 102 running with the object name `db-13-dev`; the guest reported hostname `debian-dev`.
- The guest ran Debian GNU/Linux 13.6 with 4 vCPU, 4 GiB RAM, a 60 GiB disk, and 51 GiB free.
- SSH listened on TCP/22 and the documented Jedi-PC public key was already authorized, but the guest was absent from SSH Manager.
- No GNOME desktop, GNOME Shell, or GDM package was installed.
- Debian 13 stable offered `gnome-shell 48.7-0+deb13u2`, `gdm3 48.0-2`, and `task-gnome-desktop 3.81`.

## Decisions

- The canonical SSH Manager name is `debian_dev`, matching the guest hostname. The old requested name remains as compatibility alias `db_13_test`.
- The complete Debian `task-gnome-desktop` task was selected because the request was for a GNOME desktop environment, not only the shell. Debian's supported packages were used instead of mixing unstable or third-party repositories.
- Proxmox snapshot `pre-gnome-20260715` was created before package installation because removing a full desktop task is not a clean inverse operation.
- The VM was rebooted only after explicit operator confirmation. Post-boot validation had to prove SSH recovery and automatic graphical startup before the change could close.

## Actions and Results

1. Confirmed the Jedi-PC public-key fingerprint matched the private-key path already used by SSH Manager for `REDACTED_USER_001` hosts.
2. Added `debian_dev` at `192.168.40.135` to the SSH Manager environment, hot-reloaded the configuration, and completed an authenticated health check.
3. Refreshed APT metadata, simulated the full desktop installation, verified guest and thin-pool capacity, and created the pre-change snapshot.
4. Installed `task-gnome-desktop`, selected `graphical.target`, and started GDM.
5. Verified package integrity, the active Wayland greeter, GNOME Shell and Xwayland processes, active SSH, zero failed systemd units, 47 GiB remaining disk space, and an overall healthy SSH Manager health result.
6. After operator approval, rebooted VM 102 through Proxmox and verified a new boot ID, restored SSH access, active GDM and GNOME greeter processes, clean package state, zero failed units, and a cleared reboot-required marker.
7. Repaired GNOME's wired-network question mark by moving `ens18` from legacy ifupdown/dhcpcd ownership to a native NetworkManager profile while preserving address `192.168.40.135` and the existing gateway/DNS.
8. Added a Polkit rule that grants all Polkit-controlled actions to `REDACTED_USER_001` only from the active local GNOME session, eliminating graphical authentication prompts without extending the rule to remote SSH sessions.
9. Removed a redundant legacy 1Password APT `.list` entry while retaining the package-maintained deb822 `.sources` definition and signing key.
10. Diagnosed Claude Desktop's non-persistent sign-in warning as a first-run ordering edge case: GNOME Keyring and PAM were healthy, but Claude created `login.keyring` after the current authenticated session began and Chromium disabled libsecret when the new collection object was not yet exported.
11. Added `REDACTED_USER_001` to the `kvm` group for Claude Cowork. The persistent account membership, `/dev/kvm` ownership, AMD virtualization flag, and loaded `kvm_amd` module were verified; activation and end-to-end Claude checks await the required GNOME sign-out/sign-in.

The SSH Manager client timed out at five minutes while the large package transaction continued remotely. Live process and log checks proved that `apt-get` and `dpkg` remained active and progressing. The transaction subsequently completed with all requested packages in the `ii` state.

## Resulting Configuration

| Setting | Result |
| --- | --- |
| SSH Manager target | `debian_dev` |
| Compatibility alias | `db_13_test` |
| SSH account | `REDACTED_USER_001` |
| Identity | Jedi-PC Ed25519 key; fingerprint verified without exposing private material |
| Desktop task | `task-gnome-desktop 3.81` |
| GNOME metapackage | `gnome 1:48+2` |
| GNOME Shell | `48.7-0+deb13u2` |
| GDM | `48.0-2`, active |
| Default boot target | `graphical.target` |
| Graphical session | GDM Wayland greeter with GNOME Shell and Xwayland observed |
| Wired network owner | NetworkManager profile `Wired connection 1`, autoconnect enabled |
| IPv4 configuration | Static `192.168.40.135/24`; gateway and DNS `192.168.40.1` |
| Connectivity probe | Disabled; Debian's packaged probe endpoint did not resolve from this network |
| GNOME Polkit policy | `/etc/polkit-1/rules.d/49-REDACTED_USER_001-gnome-nopasswd.rules`; `REDACTED_USER_001` + active + local only |
| 1Password APT source | `/etc/apt/sources.list.d/1password.sources`; stable/main AMD64 with the vendor keyring |
| Claude credential backend | GNOME Keyring 48 / Secret Service; login collection created on Claude's first launch and pending a fresh authenticated session |
| Claude Cowork virtualization | `/dev/kvm` via supplementary group `kvm`; `REDACTED_USER_001` is a persistent member, with `svm`, `kvm_amd`, and `kvm` present |
| Rollback point | `pre-gnome-20260715` |

## Verification

- `dpkg --audit` returned no findings and `apt-get check` completed successfully.
- GDM was active with main PID 36722; the Wayland greeter, GNOME Shell, and Xwayland were running.
- `systemctl --failed --no-legend` returned no units.
- SSH remained active, and the SSH Manager health check returned `overall_status: healthy`.
- Root filesystem use increased from 1.4 GiB to 5.8 GiB and remained at 12% used.
- The controlled reboot changed the boot ID from `REDACTED_PASSWORD_HASH_001` to `REDACTED_PASSWORD_HASH_002`.
- After reboot, SSH and `qemu-guest-agent` were active, GDM automatically entered the active state, the Wayland greeter stack was present, and `/run/reboot-required` was absent.
- After the network repair, NetworkManager reported global state `connected` and `ens18:ethernet:connected:Wired connection 1` three consecutive times.
- A NetworkManager service restart proved the profile autoconnected while preserving `.135`, the default route, DNS, HTTPS internet access, and SSH.
- Polkit approved PackageKit install and system reboot actions without prompting when checked against the active local GNOME Shell subject.
- The same PackageKit Polkit action remained denied from the remote SSH shell, while the existing `sudo -n` path remained passwordless.
- Two consecutive APT metadata refreshes completed without duplicate-source warnings; 1Password `8.12.28` remained installed and available from the retained vendor repository.
- GNOME Keyring packages, the enabled user daemon, Secret Service D-Bus ownership, GDM PAM hooks, and the active local Wayland session all passed inspection. Claude's journal captured the missing login collection object and Chromium's explicit restart/reboot remediation.
- The account database now reports `kvm:x:993:REDACTED_USER_001`; `/dev/kvm` remains `root:kvm` mode `0660`, and nested AMD virtualization is available through the loaded KVM modules.

## Rollback

If GNOME causes an unacceptable regression, shut down or otherwise place VM 102 in an appropriate maintenance state and roll back to Proxmox snapshot `pre-gnome-20260715`. Verify hostname, SSH, networking, and package state afterward. The post-reboot checks passed, so the snapshot may be removed later under normal snapshot-retention housekeeping.

To restore GNOME's ordinary Polkit authentication prompts without rolling back the VM, remove `/etc/polkit-1/rules.d/49-REDACTED_USER_001-gnome-nopasswd.rules` and restart `polkit.service`. The prior state had no file at that path.

To restore the retired legacy 1Password source for troubleshooting, copy `/root/apt-source-backups/1password.list.pre-dedup-20260715` back to `/etc/apt/sources.list.d/1password.list` with mode 0644. Doing so while `1password.sources` remains enabled will intentionally restore the duplicate warnings.

To remove Claude Cowork's KVM permission, run `gpasswd -d REDACTED_USER_001 kvm` and start a new login session. The keyring diagnosis did not delete or rewrite any stored keyring data.

## Remaining Work

- Optional housekeeping: remove snapshot `pre-gnome-20260715` when its short-term rollback value is no longer needed.
- Save any desktop work, sign out of GNOME, sign back in with the normal account password, and relaunch Claude. Then verify the new GNOME process contains group 993, the login Secret Service collection is exported, Claude no longer logs `isEncryptionAvailable=false`, and Cowork can open `/dev/kvm`.

## Step Evidence

| Step | Evidence | Verification result |
| --- | --- | --- |
| S01 | [Preflight and identity](../../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S01-Preflight-And-Identity-2026-07-15.md) | Guest identity, repository candidate, capacity, and passwordless sudo confirmed |
| S02 | [SSH registration and snapshot](../../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S02-SSH-And-Snapshot-2026-07-15.md) | New target authenticated and rollback snapshot appeared in Proxmox |
| S03 | [Complete APT install log](../../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S03-GNOME-Package-Install-2026-07-15.log) | GNOME task, Shell, session, and GDM packages configured |
| S04 | [Final verification](../../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S04-Final-Verification-2026-07-15.md) | Package, display-manager, SSH, systemd, disk, and health checks passed |
| S05 | [Controlled reboot and post-boot verification](../../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S05-Controlled-Reboot-2026-07-15.md) | A new boot completed with SSH, GDM, GNOME greeter, graphical target, and system health restored |
| S06 | [NetworkManager indicator repair](../../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S06-NetworkManager-Indicator-Repair-2026-07-15.md) | GNOME-facing wired state and NetworkManager autoconnect passed while address, route, DNS, and SSH remained stable |
| S07 | [GNOME Polkit passwordless policy](../../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S07-GNOME-Polkit-Passwordless-2026-07-15.md) | Active local GNOME actions were approved without a prompt while remote Polkit remained denied |
| S08 | [1Password APT source deduplication](../../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S08-1Password-APT-Source-Deduplication-2026-07-15.md) | Duplicate warnings cleared twice while repository signing and package visibility remained intact |
| S09 | [Claude keyring and KVM repair](../../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S09-Claude-Keyring-And-KVM-Repair-2026-07-15.md) | Root cause and persistent KVM membership confirmed; final Secret Service and `/dev/kvm` checks await a fresh GNOME login |
