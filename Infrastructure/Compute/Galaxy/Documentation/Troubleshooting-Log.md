# Galaxy Troubleshooting Log

**Created:** 2026-07-14  
**Last updated:** 2026-07-22

This is my chronological troubleshooting record for the Galaxy Proxmox cluster. Open follow-up work is tracked in the [Galaxy TODO](TODO.md).

## Quick Index

| # | Date investigated | Symptom | Current finding | Status |
|---:|---|---|---|---|
| 1 | 2026-07-13 | Proxmox reported `blue-server` as `unknown` while its guests remained online | `pvestatd` repeatedly crashes and does not restart; the deeper cause is not yet proven | Known issue; deferred |
| 2 | 2026-07-15 | GNOME showed a question mark for wired networking on `debian-dev` although internet access worked | `ens18` was owned by legacy ifupdown/dhcpcd and therefore appeared unmanaged to NetworkManager | Resolved |
| 3 | 2026-07-15 | `apt update` emitted repeated duplicate-target warnings for the 1Password repository | Equivalent legacy `.list` and maintained deb822 `.sources` entries were both active | Resolved |
| 4 | 2026-07-15 | Claude Desktop would not persist sign-in and Cowork could not use `/dev/kvm` on `debian-dev` | Claude first created the login keyring after session authentication; `<YOUR_ADMIN_USERNAME>` was also absent from `kvm` | Repair applied; login cycle required |
| 5 | 2026-07-20 | CT 107 `docker-network` & CT 108 `docker-blue` down and stuck in HA `error` on purple-server; couldn't migrate back to blue | HA relocated the configs off blue on a shutdown, but the guests' `local-lvm` disks stayed on blue, so no node could start them | Resolved |
| 6 | 2026-07-22 | HA reported `grey-server` with `old timestamp - dead?`, `watchdog standby`, & a 2025-08-22 LRM timestamp | Grey's `pve-ha-lrm` & `pve-ha-crm` units were disabled and hadn't started during the current boot | Resolved |

## 1. Recurring `pvestatd` Failure on `blue-server`

**First retained occurrence:** 2026-06-19  
**Investigated:** 2026-07-13  
**Owner:** Galaxy / Proxmox  
**Status:** Known issue; I deferred the corrective work

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

- `pve-cluster`, `corosync`, `pvedaemon`, and `pveproxy` were running; only `pvestatd` was stopped among the Proxmox services I checked.
- Grey, Purple, and Red ran the same relevant Proxmox and Perl versions and had no comparable retained `pvestatd` failures.
- Blue's relevant installed package files passed `dpkg -V`; the only reported modification was its expected APT source configuration file.
- I found no OOM kill, filesystem or NVMe error, machine-check event, or EDAC error in the retained logs.
- No retained core dump was available. The host has no `coredumpctl`, and no matching core file was found.
- Intel microcode was current at the time of inspection.
- Blue is a Lenovo ThinkCentre M910q with BIOS `M1AKT35A` dated 2018-03-21. Lenovo identifies `M1AKT36A` as a corrected minimum for this model family and publishes the newer `M1AKT5AA`; firmware age is therefore a material lead, not a confirmed cause.
- Similar recurring `pvestatd`/Perl crashes have been reported to Proxmox. Proxmox staff guidance for this failure pattern includes package verification, firmware and microcode review, and extended CPU/RAM testing. Package verification and the live log review did not expose a software-installation or disk fault on Blue.
- Repeating `ip6tables-restore` errors from `pve-firewall` were present near the latest crash. They continued independently and are not presently linked to the `pvestatd` segmentation fault.

### Confirmed failure and open cause

The immediate cause of the unknown Proxmox status is confirmed: `pvestatd` crashed and its unit does not restart automatically. The deeper cause remains open. Blue-specific firmware or hardware instability is my leading hypothesis because the failures recur only on this node, include allocator-pointer corruption and an abort, and the BIOS predates Lenovo's corrected minimum. A node-specific Proxmox/Perl code path remains possible because only `pvestatd` has been observed crashing.

I performed no service restart, firmware change, stress test, offline memory test, or configuration change during this investigation.

### Deferred follow-up

The controlled follow-up is tracked in the [Galaxy TODO](TODO.md#blue-server-recurring-pvestatd-crashes). It should begin with evidence capture and non-disruptive integrity checks, then use an approved maintenance window for BIOS work and extended offline memory testing.

### Related records

- I recorded the first operational discovery and temporary restart in the [NetBird troubleshooting log](../../../../Platforms/Netbird/Documentation/Troubleshooting-Log.md#1-pvestatd-was-failed-on-blue-server).
- Lenovo BIOS notice: <https://support.lenovo.com/us/en/solutions/ht507019-new-recommended-version-of-system-bios-available-for-thinkcentre-all-m700-m710q-m800-m900s-m900t-all-m910-and-thinkstation-p320-tiny-systems>
- Lenovo M910q BIOS package: <https://pcsupport.lenovo.com/it/it/products/desktops-and-all-in-ones/thinkcentre-m-series-desktops/thinkcentre-m910q/downloads/ds120436>
- Proxmox discussion of the recurring crash pattern: <https://forum.proxmox.com/threads/pvestatd-segfaults.170897/>

## 2. GNOME Wired Network Indicator Showed a Question Mark on `debian-dev`

**Investigated:** 2026-07-15  
**Owner:** Galaxy VM 102 / `debian-dev`  
**Status:** Resolved

### Reproduction

GNOME displayed a question mark for the wired connection while DNS, the default route, and internet access continued to work. My tight CLI reproduction was:

```sh
state=$(nmcli -t -f STATE general)
ethernet=$(nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status | grep ':ethernet:')
test "$state" = connected && echo "$ethernet" | grep -q ':connected:'
```

Before repair, `state=connected` but `ens18:ethernet:unmanaged:` caused the assertion to fail consistently.

### Root cause

The Debian server-style installation still declared `ens18` in `/etc/network/interfaces` and ran it through `networking.service` plus `dhcpcd`. NetworkManager was configured with the standard ifupdown plugin setting `managed=false`, so GNOME's network UI could not associate the working kernel interface with a managed wired connection.

I briefly tested the Debian connectivity-check package as a secondary hypothesis. Its official `network-test.debian.org` endpoint did not resolve from my network, so I removed the package; leaving it enabled would have risked a different limited-connectivity question mark. Connectivity status now comes from the managed connection and working global route without an external probe.

### Corrective action

- I created native NetworkManager profile `Wired connection 1` for `ens18` with autoconnect enabled.
- I preserved the established management address explicitly: `192.168.40.135/24`, gateway `192.168.40.1`, and DNS `192.168.40.1`.
- I removed only the `ens18` stanza from `/etc/network/interfaces`; loopback remains under ifupdown.
- I performed the network-ownership cutover through the Proxmox guest agent with an automatic rollback to `/etc/network/interfaces.pre-networkmanager-20260715` if address, gateway, DNS, or NetworkManager assertions failed.

My first two attempts rolled back safely. The first exposed incorrect `ifdown` ordering. The second proved NetworkManager worked but received DHCP address `.136` because the old dhcpcd identity was inherited from the source template rather than the VM's current MAC. The final profile used the already-established `.135` address and passed immediately.

### Verification

- The GNOME-facing loop passed three consecutive times with `state=connected` and `ens18:ethernet:connected:Wired connection 1`.
- Restarting NetworkManager through the guest agent reactivated the profile automatically on attempt 2.
- Address `.135`, the `.1` default gateway, DNS resolution, and an HTTPS request to `deb.debian.org` all passed.
- SSH, GDM, and QEMU Guest Agent remained active; no failed systemd units were present.
- NetworkManager consumed 0.5% CPU in the final sample. A separate elevated desktop CPU sample was attributable to GNOME Shell, GNOME Software/PackageKit, and Chrome, not a network loop; the follow-up system sample was 97.6% idle and the final SSH Manager health result was `healthy`.

## 3. Duplicate 1Password APT Repository on `debian-dev`

**Investigated:** 2026-07-15  
**Owner:** Galaxy VM 102 / `debian-dev`  
**Status:** Resolved

### Symptom

`sudo apt update` succeeded but emitted duplicate `Packages`, translations, DEP-11, and icon target warnings referencing both:

- `/etc/apt/sources.list.d/1password.list`
- `/etc/apt/sources.list.d/1password.sources`

My regression command captured the complete APT output and failed when it matched `configured multiple times.*1password`.

### Root cause and correction

Both entries defined the same AMD64 repository, stable suite, main component, and signing key. The deb822 `.sources` file stated that the 1Password package automatically adds and configures it. The legacy `.list` file was newer, unmanaged, and redundant.

I copied the legacy file to root-only rollback path `/root/apt-source-backups/1password.list.pre-dedup-20260715` and removed it from `sources.list.d`. I left the maintained `.sources` file and `/usr/share/keyrings/1password-archive-keyring.gpg` unchanged.

### Verification

- Two consecutive `apt-get update` executions returned `PASS_NO_DUPLICATE_1PASSWORD_SOURCE` with no warnings.
- The 1Password repository remained reachable.
- `apt-cache policy 1password` reported installed and candidate version `8.12.28` from the retained repository.
- `apt-get check` completed successfully.

## 4. Claude Desktop Keyring and KVM Access on `debian-dev`

**Investigated:** 2026-07-15  
**Owner:** Galaxy VM 102 / `debian-dev`  
**Status:** Repair applied; final verification awaits a fresh GNOME login

### Reproduction

Claude Desktop warned that sign-in would not be saved without an installed and unlocked system keyring. Cowork separately reported that `<YOUR_ADMIN_USERNAME>` lacked permission to use `/dev/kvm`.

My tight reproduction combined Claude's `safeStorage` log with the live Secret Service tree. Claude selected `gnome_libsecret` but logged `isEncryptionAvailable=false`; the D-Bus service answered normally while `/org/freedesktop/secrets/collection/login` was absent.

### Root cause

GNOME Keyring was already installed, enabled, running, and integrated into both GDM authentication/session PAM and password changes. The login journal proved PAM successfully handed the login password to the daemon. The decisive timing evidence was that `login.keyring` was created at 18:31:31, exactly when Claude first launched, 42 minutes after the authenticated GNOME session began. Chromium then logged that the login collection object did not exist, disabled libsecret to avoid deadlock, and requested a keyring restart or reboot before the next launch.

The virtualization problem was independent and direct: `/dev/kvm` was correctly `root:kvm` mode `0660`, but the `kvm` group had no members. The VM exposes `svm`, and the `kvm_amd` and `kvm` modules were already loaded.

### Corrective action

I added `<YOUR_ADMIN_USERNAME>` to group `kvm`. I didn't change the keyring packages, PAM files, or keyring database. A blank unlock probe didn't export the new login collection, so the remaining test requires a normal GNOME sign-out and sign-in.

### Verification state

The account database reports `kvm:x:993:<YOUR_ADMIN_USERNAME>`, and the KVM device, CPU feature, and kernel modules all passed. The currently running GNOME Shell retains its old supplementary group list, so to activate both fixes I need to save my work, sign out, sign back in with the normal account password, and relaunch Claude.

After that cycle, verification must show group 993 on the new GNOME process, an exported login Secret Service collection, no new Claude `isEncryptionAvailable=false` warning, and successful Cowork access to `/dev/kvm`.

## 5. HA Local-Storage Stranding of CT 107 and CT 108 After a Blue-Server Shutdown

**Investigated:** 2026-07-20  
**Owner:** Galaxy / Proxmox HA  
**Status:** Resolved

### Symptom and impact

CT 107 `docker-network` & CT 108 `docker-blue` were both down and both sat in the HA `error` state on purple-server. `ha-manager migrate ct:107 blue-server` returned exit code 255, so I couldn't move either one back to blue where it started. NetBird, Nginx Proxy Manager (CT 107), & the RustDesk relay `hbbs`/`hbbr` (CT 108) were offline from 16:30 to 17:04 EDT, about 34 minutes.

### What I found

The two config files had moved to `/etc/pve/nodes/purple-server/lxc/`, but purple had no disks for them: `pct list` showed both `stopped`, and `lvs` on purple carried only `data`, `root`, & `swap`. blue still held the real disks, `pve/vm-107-disk-0` (32 GiB) & `pve/vm-108-disk-0` (15 GiB), inactive because the configs weren't on blue. The purple task log spelled it out: `vzstart` failing with `no such logical volume pve/vm-107-disk-0`, `vzmigrate ... migration aborted`, and `ha-manager migrate ct:107 blue-server' failed: exit code 255`.

### Root cause

Both containers are HA-managed and put their rootfs on `local-lvm`, node-local LVM-thin with no shared copy on any other node. The trigger was planned maintenance: I was moving blue, purple, red, & grey onto a UPS and shut blue down. `datacenter.cfg` sets no HA `shutdown_policy`, so it defaults to `conditional`, which relocates HA services on a node shutdown rather than freezing them, and blue's LRM logged `got shutdown request with shutdown policy 'conditional'` at 16:30:14. `last` confirms `shutdown system down Mon Jul 20 16:30 - 16:36`, a power-down, not a reboot. The shutdown made the CRM relocate 107 & 108 off blue; the configs went to purple, the node-local disks couldn't follow, and every start looped into `error`. A migrate command against a service already in `error` is refused (`service 'ct:107' in error state, must be disabled and fixed first`), which is why the exit 255 attempts never had a chance.

### Corrective action

The data was safe on blue, so this was a config-and-disk reunion, not a restore. I removed both from HA (`ha-manager remove ct:107` & `ct:108`) to clear the error state, moved each config from `purple-server/lxc/` back to `blue-server/lxc/`, and started them with `pct start`. The disks reactivated (`Vwi-aotz--`) and both workloads came up: `netbird-server`, `netbird-dashboard`, & a healthy `nginx-proxy-manager` on 107; `hbbs` & `hbbr` on 108. I then re-added both to HA and applied a strict node-affinity rule, `pin-blue-local-storage`, limiting `ct:107,ct:108` to `blue-server` so the HA manager can't relocate them to a diskless node again.

### Verification

- `ha-manager status` reports `service ct:107 (blue-server, started)` & `service ct:108 (blue-server, started)`.
- `ha-manager rules list` shows `pin-blue-local-storage`; `pct list` on blue shows both `running`.
- SSH reached 192.168.85.2 with NetBird & NPM healthy; CT 108 held 192.168.40.39/24 with its gateway reachable and both relay containers up.
- purple's `lxc` directory is empty of 107/108, and red carried no stale `vm-107`/`vm-108` volumes.

### Related records

- Full write-up, screenshots, & log transcripts in the [Galaxy HA Local-Storage Stranding Incident report](../../../../Security/Incidents/Galaxy-HA-Local-Storage-Stranding-2026-07-20/Galaxy-HA-Local-Storage-Stranding-Incident-2026-07-20.md).
- The [Docker-Network LXC deployment record](Change%20Records/Galaxy%20Docker-Network%20LXC%20Deployment%20-%202026-07-10.md) documented the no-failover caveat this incident exercised.
- blue's back-to-back reboot & shutdown may relate to the [recurring pvestatd failure on blue-server](#1-recurring-pvestatd-failure-on-blue-server).

## 6. Disabled HA Daemons on `grey-server`

**Investigated:** 2026-07-22  
**Owner:** Galaxy / Proxmox HA  
**Status:** Resolved

### Symptom and impact

Proxmox HA reported `lrm grey-server (old timestamp - dead?, watchdog standby, Fri Aug 22 23:47:05 2025)`. All four nodes returned the same status, so the date came from cluster state rather than a browser cache. Grey remained online in Corosync & continued to cast one vote, but its Local Resource Manager wasn't publishing heartbeats or available to manage an HA resource placed on the node.

No guest went down. The only HA resources were CT 107 `docker-network` & CT 108 `docker-blue`; both remained started on `blue-server` under the `pin-blue-local-storage` node-affinity rule.

### Tests and root cause

Grey's clock read `2026-07-22T02:11:25-04:00`, ruling out a current clock error. `systemctl show` identified the fault: `pve-ha-lrm.service` & `pve-ha-crm.service` were `inactive`, `dead`, & `disabled`, although each installed unit carried `preset: enabled`. Both reported `Result=success` with no current-boot start timestamp, so neither daemon had crashed.

`/etc/pve/nodes/grey-server/lrm_status` was valid JSON with mode `restart`, state `wait_for_agent_lock`, & modification time `2025-08-22 23:47:05 -0400`. The installed `PVE::HA::LRM` code uses mode `restart` for a daemon restart and for a conditional-policy node reboot, so that field doesn't distinguish the two paths. The retained journal begins on 2026-02-16 & contains no Grey HA daemon entries before this repair; the repository & retained root history contain no matching disable record. I can prove the disabled units caused the stale heartbeat, but the command, caller, & date of the disable are no longer retained.

The stale timestamp file was readable, and the other three nodes updated their LRM files normally. That ruled out pmxcfs corruption. `watchdog-mux` was inactive because neither Grey HA daemon had requested it; `watchdog standby` was a result of the stopped LRM, not a watchdog failure.

### Corrective action

I ran `systemctl enable --now pve-ha-lrm pve-ha-crm` on `grey-server`. Systemd created both `multi-user.target.wants` links & started the CRM at 02:22:12 EDT and the LRM at 02:22:13 EDT. I didn't edit `/etc/pve/ha/resources.cfg`, change `pin-blue-local-storage`, move a guest, or delete the stale LRM status file.

### Verification

- Both Grey units report `enabled`, `active`, & `running`; `watchdog-mux` is active.
- Grey rewrote `lrm_status` at 02:22:28 EDT. `ha-manager status` changed its entry to `lrm grey-server (idle, watchdog standby, Wed Jul 22 02:22:28 2026)`.
- A second check at 02:23:16 EDT showed another current Grey heartbeat at 02:23:13. Purple independently returned the same Grey state.
- The Galaxy cluster remained quorate with four votes during the repair. Purple remained CRM master & fencing remained armed.
- CT 107 & CT 108 remained `started` in HA and `running` under `pct status` on Blue.
- Grey logged no warning, error, critical, alert, or emergency entries for either HA daemon after startup.

### Related records

- [Grey Server HA Daemon Restoration change record](Change%20Records/Galaxy%20Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22.md)
- [Pre-change transcript](../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S01-grey-ha-prechange-2026-07-22.txt)
- [Service restoration transcript](../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S02-grey-ha-enable-services-2026-07-22.txt)
- [After-change verification transcript](../Evidence/Grey%20Server%20HA%20Daemon%20Restoration%20-%202026-07-22/Logs/S03-grey-ha-verification-2026-07-22.txt)
