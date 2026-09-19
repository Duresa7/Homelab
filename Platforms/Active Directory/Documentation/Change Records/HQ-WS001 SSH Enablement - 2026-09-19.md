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
| Windows Firewall | `OpenSSH-Server-In-TCP`, profile `Private` to `Domain, Private`, remote address scoped to `192.168.50.0/24` |

I made the change through the QEMU guest agent on VM 310 on grey-server, the same path the [RDP enablement](Domain%20Machine%20RDP%20Enablement%20-%202026-09-12.md) used, because `HQ-WS001` had no SSH session configured. That was the circularity this change removes.

## Gateway path

`Allow Secure to HQ-WS001 SSH`: IPv4 TCP, source the Secure network (VLAN 50) in Internal, destination `192.168.65.20:22` in `AlphaSec-Identity`, with logging and a response companion enabled and the Always schedule. The controller assigned index 10007 and the user-defined total rose from 87 to 88.

I admitted the whole network rather than `Jedi PC` at `192.168.50.241` alone. That matches the decision recorded for RDP on 2026-09-12, where I admitted Secure as a network for the same machine, and keeps the two remote-access paths to this host described the same way.

## The rule was enabled and still blocking

My first pass read the Windows Firewall rule as `Enabled=True` and moved on. That was not enough, and the first connection attempt failed because of it. The rule was scoped to the **Private** profile, while the adapter's profile is `DomainAuthenticated` on `ad.alphasecunited.com`. An enabled rule on a profile that is not active does nothing, so Windows dropped inbound 22 before the gateway path was ever exercised.

I set the rule to `Domain, Private` and, while I was there, scoped its remote address to `192.168.50.0/24`. That gives the host its own source restriction rather than relying on the gateway alone, which is the same two-layer arrangement the [RDP enablement](Domain%20Machine%20RDP%20Enablement%20-%202026-09-12.md) used on all five machines.

The lesson worth carrying: on a Windows host, `Enabled` is not the whole answer for a firewall rule. Read the profile and compare it with `Get-NetConnectionProfile`, because the capability installer picks a profile at install time and a domain join changes which one is active.

## Verification

| Check | Result |
|---|---|
| Service after the change | `Running`, start type `Automatic` |
| Listener | Two sockets on TCP 22, `0.0.0.0` and `::` |
| Loopback connect on the host | `True`, so the daemon itself accepts connections |
| Windows Firewall rule after the correction | `Enabled=True`, profile `Domain, Private`, port 22, remote `192.168.50.0/24` |
| Default shell | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` |
| Control, `ubuntu-dev` on Personal-A to `192.168.65.20:22` | Refused, so the new rule admits Secure and did not open the host to the automation hosts |
| Sanity, `ubuntu-dev` to `HQ-DC01:22` | Open, so the existing automation path is untouched |
| Gateway rule hit counter | `0` at first failure, against `8` on a sibling policy created minutes earlier, so the counter works and this rule had never matched |
| Client inventory | `Jedi PC` is on `192.168.50.241` and is the only client on VLAN 50; the MacBook Air is on `192.168.10.27` in Trusted |
| From the source network | **Not proved.** No host I can drive lives on VLAN 50, so the first connection from `Jedi PC` is the proof |

## Open

- **Untested from Secure.** Everything above is verified from the host side and from a negative control. The positive test is one `ssh` from `Jedi PC`, and until it happens this rule is unproven. Only `Jedi PC` sits on that network, so SSH from the MacBook Air or any other Trusted machine needs Trusted added to both the gateway rule and the host rule; RDP to this host already admits Trusted, so that would follow an existing decision rather than make a new one.
- **Not in SSH Manager.** The gateway runs on Personal-A, which this rule deliberately does not admit, so `HQ-WS001` is still absent from the server list and agent work on it continues through the guest agent. Enrolling it would need a second rule from the automation hosts, which I have not written because nothing needs it yet.
- **Password authentication.** A domain credential over SSH is what this enables today. A key in `administrators_authorized_keys` would be better and costs one file; I left it out rather than handle a key I was not asked to place.
