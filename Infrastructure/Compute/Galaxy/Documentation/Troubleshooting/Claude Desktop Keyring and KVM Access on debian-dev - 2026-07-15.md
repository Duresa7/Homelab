# Claude Desktop Keyring and KVM Access on `debian-dev`

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-15  
**Owner:** Galaxy VM 102 / `debian-dev`  
**Resolved:** 2026-07-22  
**Status:** Resolved

## Reproduction

Claude Desktop warned that sign-in would not be saved without an installed and unlocked system keyring. Cowork separately reported that `<YOUR_ADMIN_USERNAME>` lacked permission to use `/dev/kvm`.

My tight reproduction combined Claude's `safeStorage` log with the live Secret Service tree. Claude selected `gnome_libsecret` but logged `isEncryptionAvailable=false`; the D-Bus service answered normally while `/org/freedesktop/secrets/collection/login` was absent.

## Root cause

GNOME Keyring was already installed, enabled, running, and integrated into both GDM authentication/session PAM and password changes. The login journal proved PAM successfully handed the login password to the daemon. The decisive timing evidence was that `login.keyring` was created at 18:31:31, exactly when Claude first launched, 42 minutes after the authenticated GNOME session began. Chromium then logged that the login collection object did not exist, disabled libsecret to avoid deadlock, and requested a keyring restart or reboot before the next launch.

The virtualization problem was independent and direct: `/dev/kvm` was correctly `root:kvm` mode `0660`, but the `kvm` group had no members. The VM exposes `svm`, and the `kvm_amd` and `kvm` modules were already loaded.

## Corrective action

I added `<YOUR_ADMIN_USERNAME>` to group `kvm`. I didn't change the keyring packages, PAM files, or keyring database. A blank unlock probe didn't export the new login collection, so I completed a normal GNOME sign-out & sign-in to create a session with the updated group list & an initialized login collection.

## Verification

The account database reported `kvm:x:993:<YOUR_ADMIN_USERNAME>`, and the KVM device, CPU feature, & kernel modules passed before the session restart. After the fresh GNOME login on 2026-07-22, Claude retained sign-in & Cowork used `/dev/kvm` without the prior permission error.

I retained no new terminal transcript or screenshot from the final interactive check. The closure evidence is the observed application behavior: the Claude sign-in survives relaunch & Cowork's KVM workflow opens without the original warning.
