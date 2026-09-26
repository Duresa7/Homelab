# win11-dev Completion

**Created:** 2026-09-21  
**Last updated:** 2026-09-25

I completed VM 103 `win11-dev` on `green-server` as a standalone Windows 11 Pro workstation with Windows and SSH only. I resumed the [failed 2026-09-20 build](win11-dev%20Provisioning%20and%20Green%20Memory%20Failure%20-%202026-09-20.md) by choice despite Green's unresolved host memory errors. The guest is running, boots from its system disk, and has automatic startup enabled.

## Installed state

| Setting | Verified value |
| --- | --- |
| OS | Windows 11 Pro 25H2, build 26200.6584 |
| VM / host | 103 `win11-dev`, `green-server` (`192.168.70.14`) |
| CPU / memory | 4 host-model vCPUs; 8 GiB fixed allocation, 7.93 GiB visible to Windows |
| System disk | 120 GiB on NVMe-backed `local-lvm`; VirtIO SCSI, discard, SSD flag and I/O thread |
| Firmware | OVMF; Secure Boot verified enabled; TPM 2.0 present and ready |
| Network | VirtIO, `vmbr0`, Personal-A VLAN 40; DHCP reservation `192.168.40.117/24` |
| Membership | `WORKGROUP`; `PartOfDomain=false` |
| Local login | `dkadi`, enabled with a required password stored securely |
| SSH | TCP 22; SSH Manager entry `win11_dev`; key authentication; PowerShell default shell |
| Startup | `sshd` and `QEMU-GA` automatic; VM `onboot=1` |
| Activation | Not activated; Windows reports Notification mode |

I installed the VirtIO storage, network, serial, balloon and firmware-configuration drivers. The final device query returned zero devices with a nonzero configuration error. The guest agent responds, and the Windows desktop reached local first login. I disabled setup autologon and verified that Winlogon retained no `DefaultPassword`.

## SSH and addressing

OpenSSH Server installed through the Windows optional capability. I placed the SSH Manager public key in `C:\ProgramData\ssh\administrators_authorized_keys` with only SYSTEM and Administrators access. The effective server configuration permits `dkadi`, enables public-key authentication and disables password authentication.

The first host-key scan timed out. Windows classified this connection as Public, while the installed `OpenSSH-Server-In-TCP` rule applied only to Private. I enabled that rule on all profiles; the same scan then succeeded. I compared RSA, ECDSA and ED25519 fingerprints with those read through the QEMU guest agent before enrolling them in SSH Manager's persistent known-hosts file. No UniFi firewall policy changed.

I reserved the guest's existing address in UniFi. The final controller readback returned `use_fixedip=true`, `fixed_ip=192.168.40.117`, Personal-A, VLAN 40 and online status.

I added `win11_dev` to SSH Manager. The older `ssh-manager-servers.env` reference was no longer loaded by the live service, so changing it alone had no effect. I added the seven non-secret server settings to the active resolved Compose definition at `/opt/docker/mcp-gateway/docker-compose.yml`, then recreated only `ssh-manager` with pulls and builds disabled. I applied the same settings to Dockhand's imported definition at `/opt/docker/dockhand/stacks/imported/docker_blue/docker-mcp-gateway/compose.yaml` so a later UI deployment retains the entry. The live catalog now returns 24 configured hosts. The SSH Manager container is healthy.

## Verification and cleanup

At 3:25 AM Eastern I connected through Executor and SSH Manager after a Windows restart. `hostname` returned `win11-dev`, `whoami` returned `win11-dev\dkadi`, and the query again returned Windows 11 Pro, `WORKGROUP`, no domain membership, both services running with automatic startup, the reserved IPv4 address, zero device errors, autologon disabled and no saved autologon password. The effective SSH settings remained `pubkeyauthentication yes`, `passwordauthentication no` and `allowusers dkadi`.

I detached all three installation discs and removed the answer ISO, password and answer-file staging copies, remote build directory and SSH Manager transfer files. I removed cached answer-file paths from Windows. The verified general Windows and VirtIO installation ISOs remain available on Green. No snapshot or backup was created.

At 3:25:56 AM Eastern Green reported VM 103 running with `onboot=1`, system-disk-only boot order and no installation discs. Its thin pool used 34,193,238 KiB (23.09%), leaving 113,893,545 KiB available. Galaxy remained quorate with five votes.

I retained [Windows verification after restart](../../Evidence/win11-dev%20Completion%20-%202026-09-21/Exports/Windows-After-Restart.json), [host and cleanup verification](../../Evidence/win11-dev%20Completion%20-%202026-09-21/Exports/Host-And-Cleanup.json), and the filtered [DHCP readback](../../Evidence/win11-dev%20Completion%20-%202026-09-21/Exports/DHCP-Reservation-Readback.json). Earlier installation, driver, SSH configuration and Compose changes have no separately retained terminal capture.

## Local password update

At 2:17 PM Eastern on 2026-09-21 I changed the local `dkadi` password to match the saved App Portal credential. Windows `LogonUser` with interactive logon type returned success for `WIN11-DEV\dkadi` using the new password. I updated the saved workstation credential and verified its readback matched the password used for that successful login. The source App Portal credential was unchanged.

I removed the restricted password staging file from Windows and the local and SSH Manager transfer copies. A subsequent SSH Manager command confirmed `StagingAbsent=true` and `SshRunning=true`. SSH remains key authenticated. No secret value was displayed or retained in this record. These checks have no separately retained terminal capture.

## Open

Windows activation needs a valid license. Green's [memory fault](../Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md) remains unresolved; successful installation and restart do not validate the host hardware. Development tools remain for later, as intended.
