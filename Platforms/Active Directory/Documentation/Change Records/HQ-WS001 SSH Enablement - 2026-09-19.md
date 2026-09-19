# HQ-WS001 SSH Enablement - 2026-09-19

**Created:** 2026-09-19  
**Last updated:** 2026-09-19  
**Implementation and verification:** 2026-09-19

I enabled SSH on `HQ-WS001` and opened one path to it from Secure VLAN 50, so I can work on that test workstation from a terminal instead of an RDP session. This covers host configuration and the gateway path. I installed no key, changed no Group Policy, and did not enrol the host in SSH Manager.

## Pre-change state

The work was smaller than I expected, because the [unattended build](HQ-WS001%20Workstation%20Join%20-%202026-09-10.md) already carries OpenSSH. The capability read `Installed`, the Windows firewall rule `OpenSSH-Server-In-TCP` was enabled, and the only thing missing was the service: `sshd` was `Stopped` with start type `Manual`, and nothing was listening on TCP 22.

The gateway was the real obstacle. The identity plane accepts SSH from almost nothing: the single rule is `Allow Automation to Identity SSH`, which admits `AG-Automation-Hosts` (`ubuntu-dev` and `docker-blue`) to `AG-Identity-Servers`, and that group holds `192.168.65.10`, `.11` and `.12` only. The workstation at `.20` was outside it.

**I did not add `.20` to `AG-Identity-Servers`,** which would have been the quickest edit. `Allow PAW to Windows Admin` also targets that group, on the `PG-Windows-Admin` port group, so putting the workstation in it would have silently widened a second policy onto a machine that policy was never scoped for. A dedicated rule keeps the change to the one path I intended.

## Host configuration

| Setting | Value |
|---|---|
| OpenSSH | `OpenSSH_for_Windows_9.5p2`, LibreSSL 3.8.2, already present as a Windows capability |
| Service | `sshd`, start type `Manual` to `Automatic`, started |
| Default shell | PowerShell, matching the other Windows hosts so that remote commands separate with `;` rather than `&&` |
| Authentication | `sshd_config` carries no `PasswordAuthentication` or `PubkeyAuthentication` directive, so both sit at their shipped defaults and a domain credential works without further change |
| Administrator keys | The stock `Match Group administrators` block points at `__PROGRAMDATA__/ssh/administrators_authorized_keys`. A key for an administrative account belongs there, not in the profile's `.ssh` |

I made the change through the QEMU guest agent on VM 310 on grey-server, the same path the [RDP enablement](Domain%20Machine%20RDP%20Enablement%20-%202026-09-12.md) used, because `HQ-WS001` had no SSH session configured. That was the circularity this change removes.

## Gateway path

`Allow Secure to HQ-WS001 SSH`: IPv4 TCP, source the Secure network (VLAN 50) in Internal, destination `192.168.65.20:22` in `AlphaSec-Identity`, with logging and a response companion enabled and the Always schedule. The controller assigned index 10007 and the user-defined total rose from 87 to 88.

I admitted the whole network rather than `Jedi PC` at `192.168.50.241` alone. That matches the decision recorded for RDP on 2026-09-12, where I admitted Secure as a network for the same machine, and keeps the two remote-access paths to this host described the same way.

## Verification

| Check | Result |
|---|---|
| Service after the change | `Running`, start type `Automatic` |
| Listener | Two sockets on TCP 22 |
| Default shell | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` |
| Control, `ubuntu-dev` on Personal-A to `192.168.65.20:22` | Refused, so the new rule admits Secure and did not open the host to the automation hosts |
| Sanity, `ubuntu-dev` to `HQ-DC01:22` | Open, so the existing automation path is untouched |
| From the source network | **Not proved.** No host I can drive lives on VLAN 50, so the first connection from `Jedi PC` is the proof |

## Open

- **Untested from Secure.** Everything above is verified from the host side and from a negative control. The positive test is one `ssh` from `Jedi PC`, and until it happens this rule is unproven.
- **Not in SSH Manager.** The gateway runs on Personal-A, which this rule deliberately does not admit, so `HQ-WS001` is still absent from the server list and agent work on it continues through the guest agent. Enrolling it would need a second rule from the automation hosts, which I have not written because nothing needs it yet.
- **Password authentication.** A domain credential over SSH is what this enables today. A key in `administrators_authorized_keys` would be better and costs one file; I left it out rather than handle a key I was not asked to place.
