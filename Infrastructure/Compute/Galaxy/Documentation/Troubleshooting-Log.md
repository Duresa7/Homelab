# Galaxy Troubleshooting Log

**Created:** 2026-07-14  
**Last updated:** 2026-07-17

This is the chronological troubleshooting record for the Galaxy Proxmox cluster. Open follow-up work is tracked in the [Galaxy TODO](TODO.md).

## Quick Index

| # | Date investigated | Symptom | Current finding | Status |
|---:|---|---|---|---|
| 1 | 2026-07-13 | Proxmox reported `blue-server` as `unknown` while its guests remained online | `pvestatd` repeatedly crashes and does not restart; the deeper cause is not yet proven | Known issue — deferred |
| 2 | 2026-07-15 | GNOME showed a question mark for wired networking on `debian-dev` although internet access worked | `ens18` was owned by legacy ifupdown/dhcpcd and therefore appeared unmanaged to NetworkManager | Resolved |
| 3 | 2026-07-15 | `apt update` emitted repeated duplicate-target warnings for the 1Password repository | Equivalent legacy `.list` and maintained deb822 `.sources` entries were both active | Resolved |
| 4 | 2026-07-15 | Claude Desktop would not persist sign-in and Cowork could not use `/dev/kvm` on `debian-dev` | Claude first created the login keyring after session authentication; `REDACTED_USER_001` was also absent from `kvm` | Repair applied — login cycle required |

## 1. Recurring `pvestatd` Failure on `blue-server`

**First retained occurrence:** 2026-06-19  
**Investigated:** 2026-07-13  
**Owner:** Galaxy / Proxmox  
**Status:** Known issue; corrective work deferred by the operator

### Symptom and impact

The Proxmox cluster resource view reported `blue-server` with status `unknown`, while the host, its guests, and cluster communications remained online. Blue remained reachable over SSH, reported healthy CPU, memory, disk, and network metrics, and had more than two weeks of uptime. Corosync reported all four nodes present and the cluster quorate.

The loss of status was limited to the node and resource information normally published by `pvestatd`. It did not stop the hypervisor or its running workloads.

### Exact failure

`pvestatd.service` was failed with `Result=signal`, `ExecMainStatus=11`, and `signal=SEGV`. The most recent retained crash occurred at `2026-07-11 15:50:35 EDT` inside the Perl runtime. The unit declares `Restart=no`, so the daemon remained stopped after the crash and Proxmox continued to show the node as unknown.

The retained journal shows four failures since the Proxmox 9 installation:

| Date and time (EDT) | Result | Relevant observation |
|---|---|---|
| 2026-06-19 17:42:16 | `SIGSEGV` | Fault in Perl at executable offset `0x1a76f6` |
| 2026-06-24 03:52:39 | `SIGABRT` | Occurred just after the daily PVE package-list update; causation is not established |
| 2026-07-05 07:50:09 | Exit status `1` | Preceded by uninitialized `$upid` warnings in `PVE/RESTEnvironment.pm` |
| 2026-07-11 15:50:35 | `SIGSEGV` | Same Perl executable offset `0x1a76f6` as the June 19 crash |

The repeated fault offset maps to `Perl_newSVhek`, where Perl attempted to read an invalid internal pointer. This is consistent with memory corruption but does not by itself distinguish a software defect from firmware, CPU, or RAM instability.

### Tests and findings

- `pve-cluster`, `corosync`, `pvedaemon`, and `pveproxy` were running; only `pvestatd` was stopped among the checked Proxmox services.
- Grey, Purple, and Red ran the same relevant Proxmox and Perl versions and had no comparable retained `pvestatd` failures.
- Blue's relevant installed package files passed `dpkg -V`; the only reported modification was its expected APT source configuration file.
- No OOM kill, filesystem or NVMe error, machine-check event, or EDAC error was found in the retained logs.
- No retained core dump was available. The host has no `coredumpctl`, and no matching core file was found.
- Intel microcode was current at the time of inspection.
- Blue is a Lenovo ThinkCentre M910q with BIOS `M1AKT35A` dated 2018-03-21. Lenovo identifies `M1AKT36A` as a corrected minimum for this model family and publishes the newer `M1AKT5AA`; firmware age is therefore a material lead, not a confirmed cause.
- Similar recurring `pvestatd`/Perl crashes have been reported to Proxmox. Proxmox staff guidance for this failure pattern includes package verification, firmware and microcode review, and extended CPU/RAM testing. Package verification and the live log review did not expose a software-installation or disk fault on Blue.
- Repeating `ip6tables-restore` errors from `pve-firewall` were present near the latest crash. They continued independently and are not presently linked to the `pvestatd` segmentation fault.

### Current conclusion

The immediate cause of the unknown Proxmox status is confirmed: `pvestatd` crashed and its unit does not restart automatically. The deeper cause remains open. Blue-specific firmware or hardware instability is the leading hypothesis because the failures recur only on this node, include allocator-pointer corruption and an abort, and the BIOS predates Lenovo's corrected minimum. A node-specific Proxmox/Perl code path remains possible because only `pvestatd` has been observed crashing.

No service restart, firmware change, stress test, offline memory test, configuration change, or other corrective action was performed during this investigation.

### Deferred follow-up

The controlled follow-up is tracked in the [Galaxy TODO](TODO.md#blue-server-recurring-pvestatd-crashes). It should begin with evidence capture and non-disruptive integrity checks, then use an approved maintenance window for BIOS work and extended offline memory testing.

### Related records

- The first operational discovery and temporary restart were recorded in the [NetBird troubleshooting log](../../../../Platforms/Netbird/Documentation/Troubleshooting-Log.md#1-pvestatd-was-failed-on-blue-server).
- Lenovo BIOS notice: <https://support.lenovo.com/us/en/solutions/ht507019-new-recommended-version-of-system-bios-available-for-thinkcentre-all-m700-m710q-m800-m900s-m900t-all-m910-and-thinkstation-p320-tiny-systems>
- Lenovo M910q BIOS package: <https://pcsupport.lenovo.com/it/it/products/desktops-and-all-in-ones/thinkcentre-m-series-desktops/thinkcentre-m910q/downloads/ds120436>
- Proxmox discussion of the recurring crash pattern: <https://forum.proxmox.com/threads/pvestatd-segfaults.170897/>

## 2. GNOME Wired Network Indicator Showed a Question Mark on `debian-dev`

**Investigated:** 2026-07-15  
**Owner:** Galaxy VM 102 / `debian-dev`  
**Status:** Resolved

### Symptom and feedback loop

GNOME displayed a question mark for the wired connection while DNS, the default route, and internet access continued to work. The tight CLI reproduction was:

```sh
state=$(nmcli -t -f STATE general)
ethernet=$(nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status | grep ':ethernet:')
test "$state" = connected && echo "$ethernet" | grep -q ':connected:'
```

Before repair, `state=connected` but `ens18:ethernet:unmanaged:` caused the assertion to fail consistently.

### Root cause

The Debian server-style installation still declared `ens18` in `/etc/network/interfaces` and ran it through `networking.service` plus `dhcpcd`. NetworkManager was configured with the standard ifupdown plugin setting `managed=false`, so GNOME's network UI could not associate the working kernel interface with a managed wired connection.

The Debian connectivity-check package was briefly tested as a secondary hypothesis. Its official `network-test.debian.org` endpoint did not resolve from this network, so the package was removed; leaving it enabled would have risked a different limited-connectivity question mark. Connectivity status now comes from the managed connection and working global route without an external probe.

### Corrective action

- Created native NetworkManager profile `Wired connection 1` for `ens18` with autoconnect enabled.
- Preserved the established management address explicitly: `192.168.40.135/24`, gateway `192.168.40.1`, and DNS `192.168.40.1`.
- Removed only the `ens18` stanza from `/etc/network/interfaces`; loopback remains under ifupdown.
- Performed the network-ownership cutover through the Proxmox guest agent with an automatic rollback to `/etc/network/interfaces.pre-networkmanager-20260715` if address, gateway, DNS, or NetworkManager assertions failed.

Two initial attempts rolled back safely. The first exposed incorrect `ifdown` ordering. The second proved NetworkManager worked but received DHCP address `.136` because the old dhcpcd identity was inherited from the source template rather than the VM's current MAC. The final profile used the already-established `.135` address and passed immediately.

### Verification

- The GNOME-facing loop passed three consecutive times with `state=connected` and `ens18:ethernet:connected:Wired connection 1`.
- Restarting NetworkManager through the guest agent reactivated the profile automatically on attempt 2.
- Address `.135`, the `.1` default gateway, DNS resolution, and an HTTPS request to `deb.debian.org` all passed.
- SSH, GDM, and QEMU Guest Agent remained active; no failed systemd units were present.
- NetworkManager consumed 0.5% CPU in the final sample. A separate elevated desktop CPU sample was attributable to GNOME Shell, GNOME Software/PackageKit, and Chrome, not a network loop; the follow-up system sample was 97.6% idle and the final SSH Manager health result was `healthy`.

Full step evidence is retained in [S06 NetworkManager repair](../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S06-NetworkManager-Indicator-Repair-2026-07-15.md).

## 3. Duplicate 1Password APT Repository on `debian-dev`

**Investigated:** 2026-07-15  
**Owner:** Galaxy VM 102 / `debian-dev`  
**Status:** Resolved

### Symptom

`sudo apt update` succeeded but emitted duplicate `Packages`, translations, DEP-11, and icon target warnings referencing both:

- `/etc/apt/sources.list.d/1password.list`
- `/etc/apt/sources.list.d/1password.sources`

The regression command captured the complete APT output and failed when it matched `configured multiple times.*1password`.

### Root cause and correction

Both entries defined the same AMD64 repository, stable suite, main component, and signing key. The deb822 `.sources` file stated that the 1Password package automatically adds and configures it. The legacy `.list` file was newer, unmanaged, and redundant.

The legacy file was copied to root-only rollback path `/root/apt-source-backups/1password.list.pre-dedup-20260715` and removed from `sources.list.d`. The maintained `.sources` file and `/usr/share/keyrings/1password-archive-keyring.gpg` were left unchanged.

### Verification

- Two consecutive `apt-get update` executions returned `PASS_NO_DUPLICATE_1PASSWORD_SOURCE` with no warnings.
- The 1Password repository remained reachable.
- `apt-cache policy 1password` reported installed and candidate version `8.12.28` from the retained repository.
- `apt-get check` completed successfully.

Full evidence is retained in [S08 APT source deduplication](../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S08-1Password-APT-Source-Deduplication-2026-07-15.md).

## 4. Claude Desktop Keyring and KVM Access on `debian-dev`

**Investigated:** 2026-07-15  
**Owner:** Galaxy VM 102 / `debian-dev`  
**Status:** Repair applied; final verification awaits a fresh GNOME login

### Symptoms and feedback loop

Claude Desktop warned that sign-in would not be saved without an installed and unlocked system keyring. Cowork separately reported that `REDACTED_USER_001` lacked permission to use `/dev/kvm`.

The tight reproduction combined Claude's `safeStorage` log with the live Secret Service tree. Claude selected `gnome_libsecret` but logged `isEncryptionAvailable=false`; the D-Bus service answered normally while `/org/freedesktop/secrets/collection/login` was absent.

### Root cause

GNOME Keyring was already installed, enabled, running, and integrated into both GDM authentication/session PAM and password changes. The login journal proved PAM successfully handed the login password to the daemon. The decisive timing evidence was that `login.keyring` was created at 18:31:31, exactly when Claude first launched, 42 minutes after the authenticated GNOME session began. Chromium then logged that the login collection object did not exist, disabled libsecret to avoid deadlock, and requested a keyring restart or reboot before the next launch.

The virtualization problem was independent and direct: `/dev/kvm` was correctly `root:kvm` mode `0660`, but the `kvm` group had no members. The VM exposes `svm`, and the `kvm_amd` and `kvm` modules were already loaded.

### Corrective action

`REDACTED_USER_001` was added persistently to group `kvm`. No keyring package, PAM file, keyring database, or stored secret was replaced or deleted. A credential-free blank unlock probe did not export the new login collection, confirming that the safe next step is a normal authenticated GNOME session cycle rather than weakening or resetting the keyring.

### Verification state

The account database reports `kvm:x:993:REDACTED_USER_001`, and the KVM device, CPU feature, and kernel modules all passed. The currently running GNOME Shell retains its old supplementary group list, so both fixes require the operator to save work, sign out, sign back in using the normal account password, and relaunch Claude.

After that cycle, verification must show group 993 on the new GNOME process, an exported login Secret Service collection, no new Claude `isEncryptionAvailable=false` warning, and successful Cowork access to `/dev/kvm`.

Full evidence is retained in [S09 Claude keyring and KVM repair](../Evidence/Galaxy%20Debian%20Dev%20GNOME%20Installation%20-%202026-07-15/Logs/S09-Claude-Keyring-And-KVM-Repair-2026-07-15.md).
